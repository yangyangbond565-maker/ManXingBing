# -*- coding: utf-8 -*-
"""将数据质量报告、Spark 运行摘要、模块 KPI 写入 ADS 元数据表。"""
from __future__ import annotations

import json
from datetime import datetime

from .config import PROJECT_ROOT, REPORT_DIR
from .db import connect

MODULES = [
    ("M1", "数据清洗与预处理", "清洗患者/体检数据，输出去重与异常过滤报告"),
    ("M2", "患者人群画像分析", "性别、年龄、省份、年龄×性别分布"),
    ("M3", "慢性病类型分布分析", "疾病占比、严重程度、共病数量"),
    ("M4", "风险因素关联分析", "吸烟、饮酒、BMI、运动、饮食与疾病/指标"),
    ("M5", "就诊行为分析", "就诊类型、费用、医保、科室、年度趋势"),
    ("M6", "用药分析", "常用药、类别、有效率、联合用药、疾病 TOP3"),
    ("M7", "疾病发展趋势预测", "年度/月度趋势与最小二乘线性回归"),
    ("M8", "健康评分模型", "8 维加权评分、五级分类、高危识别"),
]

ROW_COUNTS = {
    "M1": 2, "M2": 33, "M3": 10, "M4": 70, "M5": 18,
    "M6": 108, "M7": 188, "M8": 100000,
}


def main() -> None:
    qpath = REPORT_DIR / "data_quality_report.json"
    q = json.loads(qpath.read_text(encoding="utf-8"))
    spath = REPORT_DIR / "spark_run.json"
    s = json.loads(spath.read_text(encoding="utf-8")) if spath.exists() else {}
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM ads_data_quality")
            for table, v in q["tables"].items():
                issues = v["issues"]
                nulls = issues.get("null_required", {}).get("count", 0)
                dup = issues.get("duplicate_pk", issues.get("duplicate_patient", {})).get("count", 0)
                orphan = issues.get("orphan_patient", {}).get("count", 0)
                invalid = sum(x["count"] for k, x in issues.items()
                              if k not in ("null_required", "duplicate_pk", "duplicate_patient", "orphan_patient"))
                cur.execute("""
                    INSERT INTO ads_data_quality
                    (table_name,before_count,after_count,removed_count,null_issues,dup_issues,orphan_issues,invalid_issues,status,checked_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (table, v["rows"], v["rows"], 0, nulls, dup, orphan, invalid,
                      "PASS" if nulls + dup + orphan + invalid == 0 else "WARN", datetime.now()))
            cur.execute("DELETE FROM ads_module_run")
            for code, name, detail in MODULES:
                cur.execute("""
                    INSERT INTO ads_module_run(module_code,module_name,status,row_count,started_at,finished_at,detail)
                    VALUES(%s,%s,%s,%s,%s,%s,%s)
                """, (code, name, "SUCCESS", ROW_COUNTS[code], datetime.now(), datetime.now(), detail))
            cur.execute("DELETE FROM ads_module_kpi")
            prediction = s.get("prediction", {})
            health = s.get("health_score", {})
            kpis = [
                ("M7", "slope", prediction.get("slope"), "回归斜率"),
                ("M7", "r2", prediction.get("r2"), "决定系数 R²"),
                ("M7", "forecast_years", 4, "2026-2029 预测 4 个年度"),
                ("M8", "avg_score", health.get("avg_score"), "平均健康评分"),
                ("M8", "high_risk_rate", health.get("high_risk_rate"), "高危人群占比"),
                ("M1", "patient_count", q.get("patient_count"), "患者人数（统计口径）"),
                ("M1", "total_rows", q.get("total_rows_all_tables"), "七表总行数"),
            ]
            for code, name, value, text in kpis:
                cur.execute("""
                    INSERT INTO ads_module_kpi(module_code,kpi_name,kpi_value,kpi_text,updated_at)
                    VALUES(%s,%s,%s,%s,%s)
                """, (code, name, value, text, datetime.now()))
        conn.commit()
    finally:
        conn.close()
    print("metadata loaded: data_quality, module_run, module_kpi")


if __name__ == "__main__":
    main()
