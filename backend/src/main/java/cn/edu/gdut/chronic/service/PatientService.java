package cn.edu.gdut.chronic.service;

import cn.edu.gdut.chronic.common.BusinessException;
import cn.edu.gdut.chronic.common.PageResult;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
public class PatientService {
    private final NamedParameterJdbcTemplate jdbc;

    public PatientService(NamedParameterJdbcTemplate jdbc) { this.jdbc = jdbc; }

    public PageResult<Map<String, Object>> list(int page, int size, String keyword, String gender,
                                                String province, String level, Integer minAge, Integer maxAge) {
        page = Math.max(1, page);
        size = Math.min(100, Math.max(1, size));
        StringBuilder where = new StringBuilder(" WHERE 1=1");
        MapSqlParameterSource p = new MapSqlParameterSource();
        if (keyword != null && !keyword.trim().isEmpty()) {
            String kw = keyword.trim();
            where.append(" AND (CAST(p.patient_id AS CHAR) LIKE :kw OR p.province LIKE :kw OR p.city LIKE :kw)");
            p.addValue("kw", "%" + kw + "%");
        }
        if (gender != null && !gender.isEmpty()) { where.append(" AND p.gender = :gender"); p.addValue("gender", gender); }
        if (province != null && !province.isEmpty()) { where.append(" AND p.province = :province"); p.addValue("province", province); }
        if (level != null && !level.isEmpty()) { where.append(" AND s.health_level = :level"); p.addValue("level", level); }
        if (minAge != null) { where.append(" AND p.age >= :minAge"); p.addValue("minAge", minAge); }
        if (maxAge != null) { where.append(" AND p.age <= :maxAge"); p.addValue("maxAge", maxAge); }

        String base = " FROM patient_info p LEFT JOIN ads_health_score s ON p.patient_id = s.patient_id" + where;
        Long total = jdbc.queryForObject("SELECT COUNT(*)" + base, p, Long.class);
        p.addValue("limit", size).addValue("offset", (page - 1) * size);
        List<Map<String, Object>> rows = jdbc.queryForList("""
            SELECT p.patient_id AS patientId, p.gender, p.age, p.province, p.city,
                   p.create_time AS createTime, s.health_score AS healthScore,
                   s.health_level AS healthLevel
            """ + base + " ORDER BY p.patient_id LIMIT :limit OFFSET :offset", p);
        return new PageResult<>(rows, total == null ? 0 : total, page, size);
    }

    public Map<String, Object> detail(int patientId) {
        List<Map<String, Object>> patients = jdbc.queryForList("""
            SELECT patient_id AS patientId, gender, age, province, city,
                   id_number AS idNumber, phone, create_time AS createTime
            FROM patient_info WHERE patient_id = :id
        """, new MapSqlParameterSource("id", patientId));
        if (patients.isEmpty()) throw new BusinessException(404, "患者不存在：" + patientId);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("patient", patients.get(0));
        out.put("diseases", jdbc.queryForList("""
            SELECT disease_type AS diseaseType, disease_name AS diseaseName,
                   diagnose_date AS diagnoseDate, severity, hospital, doctor_id AS doctorId
            FROM disease_record WHERE patient_id = :id ORDER BY diagnose_date DESC
        """, new MapSqlParameterSource("id", patientId)));
        out.put("checkups", jdbc.queryForList("""
            SELECT checkup_date AS checkupDate, sbp, dbp, fasting_glucose AS fastingGlucose,
                   hba1c, tc, tg, hdl, ldl, bmi, heart_rate AS heartRate,
                   creatinine, uric_acid AS uricAcid
            FROM health_checkup WHERE patient_id = :id ORDER BY checkup_date DESC LIMIT 10
        """, new MapSqlParameterSource("id", patientId)));
        out.put("lifestyle", jdbc.queryForList("""
            SELECT smoking_status AS smokingStatus, smoking_amount AS smokingAmount,
                   drinking_status AS drinkingStatus, exercise_freq AS exerciseFreq,
                   sleep_hours AS sleepHours, diet_pattern AS dietPattern
            FROM lifestyle WHERE patient_id = :id
        """, new MapSqlParameterSource("id", patientId)));
        out.put("visits", jdbc.queryForList("""
            SELECT visit_date AS visitDate, visit_type AS visitType, hospital, department,
                   diagnosis, cost, insurance_pay AS insurancePay, self_pay AS selfPay,
                   stay_days AS stayDays
            FROM visit_record WHERE patient_id = :id ORDER BY visit_date DESC LIMIT 20
        """, new MapSqlParameterSource("id", patientId)));
        out.put("medications", jdbc.queryForList("""
            SELECT drug_name AS drugName, drug_type AS drugType, dosage,
                   start_date AS startDate, end_date AS endDate, cost,
                   is_effective AS isEffective
            FROM medication_record WHERE patient_id = :id ORDER BY start_date DESC LIMIT 20
        """, new MapSqlParameterSource("id", patientId)));
        out.put("followups", jdbc.queryForList("""
            SELECT follow_date AS followDate, follow_type AS followType,
                   symptom_status AS symptomStatus, medication_adherence AS medicationAdherence,
                   doctor_advice AS doctorAdvice, next_follow_date AS nextFollowDate
            FROM follow_up WHERE patient_id = :id ORDER BY follow_date DESC LIMIT 20
        """, new MapSqlParameterSource("id", patientId)));
        List<Map<String, Object>> scores = jdbc.queryForList("""
            SELECT bp_score AS bpScore, glucose_score AS glucoseScore, bmi_score AS bmiScore,
                   lipid_score AS lipidScore, hr_score AS hrScore, smoking_score AS smokingScore,
                   drinking_score AS drinkingScore, exercise_score AS exerciseScore,
                   health_score AS healthScore, health_level AS healthLevel, scored_at AS scoredAt
            FROM ads_health_score WHERE patient_id = :id
        """, new MapSqlParameterSource("id", patientId));
        out.put("healthScore", scores.isEmpty() ? null : scores.get(0));
        return out;
    }
}
