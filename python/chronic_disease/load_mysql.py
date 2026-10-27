# -*- coding: utf-8 -*-
"""建库建表 + 将生成的 CSV 批量装入 MySQL。

用法（在项目根目录）：
  python -m python.chronic_disease.load_mysql --init --truncate
  python -m python.chronic_disease.load_mysql --init --truncate --patients 100000

实现优先使用 MySQL LOAD DATA LOCAL INFILE（快、可重复），
若服务端禁用 local_infile，则自动退化为分批 executemany。
"""
from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

import pymysql
from pymysql.constants import CLIENT

from .config import DB_CONFIG, GENERATED_DIR, PROJECT_ROOT, TABLES, ensure_dirs
from .db import connect

LOAD_ORDER = [
    "patient_info", "disease_record", "health_checkup", "lifestyle",
    "visit_record", "medication_record", "follow_up",
]
COLUMNS = {
    "patient_info": "patient_id,gender,age,province,city,id_number,phone,create_time",
    "disease_record": "patient_id,disease_type,disease_name,diagnose_date,severity,doctor_id,hospital",
    "health_checkup": "patient_id,checkup_date,sbp,dbp,fasting_glucose,hba1c,tc,tg,hdl,ldl,bmi,heart_rate,creatinine,uric_acid",
    "lifestyle": "patient_id,smoking_status,smoking_amount,drinking_status,exercise_freq,sleep_hours,diet_pattern",
    "visit_record": "patient_id,visit_date,visit_type,hospital,department,diagnosis,cost,insurance_pay,self_pay,stay_days",
    "medication_record": "patient_id,drug_name,drug_type,dosage,start_date,end_date,cost,is_effective",
    "follow_up": "patient_id,follow_date,follow_type,symptom_status,medication_adherence,doctor_advice,next_follow_date",
}


def run_sql_file(path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    cfg = {k: v for k, v in DB_CONFIG.items() if k != "autocommit"}
    cfg["database"] = None
    conn = pymysql.connect(
        **cfg,
        client_flag=CLIENT.MULTI_STATEMENTS,
        autocommit=True,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            while cur.nextset():
                pass
    finally:
        conn.close()


def truncate_tables() -> None:
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SET FOREIGN_KEY_CHECKS=0")
            for t in LOAD_ORDER:
                # 表可能尚未创建，忽略错误
                try:
                    cur.execute(f"TRUNCATE TABLE {t}")
                except Exception as exc:
                    print(f"  [WARN] truncate {t}: {exc}")
            cur.execute("SET FOREIGN_KEY_CHECKS=1")
        conn.commit()
    finally:
        conn.close()


def load_with_infile(table: str, csv_path: Path) -> int:
    conn = connect(local_infile=True)
    try:
        with conn.cursor() as cur:
            cur.execute("SET FOREIGN_KEY_CHECKS=0")
            stmt = f"""
                LOAD DATA LOCAL INFILE %s
                INTO TABLE {table}
                CHARACTER SET utf8mb4
                FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY '"'
                LINES TERMINATED BY '\n'
                IGNORE 1 LINES
                ({COLUMNS[table]})
            """
            cur.execute(stmt, (str(csv_path).replace("\\", "/"),))
            affected = cur.rowcount
            cur.execute("SET FOREIGN_KEY_CHECKS=1")
        conn.commit()
        return int(affected)
    finally:
        conn.close()


def load_with_batches(table: str, csv_path: Path, batch_size: int = 5000) -> int:
    conn = connect()
    try:
        with conn.cursor() as cur, csv_path.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            cols = reader.fieldnames or []
            placeholders = ",".join(["%s"] * len(cols))
            stmt = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
            batch = []
            total = 0
            for row in reader:
                batch.append(tuple(row[c] if row[c] != "\\N" else None for c in cols))
                if len(batch) >= batch_size:
                    cur.executemany(stmt, batch)
                    total += len(batch)
                    batch.clear()
            if batch:
                cur.executemany(stmt, batch)
                total += len(batch)
        conn.commit()
        return total
    finally:
        conn.close()


def verify_counts(manifest: dict | None = None) -> dict:
    conn = connect()
    try:
        with conn.cursor() as cur:
            actual = {}
            for t in LOAD_ORDER:
                cur.execute(f"SELECT COUNT(*) FROM {t}")
                actual[t] = cur.fetchone()[0]
    finally:
        conn.close()
    if manifest:
        for t in LOAD_ORDER:
            expected = manifest.get("tables", {}).get(t, {}).get("rows")
            if expected is not None and actual[t] != expected:
                raise RuntimeError(f"记录数不一致 {t}: expected={expected}, actual={actual[t]}")
    return actual


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true", help="执行建库建表 SQL")
    parser.add_argument("--truncate", action="store_true", help="导入前清空 7 张业务表")
    parser.add_argument("--data-dir", type=Path, default=GENERATED_DIR)
    args = parser.parse_args()
    ensure_dirs()
    t0 = time.time()

    if args.init:
        print("[1/4] 执行 MySQL 建表脚本")
        run_sql_file(PROJECT_ROOT / "sql" / "mysql" / "01_schema.sql")
        run_sql_file(PROJECT_ROOT / "sql" / "mysql" / "02_ads_schema.sql")
    if args.truncate:
        print("[2/4] 清空业务表（保留 ADS 结果表）")
        truncate_tables()

    manifest_path = args.data_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else None
    if manifest is None:
        raise SystemExit("未找到 manifest.json，请先运行 generate.py")

    print("[3/4] 批量导入 CSV")
    results = {}
    for t in LOAD_ORDER:
        csv_path = args.data_dir / f"{t}.csv"
        if not csv_path.exists():
            raise SystemExit(f"缺少 {csv_path}")
        start = time.time()
        try:
            n = load_with_infile(t, csv_path)
            method = "LOAD DATA LOCAL INFILE"
        except Exception as exc:
            print(f"  [INFO] {t} LOAD DATA 失败，回退分批 INSERT：{exc}")
            n = load_with_batches(t, csv_path)
            method = "executemany"
        results[t] = n
        print(f"  {t:<20} {n:>10,} 行  {method}  {time.time()-start:.1f}s")

    print("[4/4] 核对记录数")
    actual = verify_counts(manifest)
    print(json.dumps(actual, ensure_ascii=False, indent=2))
    print(f"完成，总耗时 {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
