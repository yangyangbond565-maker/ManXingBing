package cn.edu.gdut.chronic.controller;

import cn.edu.gdut.chronic.common.ApiResponse;
import cn.edu.gdut.chronic.common.PageResult;
import cn.edu.gdut.chronic.service.AnalysisService;
import cn.edu.gdut.chronic.service.PatientService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class AnalysisController {
    private final AnalysisService analysis;
    private final PatientService patients;

    public AnalysisController(AnalysisService analysis, PatientService patients) {
        this.analysis = analysis;
        this.patients = patients;
    }

    @GetMapping("/health")
    public ApiResponse<Map<String, Object>> health() {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("status", "UP");
        m.put("service", "chronic-disease-backend");
        m.put("time", java.time.LocalDateTime.now().toString());
        return ApiResponse.ok(m);
    }

    @GetMapping("/dashboard/overview")
    public ApiResponse<Map<String, Object>> overview() { return ApiResponse.ok(analysis.overview()); }

    @GetMapping("/patient-profile")
    public ApiResponse<Map<String, Object>> patientProfile() { return ApiResponse.ok(analysis.patientProfile()); }

    @GetMapping("/disease-distribution")
    public ApiResponse<Map<String, Object>> disease() { return ApiResponse.ok(analysis.diseaseDistribution()); }

    @GetMapping("/risk-factors")
    public ApiResponse<List<Map<String, Object>>> risk(
            @RequestParam(required = false) String factor) {
        return ApiResponse.ok(analysis.riskFactors(factor));
    }

    @GetMapping("/visits")
    public ApiResponse<Map<String, Object>> visits(@RequestParam(required = false) String type) {
        return ApiResponse.ok(analysis.visits(type));
    }

    @GetMapping("/medications")
    public ApiResponse<Map<String, Object>> medications(@RequestParam(required = false) String type) {
        return ApiResponse.ok(analysis.medications(type));
    }

    @GetMapping("/trend")
    public ApiResponse<Map<String, Object>> trend(@RequestParam(defaultValue = "year") String grain) {
        return ApiResponse.ok(analysis.trend(grain));
    }

    @GetMapping("/health-score/overview")
    public ApiResponse<Map<String, Object>> healthOverview() { return ApiResponse.ok(analysis.healthOverview()); }

    @GetMapping("/health-score/patients")
    public ApiResponse<PageResult<Map<String, Object>>> healthPatients(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) String gender,
            @RequestParam(required = false) String province,
            @RequestParam(required = false) String level,
            @RequestParam(required = false) Integer minAge,
            @RequestParam(required = false) Integer maxAge) {
        return ApiResponse.ok(patients.list(page, size, keyword, gender, province, level, minAge, maxAge));
    }

    @GetMapping("/data-quality")
    public ApiResponse<Map<String, Object>> dataQuality() { return ApiResponse.ok(analysis.dataQuality()); }

    @GetMapping("/modules")
    public ApiResponse<List<Map<String, Object>>> modules() { return ApiResponse.ok(analysis.moduleRuns()); }
}
