# -*- coding: utf-8 -*-
"""MySQL -> Hive ODS 同步。

三种落地方式：
  python -m chronic_disease.sync_mysql_to_hive --mode local
  python -m chronic_disease.sync_mysql_to_hive --mode hdfs      (hdfs dfs CLI)
  python -m chronic_disease.sync_mysql_to_hive --mode webhdfs   (远程 WebHDFS)

默认 auto：优先 hdfs CLI，失败回退 local，并在报告中如实记录。
导出格式为 UTF-8 TSV，NULL 使用 \\N，供 Hive EXTERNAL TABLE 直接读取。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import requests

from .config import HDFS_BASE, HDFS_URI, PROJECT_ROOT, SYNC_DIR, TABLES
from .db import connect

COLUMNS = {
    "patient_info": ["patient_id", "gender", "age", "province", "city", "id_number", "phone", "create_time"],
    "disease_record": ["record_id", "patient_id", "disease_type", "disease_name", "diagnose_date", "severity", "doctor_id", "hospital"],
    "health_checkup": ["checkup_id", "patient_id", "checkup_date", "sbp", "dbp", "fasting_glucose", "hba1c", "tc", "tg", "hdl", "ldl", "bmi", "heart_rate", "creatinine", "uric_acid"],
    "lifestyle": ["lifestyle_id", "patient_id", "smoking_status", "smoking_amount", "drinking_status", "exercise_freq", "sleep_hours", "diet_pattern"],
    "visit_record": ["visit_id", "patient_id", "visit_date", "visit_type", "hospital", "department", "diagnosis", "cost", "insurance_pay", "self_pay", "stay_days"],
    "medication_record": ["med_id", "patient_id", "drug_name", "drug_type", "dosage", "start_date", "end_date", "cost", "is_effective"],
    "follow_up": ["follow_id", "patient_id", "follow_date", "follow_type", "symptom_status", "medication_adherence", "doctor_advice", "next_follow_date"],
}


def clean_value(v) -> str:
    if v is None:
        return r"\N"
    if hasattr(v, "isoformat"):
        return v.isoformat()
    s = str(v).replace("\t", " ").replace("\r", " ").replace("\n", " ")
    return s


def export_table(table: str, limit: int | None = None) -> tuple[Path, int]:
    out_dir = SYNC_DIR / table
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "data.tsv"
    cols = COLUMNS[table]
    sql = f"SELECT {','.join(cols)} FROM {table}"
    if limit:
        sql += f" LIMIT {int(limit)}"
    conn = connect()
    n = 0
    try:
        with conn.cursor() as cur, path.open("w", encoding="utf-8", newline="\n") as f:
            cur.execute(sql)
            while True:
                rows = cur.fetchmany(20000)
                if not rows:
                    break
                for row in rows:
                    f.write("\t".join(clean_value(v) for v in row) + "\n")
                    n += 1
    finally:
        conn.close()
    return path, n


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print("  $", " ".join(cmd), flush=True)
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=check)


def hdfs_available() -> bool:
    hdfs = shutil.which("hdfs")
    if not hdfs:
        return False
    try:
        run([hdfs, "dfs", "-ls", "/"], check=True)
        return True
    except Exception:
        return False


def upload_hdfs(local_file: Path, table: str) -> str:
    remote = f"{HDFS_BASE}/ods/{table}"
    hdfs = shutil.which("hdfs") or "hdfs"
    run([hdfs, "dfs", "-mkdir", "-p", remote])
    run([hdfs, "dfs", "-rm", "-f", f"{remote}/data.tsv"], check=False)
    run([hdfs, "dfs", "-put", "-f", str(local_file), f"{remote}/data.tsv"])
    return f"{HDFS_URI}{remote}/data.tsv"


def upload_webhdfs(local_file: Path, table: str) -> str:
    """远程 WebHDFS 上传；自动修正 DataNode 重定向中的主机名。"""
    base = os.getenv("CHRONIC_WEBHDFS", "")
    user = os.getenv("CHRONIC_HDFS_USER", "root")
    if not base:
        raise RuntimeError("未配置 CHRONIC_WEBHDFS，例如 http://192.168.20.135:9870/webhdfs/v1")
    remote = f"{HDFS_BASE}/ods/{table}/data.tsv"
    requests.put(f"{base}{remote.rsplit('/',1)[0]}", params={"op": "MKDIRS", "user.name": user}, timeout=30)
    requests.delete(f"{base}{remote}", params={"op": "DELETE", "recursive": "true", "user.name": user}, timeout=30)
    r = requests.put(f"{base}{remote}", params={"op": "CREATE", "overwrite": "true", "user.name": user},
                     allow_redirects=False, timeout=30)
    if r.status_code not in (301, 302, 307):
        raise RuntimeError(f"WebHDFS CREATE 失败: {r.status_code} {r.text[:200]}")
    p = urlparse(r.headers["Location"])
    host = os.getenv("CHRONIC_HDFS_HOST", p.hostname or "127.0.0.1")
    fixed = urlunparse(p._replace(netloc=f"{host}:{p.port}"))
    with local_file.open("rb") as f:
        r2 = requests.put(fixed, data=f, headers={"Content-Type": "application/octet-stream"}, timeout=300)
    if r2.status_code not in (200, 201):
        raise RuntimeError(f"WebHDFS 上传失败: {r2.status_code} {r2.text[:200]}")
    return f"{base}{remote}"


def write_local_ddl(warehouse: Path) -> Path:
    import re
    warehouse = warehouse if warehouse.is_absolute() else PROJECT_ROOT / warehouse
    src = PROJECT_ROOT / "sql" / "hive" / "01_ods.sql"
    ddl = src.read_text(encoding="utf-8")
    base = "file:///" + warehouse.as_posix().lstrip("/")  # Hive local FS accepts raw unicode path
    ddl = re.sub(
        r"LOCATION '/warehouse/chronic_disease/ods/([a-z_]+)'",
        lambda m: f"LOCATION '{base}/{m.group(1)}'",
        ddl,
    )
    out = warehouse / "ods_local.sql"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(ddl, encoding="utf-8")
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["auto", "local", "hdfs", "webhdfs"], default="auto")
    parser.add_argument("--limit", type=int, default=None, help="调试用，每表最多导出 N 行")
    args = parser.parse_args()
    SYNC_DIR.mkdir(parents=True, exist_ok=True)
    log_path = PROJECT_ROOT / "logs" / "sync.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    rows = {}
    locations = {}
    t0 = time.time()
    warehouse = PROJECT_ROOT / "data" / "warehouse" / "ods"

    for table in TABLES:
        print(f"[sync] {table}", flush=True)
        local_file, n = export_table(table, args.limit)
        rows[table] = n
        mode = args.mode
        if mode == "auto":
            mode = "hdfs" if hdfs_available() else "local"
        if mode == "local":
            target = warehouse / table
            target.mkdir(parents=True, exist_ok=True)
            shutil.copy2(local_file, target / "data.tsv")
            locations[table] = ("file:///" + (target / "data.tsv").as_posix().lstrip("/"))
        elif mode == "hdfs":
            locations[table] = upload_hdfs(local_file, table)
        else:
            locations[table] = upload_webhdfs(local_file, table)
        print(f"  rows={n:,}, target={locations[table]}", flush=True)

    ddl_path = write_local_ddl(warehouse)
    report = {
        "synced_at": datetime.now().isoformat(timespec="seconds"),
        "mode": args.mode,
        "elapsed_seconds": round(time.time() - t0, 2),
        "rows": rows,
        "locations": locations,
        "local_ddl": str(ddl_path),
        "note": "local 模式落盘到项目 data/warehouse，供 Spark/Hive 本地外部表读取；hdfs/webhdfs 模式落盘到 HDFS。",
    }
    (PROJECT_ROOT / "reports" / "sync_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(report, ensure_ascii=False) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
