package cn.edu.gdut.chronic.controller;

import cn.edu.gdut.chronic.common.ApiResponse;
import cn.edu.gdut.chronic.common.PageResult;
import cn.edu.gdut.chronic.service.PatientService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/patients")
public class PatientController {
    private final PatientService service;
    public PatientController(PatientService service) { this.service = service; }

    @GetMapping
    public ApiResponse<PageResult<Map<String, Object>>> list(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) String gender,
            @RequestParam(required = false) String province,
            @RequestParam(required = false) String level,
            @RequestParam(required = false) Integer minAge,
            @RequestParam(required = false) Integer maxAge) {
        return ApiResponse.ok(service.list(page, size, keyword, gender, province, level, minAge, maxAge));
    }

    @GetMapping("/{patientId}")
    public ApiResponse<Map<String, Object>> detail(@PathVariable int patientId) {
        return ApiResponse.ok(service.detail(patientId));
    }
}
