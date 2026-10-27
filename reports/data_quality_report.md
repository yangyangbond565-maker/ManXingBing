# 数据质量检查报告

- 生成时间：2026-10-20T20:29:57
- 统计口径：10万指 patient_info 患者人数；七表总行数单独统计，不相加冒充 10 万。
- 患者人数：**100,000**（达标）
- 七表总行数：**2,065,156**
- 问题总数：**0**，其中关键问题 **0**
- 结论：**PASS**

## 各表记录数与检查结果

| 表名 | 记录数 | 空值 | 重复 | 孤立外键 | 非法值/日期 | 结论 |
|---|---:|---:|---:|---:|---:|---|
| patient_info | 100,000 | 0 | 0 | 0 | 0 | 通过 |
| disease_record | 165,087 | 0 | 0 | 0 | 0 | 通过 |
| health_checkup | 300,022 | 0 | 0 | 0 | 0 | 通过 |
| lifestyle | 100,000 | 0 | 0 | 0 | 0 | 通过 |
| visit_record | 550,070 | 0 | 0 | 0 | 0 | 通过 |
| medication_record | 549,587 | 0 | 0 | 0 | 0 | 通过 |
| follow_up | 300,390 | 0 | 0 | 0 | 0 | 通过 |

## 检查项明细

### patient_info

- null_required：0（关键）
- duplicate_pk：0（关键）
- duplicate_id_number：0（关键）
- invalid_age：0（关键）
- invalid_gender：0（关键）
- invalid_phone：0（关键）
- invalid_id_length：0（关键）
- future_create_time：0（关键）

### disease_record

- orphan_patient：0（关键）
- null_required：0（关键）
- invalid_severity：0（关键）
- future_diagnose：0（关键）
- before_create：0（关键）

### health_checkup

- orphan_patient：0（关键）
- invalid_values：0（关键）
- future_checkup：0（关键）

### lifestyle

- orphan_patient：0（关键）
- duplicate_patient：0（关键）
- invalid_values：0（关键）

### visit_record

- orphan_patient：0（关键）
- invalid_values：0（关键）
- cost_balance：0（关键）
- future_visit：0（关键）

### medication_record

- orphan_patient：0（关键）
- invalid_dates：0（关键）
- invalid_values：0（关键）

### follow_up

- orphan_patient：0（关键）
- invalid_values：0（关键）
