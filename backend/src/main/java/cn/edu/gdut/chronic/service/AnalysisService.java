package cn.edu.gdut.chronic.service;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
public class AnalysisService {
    private final JdbcTemplate jdbc;

    public AnalysisService(JdbcTemplate jdbc) { this.jdbc = jdbc; }

    public Map<String, Object> overview() {
        return jdbc.queryForMap("""
            SELECT total_patients AS totalPatients, total_disease_records AS totalDiseaseRecords,
                   total_visits AS totalVisits, total_medications AS totalMedications,
                   total_followups AS totalFollowups, avg_health_score AS avgHealthScore,
                   high_risk_count AS highRiskCount, high_risk_rate AS highRiskRate,
                   total_cost AS totalCost, avg_cost AS avgCost,
                   data_start_year AS dataStartYear, data_end_year AS dataEndYear,
                   updated_at AS updatedAt
            FROM ads_overview WHERE id = 1
        """);
    }

    public Map<String, Object> patientProfile() {
        List<Map<String, Object>> rows = jdbc.queryForList("""
            SELECT dimension_type AS dimensionType, dimension_value AS dimensionValue,
                   patient_count AS patientCount, percentage, avg_age AS avgAge,
                   extra_value AS extraValue
            FROM ads_patient_profile
            ORDER BY FIELD(dimension_type,'gender','age','province','age_gender'), patient_count DESC
        """);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("rows", rows);
        out.put("totalPatients", jdbc.queryForObject("SELECT COUNT(*) FROM patient_info", Long.class));
        out.put("topProvince", jdbc.queryForList("""
            SELECT dimension_value AS province, patient_count AS patientCount FROM ads_patient_profile
            WHERE dimension_type='province' ORDER BY patient_count DESC LIMIT 5
        """));
        return out;
    }

    public Map<String, Object> diseaseDistribution() {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("diseaseTypes", jdbc.queryForList("""
            SELECT disease_type AS diseaseType, record_count AS recordCount,
                   patient_count AS patientCount, percentage,
                   severe_count AS severeCount, severe_rate AS severeRate
            FROM ads_disease_dist ORDER BY patient_count DESC
        """));
        out.put("severity", jdbc.queryForList("""
            SELECT disease_type AS diseaseType, severity, record_count AS recordCount, percentage
            FROM ads_severity ORDER BY disease_type, FIELD(severity,'轻度','中度','重度')
        """));
        out.put("comorbidity", jdbc.queryForList("""
            SELECT disease_count AS diseaseCount, patient_count AS patientCount, percentage
            FROM ads_comorbidity ORDER BY disease_count
        """));
        out.put("summary", jdbc.queryForMap("""
            SELECT COUNT(*) AS totalRecords, COUNT(DISTINCT patient_id) AS totalPatients,
                   COUNT(DISTINCT disease_type) AS diseaseTypes
            FROM disease_record
        """));
        return out;
    }

    public List<Map<String, Object>> riskFactors(String factorType) {
        StringBuilder sql = new StringBuilder("""
            SELECT factor_type AS factorType, factor_value AS factorValue,
                   disease_type AS diseaseType, patient_count AS patientCount,
                   exposure_rate AS exposureRate, avg_sbp AS avgSbp,
                   avg_glucose AS avgGlucose, avg_bmi AS avgBmi
            FROM ads_risk_factor WHERE 1=1
        """);
        List<Object> args = new ArrayList<>();
        if (factorType != null && !factorType.isEmpty()) {
            sql.append(" AND factor_type = ?"); args.add(factorType);
        }
        sql.append(" ORDER BY factor_type, disease_type, patient_count DESC");
        return jdbc.queryForList(sql.toString(), args.toArray());
    }

    public Map<String, Object> visits(String analysisType) {
        Map<String, Object> out = new LinkedHashMap<>();
        String where = (analysisType == null || analysisType.isEmpty()) ? "" : " WHERE analysis_type = ?";
        Object[] args = (analysisType == null || analysisType.isEmpty()) ? new Object[]{} : new Object[]{analysisType};
        out.put("rows", jdbc.queryForList("""
            SELECT analysis_type AS analysisType, dimension_value AS dimensionValue,
                   visit_count AS visitCount, patient_count AS patientCount,
                   avg_cost AS avgCost, total_cost AS totalCost,
                   avg_reimbursement_rate AS avgReimbursementRate,
                   avg_stay_days AS avgStayDays
            FROM ads_visit_analysis
        """ + where + " ORDER BY analysis_type, visit_count DESC", args));
        out.put("summary", jdbc.queryForMap("""
            SELECT COUNT(*) AS totalVisits, COUNT(DISTINCT patient_id) AS totalPatients,
                   ROUND(AVG(cost),2) AS avgCost, ROUND(SUM(cost),2) AS totalCost,
                   ROUND(AVG(insurance_pay * 100.0 / NULLIF(cost,0)),2) AS avgReimbursementRate
            FROM visit_record
        """));
        return out;
    }

    public Map<String, Object> medications(String analysisType) {
        Map<String, Object> out = new LinkedHashMap<>();
        String where = (analysisType == null || analysisType.isEmpty()) ? "" : " WHERE analysis_type = ?";
        Object[] args = (analysisType == null || analysisType.isEmpty()) ? new Object[]{} : new Object[]{analysisType};
        out.put("rows", jdbc.queryForList("""
            SELECT analysis_type AS analysisType, dimension_value AS dimensionValue,
                   usage_count AS usageCount, patient_count AS patientCount,
                   avg_cost AS avgCost, effective_rate AS effectiveRate, rank_no AS rankNo
            FROM ads_medication_analysis
        """ + where + " ORDER BY analysis_type, usage_count DESC", args));
        out.put("byDisease", jdbc.queryForList("""
            SELECT disease_type AS diseaseType, drug_name AS drugName,
                   usage_count AS usageCount, rank_no AS rankNo
            FROM ads_drug_by_disease ORDER BY disease_type, rank_no
        """));
        out.put("summary", jdbc.queryForMap("""
            SELECT COUNT(*) AS totalMedications, COUNT(DISTINCT patient_id) AS totalPatients,
                   COUNT(DISTINCT drug_name) AS drugCount,
                   ROUND(SUM(CASE WHEN is_effective='是' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),2) AS effectiveRate
            FROM medication_record
        """));
        return out;
    }

    public Map<String, Object> trend(String grain) {
        String g = (grain == null || grain.isEmpty()) ? "year" : grain;
        List<Map<String, Object>> rows = jdbc.queryForList("""
            SELECT grain, period, disease_type AS diseaseType, cases,
                   predicted_cases AS predictedCases, slope, intercept, r2, trend,
                   is_forecast AS isForecast
            FROM ads_trend WHERE grain IN ('year', 'month', ?) ORDER BY period, disease_type
        """, g);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("grain", g);
        out.put("rows", rows);
        List<Map<String, Object>> forecast = new ArrayList<>();
        for (Map<String, Object> r : rows) {
            if (Integer.valueOf(1).equals(r.get("isForecast"))) forecast.add(r);
        }
        out.put("forecast", forecast);
        if (!forecast.isEmpty()) {
            Map<String, Object> first = forecast.get(0);
            Map<String, Object> metrics = new LinkedHashMap<>();
            metrics.put("slope", first.get("slope"));
            metrics.put("intercept", first.get("intercept"));
            metrics.put("r2", first.get("r2"));
            metrics.put("trend", first.get("trend"));
            metrics.put("algorithm", "最小二乘一元线性回归");
            metrics.put("trainRange", "2018-2025");
            metrics.put("forecastRange", "2026-2029");
            out.put("metrics", metrics);
        }
        return out;
    }

    public Map<String, Object> healthOverview() {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("levels", jdbc.queryForList("""
            SELECT level, patient_count AS patientCount, avg_score AS avgScore,
                   percentage, sort_no AS sortNo
            FROM ads_health_level ORDER BY sort_no
        """));
        out.put("ageGroups", jdbc.queryForList("""
            SELECT age_group AS ageGroup, COUNT(*) AS patientCount,
                   ROUND(AVG(health_score),1) AS avgScore,
                   ROUND(SUM(CASE WHEN health_score<50 THEN 1 ELSE 0 END)*100.0/COUNT(*),2) AS highRiskRate
            FROM ads_health_score GROUP BY age_group
            ORDER BY FIELD(age_group,'青年(<30)','中青年(30-44)','中年(45-59)','中老年(60-74)','老年(75+)')
        """));
        out.put("genders", jdbc.queryForList("""
            SELECT gender, COUNT(*) AS patientCount, ROUND(AVG(health_score),1) AS avgScore
            FROM ads_health_score GROUP BY gender
        """));
        out.put("provinces", jdbc.queryForList("""
            SELECT province, COUNT(*) AS patientCount, ROUND(AVG(health_score),1) AS avgScore,
                   ROUND(SUM(CASE WHEN health_score<50 THEN 1 ELSE 0 END)*100.0/COUNT(*),2) AS highRiskRate
            FROM ads_health_score GROUP BY province ORDER BY avgScore DESC LIMIT 16
        """));
        out.put("scoreBins", jdbc.queryForList("""
            SELECT FLOOR(health_score/5)*5 AS scoreBin, COUNT(*) AS patientCount
            FROM ads_health_score GROUP BY scoreBin ORDER BY scoreBin
        """));
        out.put("summary", jdbc.queryForMap("""
            SELECT COUNT(*) AS totalPatients, ROUND(AVG(health_score),1) AS avgScore,
                   SUM(CASE WHEN health_score<50 THEN 1 ELSE 0 END) AS highRiskCount,
                   ROUND(SUM(CASE WHEN health_score<50 THEN 1 ELSE 0 END)*100.0/COUNT(*),2) AS highRiskRate,
                   MIN(health_score) AS minScore, MAX(health_score) AS maxScore
            FROM ads_health_score
        """));
        return out;
    }

    public Map<String, Object> dataQuality() {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("tables", jdbc.queryForList("""
            SELECT table_name AS tableName, before_count AS beforeCount, after_count AS afterCount,
                   removed_count AS removedCount, null_issues AS nullIssues, dup_issues AS dupIssues,
                   orphan_issues AS orphanIssues, invalid_issues AS invalidIssues,
                   status, checked_at AS checkedAt
            FROM ads_data_quality ORDER BY FIELD(table_name,
              'patient_info','disease_record','health_checkup','lifestyle','visit_record','medication_record','follow_up')
        """));
        out.put("summary", jdbc.queryForMap("""
            SELECT SUM(before_count) AS totalBefore, SUM(after_count) AS totalAfter,
                   SUM(removed_count) AS totalRemoved, SUM(null_issues+dup_issues+orphan_issues+invalid_issues) AS totalIssues,
                   SUM(CASE WHEN status='PASS' THEN 1 ELSE 0 END) AS passedTables
            FROM ads_data_quality
        """));
        return out;
    }

    public List<Map<String, Object>> moduleRuns() {
        return jdbc.queryForList("""
            SELECT module_code AS moduleCode, module_name AS moduleName, status,
                   row_count AS rowCount, started_at AS startedAt, finished_at AS finishedAt, detail
            FROM ads_module_run ORDER BY module_code
        """);
    }
}
