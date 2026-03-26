package demo.senior_project.test.service.router;


import demo.senior_project.test.dto.RouterDecisionDto;
import demo.senior_project.external.openai.OpenAIService;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;
import tools.jackson.core.type.TypeReference;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class LlmRouterService {
    private final OpenAIService openAIService;
    private final ObjectMapper objectMapper;

    @Value("classpath:/static/sql/router-schema.json")
    private Resource routerSchema;

    private Map<String, Object> schemaMap;

    @PostConstruct
    public void init() throws IOException {
        String schemaJson = new String(routerSchema.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
        this.schemaMap =  objectMapper.readValue(schemaJson, new TypeReference<Map<String, Object>>() {});
    }
    private static final String SYSTEM_PROMPT = """
                      당신은 사용자 질문을 분석해서 어떤 처리 경로로 보낼지 결정하는 라우터입니다.
                      1. SQL: 사용자의 거래 내역, 소비 금액, 특정 가게에서의 지출 등 거래와 같이 관련된 숫자/데이터 조회
                      2. RAG: 금융 약관, 서비스 이용 정책, 개념 설명, 규정 등 문서 기반 질문로 분류하세요 
                      """;

    public RouterDecisionDto route(String question) {
        try {
            String response = openAIService.completeJson(SYSTEM_PROMPT, question,this.schemaMap);
            JsonNode node = objectMapper.readTree(response);

            String typeStr = node.path("queryType").asText("SQL");

            RouterDecisionDto.QueryType queryType = "RAG".equals(typeStr)
                    ? RouterDecisionDto.QueryType.RAG
                    : RouterDecisionDto.QueryType.SQL;

            log.info("[Router] 질문: '{}' → {} ({})", question, queryType);

            return RouterDecisionDto.builder()
                    .queryType(queryType)
                    .build();

        } catch (Exception e) {
            log.warn("[Router] 분류 실패, 기본값 SQL로 처리: {}", e.getMessage());
            return RouterDecisionDto.builder()
                    .queryType(RouterDecisionDto.QueryType.SQL)
                    .build();
        }
    }
}
