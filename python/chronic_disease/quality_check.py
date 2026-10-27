# -*- coding: utf-8 -*-
"""七张业务表的数据质量检查，生成 JSON + Markdown 报告。

检查维度：空值、重复、非法日期、非法数值、孤立外键、金额勾稽、记录数口径。
"""
from __future__ import annotations

import json
import sys
from datetime import datetime

from .config import REPORT_DIR, TABLES
from .db import connect


def scalar(cur, sql: str):
    cur.execute(sql)
    row = cur.fetchone()
    return row[0] if row else 0


def table_checks() -> dict:
    conn = connect()
    result = {}
    try:
        with conn.cursor() as cur:
            for t in TABLES:
                result[t] = {"rows": scalar(cur, f"SELECT COUNT(*) FROM {t}"), "issues": {}}

            def add(table: str, key: str, sql: str, critical: bool = True):
                value = int(scalar(cur, sql) or 0)
                result[table]["issues"][key] = {"count": value, "critical": critical}

            add("patient_info", "null_required", """
                SELECT COUNT(*) FROM patient_info
                WHERE patient_id IS NULL OR gender IS NULL OR age IS NULL
                   OR province IS NULL OR city IS NULL OR id_number IS NULL
                   OR phone IS NULL OR create_time IS NULL
            """)
            add("patient_info", "duplicate_pk", "SELECT COUNT(*) - COUNT(DISTINCT patient_id) FROM patient_info")
            add("patient_info", "duplicate_id_number", "SELECT COUNT(*) - COUNT(DISTINCT id_number) FROM patient_info")
            add("patient_info", "invalid_age", "SELECT COUNT(*) FROM patient_info WHERE age NOT BETWEEN 0 AND 120")
            add("patient_info", "invalid_gender", "SELECT COUNT(*) FROM patient_info WHERE gender NOT IN ('男','女')")
            add("patient_info", "invalid_phone", "SELECT COUNT(*) FROM patient_info WHERE CHAR_LENGTH(phone) <> 11")
            add("patient_info", "invalid_id_length", "SELECT COUNT(*) FROM patient_info WHERE CHAR_LENGTH(id_number) <> 18")
            add("patient_info", "future_create_time", "SELECT COUNT(*) FROM patient_info WHERE create_time > NOW()")

            add("disease_record", "orphan_patient", """
                SELECT COUNT(*) FROM disease_record d
                LEFT JOIN patient_info p ON d.patient_id=p.patient_id WHERE p.patient_id IS NULL
            """)
            add("disease_record", "null_required", """
                SELECT COUNT(*) FROM disease_record
                WHERE patient_id IS NULL OR disease_type IS NULL OR disease_name IS NULL
                   OR diagnose_date IS NULL OR severity IS NULL OR hospital IS NULL
            """)
            add("disease_record", "invalid_severity", "SELECT COUNT(*) FROM disease_record WHERE severity NOT IN ('轻度','中度','重度')")
            add("disease_record", "future_diagnose", "SELECT COUNT(*) FROM disease_record WHERE diagnose_date > CURDATE()")
            add("disease_record", "before_create", """
                SELECT COUNT(*) FROM disease_record d JOIN patient_info p ON d.patient_id=p.patient_id
                WHERE d.diagnose_date < DATE(p.create_time)
            """)

            add("health_checkup", "orphan_patient", """
                SELECT COUNT(*) FROM health_checkup c
                LEFT JOIN patient_info p ON c.patient_id=p.patient_id WHERE p.patient_id IS NULL
            """)
            add("health_checkup", "invalid_values", """
                SELECT COUNT(*) FROM health_checkup
                WHERE sbp NOT BETWEEN 60 AND 300 OR dbp NOT BETWEEN 30 AND 200
                   OR fasting_glucose NOT BETWEEN 1.0 AND 40.0
                   OR bmi NOT BETWEEN 12.0 AND 50.0
                   OR heart_rate NOT BETWEEN 30 AND 220
                   OR sbp <= dbp
            """)
            add("health_checkup", "future_checkup", "SELECT COUNT(*) FROM health_checkup WHERE checkup_date > CURDATE()")

            add("lifestyle", "orphan_patient", """
                SELECT COUNT(*) FROM lifestyle l
                LEFT JOIN patient_info p ON l.patient_id=p.patient_id WHERE p.patient_id IS NULL
            """)
            add("lifestyle", "duplicate_patient", "SELECT COUNT(*) - COUNT(DISTINCT patient_id) FROM lifestyle")
            add("lifestyle", "invalid_values", """
                SELECT COUNT(*) FROM lifestyle
                WHERE smoking_status NOT IN ('从不','已戒','在吸')
                   OR drinking_status NOT IN ('从不','已戒','在饮')
                   OR exercise_freq NOT IN ('无','偶尔','经常')
                   OR diet_pattern NOT IN ('清淡','正常','重口味')
                   OR sleep_hours NOT BETWEEN 0 AND 24
            """)

            add("visit_record", "orphan_patient", """
                SELECT COUNT(*) FROM visit_record v
                LEFT JOIN patient_info p ON v.patient_id=p.patient_id WHERE p.patient_id IS NULL
            """)
            add("visit_record", "invalid_values", """
                SELECT COUNT(*) FROM visit_record
                WHERE visit_type NOT IN ('门诊','急诊','住院')
                   OR cost < 0 OR insurance_pay < 0 OR self_pay < 0
                   OR stay_days NOT BETWEEN 0 AND 365
            """)
            add("visit_record", "cost_balance", """
                SELECT COUNT(*) FROM visit_record
                WHERE ABS(cost - insurance_pay - self_pay) >= 0.01
            """)
            add("visit_record", "future_visit", "SELECT COUNT(*) FROM visit_record WHERE visit_date > CURDATE()")

            add("medication_record", "orphan_patient", """
                SELECT COUNT(*) FROM medication_record m
                LEFT JOIN patient_info p ON m.patient_id=p.patient_id WHERE p.patient_id IS NULL
            """)
            add("medication_record", "invalid_dates", "SELECT COUNT(*) FROM medication_record WHERE end_date < start_date")
            add("medication_record", "invalid_values", """
                SELECT COUNT(*) FROM medication_record
                WHERE cost < 0 OR is_effective NOT IN ('是','否')
            """)

            add("follow_up", "orphan_patient", """
                SELECT COUNT(*) FROM follow_up f
                LEFT JOIN patient_info p ON f.patient_id=p.patient_id WHERE p.patient_id IS NULL
            """)
            add("follow_up", "invalid_values", """
                SELECT COUNT(*) FROM follow_up
                WHERE follow_type NOT IN ('电话','面访','线上')
                   OR symptom_status NOT IN ('好转','稳定','加重')
                   OR medication_adherence NOT IN ('好','一般','差')
                   OR next_follow_date < follow_date
            """)
    finally:
        conn.close()
    return result


def build_report() -> dict:
    tables = table_checks()
    total_rows = sum(v["rows"] for v in tables.values())
    total_issues = sum(i["count"] for v in tables.values() for i in v["issues"].values())
    critical_issues = sum(i["count"] for v in tables.values() for i in v["issues"].values() if i["critical"])
    patient_rows = tables.get("patient_info", {}).get("rows", 0)
    report = {
        "report_type": "data_quality",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "statistical_caliber": "10万指 patient_info 患者人数；七表总行数单独统计，不相加冒充 10 万。",
        "patient_count": patient_rows,
        "patient_count_ok": patient_rows == 100000,
        "total_rows_all_tables": total_rows,
        "total_issue_count": total_issues,
        "critical_issue_count": critical_issues,
        "status": "PASS" if critical_issues == 0 and patient_rows == 100000 else "FAIL",
        "tables": tables,
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "data_quality_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    lines = [
        "# 数据质量检查报告", "",
        f"- 生成时间：{report['generated_at']}",
        f"- 统计口径：{report['statistical_caliber']}",
        f"- 患者人数：**{report['patient_count']:,}**（{'达标' if report['patient_count_ok'] else '未达标'}）",
        f"- 七表总行数：**{total_rows:,}**",
        f"- 问题总数：**{total_issues}**，其中关键问题 **{critical_issues}**",
        f"- 结论：**{report['status']}**", "",
        "## 各表记录数与检查结果", "",
        "| 表名 | 记录数 | 空值 | 重复 | 孤立外键 | 非法值/日期 | 结论 |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for t, v in tables.items():
        issues = v["issues"]
        vals = sum(x["count"] for x in issues.values())
        lines.append(
            f"| {t} | {v['rows']:,} | {issues.get('null_required', {}).get('count', 0)} | "
            f"{issues.get('duplicate_pk', issues.get('duplicate_patient', {})).get('count', 0)} | "
            f"{issues.get('orphan_patient', {}).get('count', 0)} | {vals} | "
            f"{'通过' if vals == 0 else '需处理'} |"
        )
    lines += ["", "## 检查项明细", ""]
    for t, v in tables.items():
        lines.append(f"### {t}")
        lines.append("")
        for k, x in v["issues"].items():
            lines.append(f"- {k}：{x['count']}（{'关键' if x['critical'] else '提示'}）")
        lines.append("")
    (REPORT_DIR / "data_quality_report.md").write_text("\n".join(lines), encoding="utf-8")
    return report


def main() -> None:
    report = build_report()
    print(json.dumps({k: report[k] for k in
                      ["patient_count", "patient_count_ok", "total_rows_all_tables",
                       "total_issue_count", "critical_issue_count", "status"]},
                     ensure_ascii=False, indent=2))
    if report["status"] != "PASS":
        sys.exit(1)


if __name__ == "__main__":
    main()
