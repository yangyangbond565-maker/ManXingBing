package cn.edu.gdut.chronic;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class ApiSmokeTest {
    @Autowired
    MockMvc mvc;

    @Test
    void overviewReturnsRealNumbers() throws Exception {
        mvc.perform(get("/api/dashboard/overview"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.totalPatients").value(100000))
                .andExpect(jsonPath("$.data.totalDiseaseRecords").value(165087));
    }

    @Test
    void healthAndProfileWork() throws Exception {
        mvc.perform(get("/api/health-score/overview"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.summary.totalPatients").value(100000))
                .andExpect(jsonPath("$.data.levels.length()").value(5));
        mvc.perform(get("/api/patient-profile"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.rows.length()").value(33));
    }

    @Test
    void patientDetailWorks() throws Exception {
        mvc.perform(get("/api/patients/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.patient.patientId").value(1))
                .andExpect(jsonPath("$.data.diseases").isArray());
    }
}
