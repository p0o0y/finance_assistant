package demo.senior_project.test.service.sql;

import demo.senior_project.global.error.BusinessException;
import demo.senior_project.global.error.ErrorCode;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import tools.jackson.databind.ObjectMapper;

import java.util.List;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class DbQueryService {
    private final JdbcTemplate jdbcTemplate;
    private final ObjectMapper objectMapper;

    /**
     * 검증된 SQL을 실행하고 결과를 반환
     */
    public List<Map<String, Object>> execute(String sql) {
        log.info("[DB Execution] SQL: {}", sql);
        try {
            // 결과가 너무 많으면 LLM 응답 토큰이 터지므로 강제로 LIMIT을 겁니다 (방어 로직)
            String safeSql = sql + " LIMIT 20";
            // List<Map<String, Object>>
            return jdbcTemplate.queryForList(safeSql);
        } catch (Exception e) {
            log.error("DB 실행 에러: {}", e.getMessage());
            throw new RuntimeException("데이터 조회 중 오류가 발생했습니다.");
        }
    }


    public String formatResults(List<Map<String, Object>> results) {
        if (results.isEmpty()) return "조회된 내역이 없습니다.";
        try {
            return objectMapper.writeValueAsString(results);
        } catch (Exception e) {
            throw new BusinessException("JSON 변환 실패", ErrorCode.INTERNAL_SERVER_ERROR);
        }
    }
}
