package demo.senior_project.test.service.sql;

import demo.senior_project.test.dto.RewrittenQueryDto;
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
import java.time.LocalDate;
import java.util.HashMap;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class QueryRewriteService {

    private final OpenAIService openAiService;
    private final ObjectMapper objectMapper;
    @Value("classpath:/static/sql/rewrite-schema.json")
    private Resource rewriteSchema;
    private Map<String, Object> schemaMap; // 리소스 담아둠

    @PostConstruct
    public void init() throws IOException {
        // 앱 시작 시 스키마 파일을 읽어 미리 캐싱 - json파일을 map에 저장해두기
        String schemaJson = new String(rewriteSchema.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
        this.schemaMap =  objectMapper.readValue(schemaJson, new TypeReference<Map<String, Object>>() {});
    }

    /**동의어 정리
     * 실제 DB의 content 컬럼에 들어있는 값 기준*/
    private static final Map<String, String> SYNONYM_MAP = new HashMap<>() {{
        // 카페/커피
        put("스벅", "스타벅스");
        put("별다방", "스타벅스");
        put("메가", "메가커피");
        put("컴포즈", "컴포즈커피");
        put("이디야", "이디야커피");
        put("빽다방", "빽다방");
        put("투썸", "투썸플레이스");
        // 편의점
        put("씨유", "CU");
        put("세븐일레븐", "7-ELEVEN");
        put("지에스", "GS25");
        put("미니스톱", "MINISTOP");
        // 식당
        put("맥날", "맥도날드");
        put("버거킹", "BURGER KING");
        put("롯데리아", "롯데리아");
        put("bhc", "BHC");
        put("교촌", "교촌치킨");
        // 쇼핑
        put("쿠팡", "쿠팡");
        put("당근", "당근마켓");
        put("올영", "올리브영");
    }};



    public RewrittenQueryDto rewrite(String question) {
        String systemPrompt = String.format(
                "당신은 금융 거래 데이터 조회를 위한 질문 분석기입니다. 오늘 날짜는 %s이고, " +
                        "질문에서 조건들을 추출해.당신의 답변으로 다음 DB에서 데이터를 추출할 것입니다\n" +
                        "            transactions 테이블 컬럼:\n" +
                        "            - tran_date: DATE (거래 날짜)\n" +
                        "            - tran_time: TIME (거래 시간)\n" +
                        "            - out_amount: INTEGER (지출액, 단위: 원)\n" +
                        "            - in_amount: INTEGER (수입액, 단위: 원)\n" +
                        "            - content: VARCHAR (거래처명, 예: 스타벅스, GS25)\n" +
                        "            - category: VARCHAR (카테고리: 식비, 카페, 쇼핑, 교통 등)\n" +
                        "            - account_display: VARCHAR (계좌번호)\n" +
                        "            \"\"\";", LocalDate.now()
        );

        try {
            String response = openAiService.completeJson(systemPrompt, question, schemaMap);
            JsonNode node = objectMapper.readTree(response);

            // 상호명 정규화
            String rawMerchant = node.path("merchant").isTextual() ? node.path("merchant").asText() : null;
            String normalizedMerchant = (rawMerchant != null) ?
                    SYNONYM_MAP.getOrDefault(rawMerchant, rawMerchant) : null;

            return RewrittenQueryDto.builder()
                    .original(question)
                    .normalizedMerchant(normalizedMerchant)
                    .category(node.path("category").asText(null))
                    .startDate(node.path("period").path("startDate").asText(null))
                    .endDate(node.path("period").path("endDate").asText(null))
                    .intent(node.path("intent").asText("SUM"))
                    .build();

        } catch (Exception e) {
            log.error("LLM 질문 재구성 중 오류 발생", e);
            return RewrittenQueryDto.builder().original(question).build();
        }
    }
}