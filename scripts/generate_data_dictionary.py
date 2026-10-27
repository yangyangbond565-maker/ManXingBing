# -*- coding: utf-8 -*-
"""从 information_schema 生成七张业务表的数据字典（Markdown）。"""
from pathlib import Path
from chronic_disease.db import connect

ROOT = Path(__file__).resolve().parents[1]
TABLES = ["patient_info", "disease_record", "health_checkup", "lifestyle",
          "visit_record", "medication_record", "follow_up"]
TITLES = {
    "patient_info": "患者基础信息表", "disease_record": "慢性病记录表",
    "health_checkup": "体检指标表", "lifestyle": "生活习惯表",
    "visit_record": "就诊记录表", "medication_record": "用药记录表",
    "follow_up": "随访记录表",
}
REL = {
    "patient_info": "主表；patient_id 被其余 6 张表引用",
    "disease_record": "多对一 → patient_info.patient_id",
    "health_checkup": "多对一 → patient_info.patient_id",
    "lifestyle": "一对一 → patient_info.patient_id（唯一约束）",
    "visit_record": "多对一 → patient_info.patient_id",
    "medication_record": "多对一 → patient_info.patient_id",
    "follow_up": "多对一 → patient_info.patient_id",
}
conn = connect()
try:
    with conn.cursor() as cur:
        parts = ["""# 05 数据字典与 ER 图

本数据字典由 information_schema 实际读取生成，与 MySQL 中的表结构一致。字段名、类型和注释以数据库为准。

## 1. ER 图

~~~mermaid
erDiagram
    patient_info ||--o{ disease_record : "1:N 患病"
    patient_info ||--o{ health_checkup : "1:N 体检"
    patient_info ||--|| lifestyle : "1:1 生活习惯"
    patient_info ||--o{ visit_record : "1:N 就诊"
    patient_info ||--o{ medication_record : "1:N 用药"
    patient_info ||--o{ follow_up : "1:N 随访"
    patient_info {
        int patient_id PK
        varchar gender
        int age
        varchar province
        varchar city
        varchar id_number UK
        varchar phone UK
        datetime create_time
    }
    disease_record {
        int record_id PK
        int patient_id FK
        varchar disease_type
        varchar disease_name
        date diagnose_date
        varchar severity
    }
    health_checkup {
        int checkup_id PK
        int patient_id FK
        date checkup_date
        int sbp
        int dbp
        decimal fasting_glucose
        decimal bmi
    }
    lifestyle {
        int lifestyle_id PK
        int patient_id FK
        varchar smoking_status
        varchar drinking_status
        varchar exercise_freq
    }
    visit_record {
        int visit_id PK
        int patient_id FK
        date visit_date
        varchar visit_type
        decimal cost
        decimal insurance_pay
    }
    medication_record {
        int med_id PK
        int patient_id FK
        varchar drug_name
        varchar drug_type
        date start_date
        date end_date
    }
    follow_up {
        int follow_id PK
        int patient_id FK
        date follow_date
        varchar follow_type
        varchar symptom_status
    }
~~~

## 2. 表关系汇总

| 子表 | 关系 | 外键 | 基数 |
|---|---|---|---|
| disease_record | 患者-疾病 | patient_id → patient_info | 1:N |
| health_checkup | 患者-体检 | patient_id → patient_info | 1:N |
| lifestyle | 患者-生活习惯 | patient_id → patient_info | 1:1 |
| visit_record | 患者-就诊 | patient_id → patient_info | 1:N |
| medication_record | 患者-用药 | patient_id → patient_info | 1:N |
| follow_up | 患者-随访 | patient_id → patient_info | 1:N |

## 3. 字段字典
"""]
        for t in TABLES:
            cur.execute("""SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY, COLUMN_DEFAULT,
                                  EXTRA, COLUMN_COMMENT
                           FROM information_schema.COLUMNS
                           WHERE TABLE_SCHEMA='chronic_disease' AND TABLE_NAME=%s
                           ORDER BY ORDINAL_POSITION""", (t,))
            rows = cur.fetchall()
            parts.append(f"\n### 3.{TABLES.index(t)+1} {t}（{TITLES[t]}）\n")
            parts.append(f"关系：{REL[t]}。实际行数：见质量报告。\n")
            parts.append("| 字段 | 类型 | 允许空 | 键 | 默认值 | 说明 |")
            parts.append("|---|---|---|---|---|---|")
            for name, typ, nullable, key, default, extra, comment in rows:
                keytxt = "PK" if key == "PRI" else ("UK" if key == "UNI" else ("FK/IDX" if key == "MUL" else ""))
                if name == "patient_id" and t != "patient_info":
                    keytxt = "FK"
                parts.append(f"| {name} | {typ} | {'是' if nullable=='YES' else '否'} | {keytxt} | {'' if default is None else default} | {comment or ''} |")
            parts.append("")
        parts.append("""## 4. 约束说明

- 主键：patient_info.patient_id 为业务主键；其余 6 表使用自增代理主键。
- 外键：6 张子表均 ON UPDATE CASCADE ON DELETE RESTRICT，防止孤立记录。
- 唯一：patient_info.id_number、phone；lifestyle.patient_id 保证一人一条习惯。
- CHECK：性别、年龄、血压、血糖、BMI、心率、金额勾稽、日期先后、枚举值。
- 索引：患者外键、日期、疾病类型、药品名称/类别、就诊类型/科室、随访日期等。
- 金额：visit_record 要求 ABS(cost - insurance_pay - self_pay) < 0.01。
- 日期：medication_record.end_date >= start_date；follow_up.next_follow_date >= follow_date。

## 5. 字段口径备注

- age 为建档时年龄，单位岁。
- sbp/dbp 单位 mmHg；fasting_glucose、tc、tg、hdl、ldl 单位 mmol/L；hba1c 单位 %；bmi 单位 kg/m²；creatinine、uric_acid 单位 umol/L。
- cost、insurance_pay、self_pay 单位元，DECIMAL(10,2)。
- id_number、phone 为程序生成虚构值，不对应真实个人。
""")
finally:
    conn.close()
out = ROOT / "docs" / "05-数据字典与ER图.md"
out.write_text("\n".join(parts), encoding="utf-8")
print("wrote", out, len(parts))
