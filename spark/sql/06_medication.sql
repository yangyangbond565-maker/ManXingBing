-- 模块6：常用药、类别、有效率、联合用药、疾病常用药 TOP3
USE chronic_disease_db;

INSERT OVERWRITE DIRECTORY '${ADS_BASE}/m6/medication_analysis'
USING csv OPTIONS ('header'='true', 'sep'='\t')
SELECT 'top' AS analysis_type, drug_name AS dimension_value, usage_count, patient_count,
       avg_cost, effective_rate, CAST(rank_no AS INT) AS rank_no
FROM (
  SELECT drug_name, COUNT(*) usage_count, COUNT(DISTINCT patient_id) patient_count,
         ROUND(AVG(cost), 2) avg_cost,
         ROUND(SUM(CASE WHEN is_effective = '是' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) effective_rate,
         ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) rank_no
  FROM dwd_medication_clean GROUP BY drug_name
) top_drugs WHERE rank_no <= 20
UNION ALL
SELECT 'type', drug_type, COUNT(*), COUNT(DISTINCT patient_id),
       ROUND(AVG(cost), 2),
       ROUND(SUM(CASE WHEN is_effective = '是' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2),
       CAST(NULL AS INT)
FROM dwd_medication_clean GROUP BY drug_type
UNION ALL
SELECT 'effective', drug_name, COUNT(*), COUNT(DISTINCT patient_id),
       ROUND(AVG(cost), 2),
       ROUND(SUM(CASE WHEN is_effective = '是' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2),
       CAST(NULL AS INT)
FROM dwd_medication_clean GROUP BY drug_name HAVING COUNT(*) >= 100
UNION ALL
SELECT 'combo', CAST(type_count AS STRING), SUM(1) AS usage_count, SUM(1) AS patient_count,
       CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE), CAST(NULL AS INT)
FROM (
  SELECT patient_id, COUNT(DISTINCT drug_type) type_count
  FROM dwd_medication_clean GROUP BY patient_id
) t
GROUP BY type_count;

INSERT OVERWRITE DIRECTORY '${ADS_BASE}/m6/drug_by_disease'
USING csv OPTIONS ('header'='true', 'sep'='\t')
SELECT disease_type, drug_name, usage_count, rank_no
FROM (
  SELECT d.disease_type, m.drug_name, COUNT(*) AS usage_count,
         ROW_NUMBER() OVER (PARTITION BY d.disease_type ORDER BY COUNT(*) DESC) AS rank_no
  FROM dwd_medication_clean m JOIN dwd_disease_clean d ON m.patient_id = d.patient_id
  GROUP BY d.disease_type, m.drug_name
) t WHERE rank_no <= 3
ORDER BY disease_type, rank_no;
