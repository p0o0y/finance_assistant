package demo.senior_project.external.openai;

import demo.senior_project.global.error.BusinessException;
import demo.senior_project.global.error.ErrorCode;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.ObjectMapper;

import java.util.List;
import java.util.Map;

/*@RequiredArCons로 @Qualifier("openaiWebClient") @Qualifier을 생성자의
* 파라미터로 복사해주지 않음 그래서 직접 생성자 안에서 지정해줘야함 */

@Slf4j
@Service
public class OpenAIService {
    private final WebClient webClient;
   private final ObjectMapper objectMapper;

    @Value("${openai.model}")
    private String model;

    public OpenAIService(@Qualifier("openaiWebClient") WebClient webClient, ObjectMapper objectMapper) {
        this.webClient = webClient;
        this.objectMapper = objectMapper;
    }

    public String complete(String systemPromt,String userMessage) {
        try {
            Map<String, Object> body = Map.of(
                    "model", model,
                    "messages", List.of(
                            Map.of("role", "system", "content", systemPromt),
                            Map.of("role", "user", "content", userMessage)
                    ),
                    "max_tokens", 500,
                    "temperature", 0.5
            );

            String response = webClient.post()
                    .uri("/chat/completions")
                    .bodyValue(body)
                    .retrieve()
                    .bodyToMono(String.class)
                    .block();

            JsonNode root = objectMapper.readTree(response);

            return root.path("choices")
                    .get(0)
                    .path("message")
                    .path("content")
                    .asText()
                    .trim();
        } catch (Exception e) {
            log.error("OpenAI chat completion 실패", e);
            throw new RuntimeException("LLM 호출 실패", e);
        }
    }

    public Mono<String> completeJson(String systemPrompt, String userMessage, Map<String,Object> schemaMap) {
        long startTime = System.currentTimeMillis();
        String threadName = Thread.currentThread().getName();


        Map<String, Object> body = Map.of(
                    "model", model,
                    "messages", List.of(
                            Map.of("role", "system", "content", systemPrompt),
                            Map.of("role", "user", "content", userMessage)
                    ),
                    "temperature", 0.0,
                    "response_format", Map.of(
                            "type", "json_schema",
                            "json_schema", Map.of(
                                    "name", "category_classification",
                                    "strict", true,          // 스키마
                                    "schema", schemaMap
                            )
                    )
            );

            log.info("[{}] ✅ OpenAI 호출 시작 {} ", body, systemPrompt);

            return webClient.post()
                    .uri("/chat/completions")
                    .bodyValue(body)
                    .retrieve()
                    .bodyToMono(String.class) //할 일 예약
                    .map(response -> {
                        //응답이 오면 실행될 로직 - 직원 스레드 나중 처리
                        try {
                            JsonNode root = objectMapper.readTree(response);
                            String content = root.at("/choices/0/message/content").asText().trim();
                            JsonNode contentNode = objectMapper.readTree(content);

                            log.info("[{}] ✅ OpenAI 응답 완료 ({}ms)", threadName, System.currentTimeMillis() - startTime);
                            return contentNode.get("category").asText();
                        } catch (Exception e) {
                            throw new BusinessException(ErrorCode.CATEGORY_LLM_FAIL);
                        }
                    })//비동기 코드는 try 빨리 통과해서 (네트워크 ,타임아웃등 전체 흐름 발생 전용 에러 처리 필요
                    .onErrorResume(e -> Mono.error(new BusinessException(ErrorCode.CATEGORY_LLM_FAIL)));
        }



    public Mono<String> classifyTransaction(String storeName, String bizNo,String storeType) {
        String systemPrompt = "너는 금융 데이터 분석 전문가다. 주어진 카드 거래내역을 바탕으로 소비 성격을 파악해 카테고리를 분류해라.가맹점명과 사업자번호를 최우선으로 보고 통상적으로 분류하고 , 가게타입이 '인터넷이나 '일반잡화'라고 되어 있으면 사업자번호로 검색해라.기타 카테고리는 최후의 수단이다"+
                "[카테고리별 분류 기준]\n" +
                "1. 카페: 커피전문점, 디저트 카페, 제과점, 베이커리, 아이스크림 전문점 " +
                "2. 음식점: 모든 식당, 패스트푸드, 반찬가게, 도시락 전문점, 밀키트 판매처\n" +
                "3. 쇼핑: 의류, 화장품, 전자제품, 액세서리, 문구, 소품샵, 백화점, 면세점, 온라인 쇼핑몰\n" +
                "4. 마트: 대형마트, 기업형 슈퍼마켓, 다이소" +
                "5. 교통: 택시, 버스, 지하철"+
                "6. 교육: 학원, 독서실, 스터디카페, 서점, 국가고시 응시료, 등록금" +
                "7. 미용: 미용실, 헤어샵, 네일아트, 왁싱, 피부관리실\n" +
                "8. 주거통신: 통신비, 아파트 관리비, 전기/수도세, 정기 구독 서비스\n" +
                "10. 여가놀이: 영화관, 노래방, PC방, 헬스장, 테마파크 골프장, 공연 티켓\n" +
                "11. 편의점 : 24시간 편의 시설 "+
                "12. 기타: 위 항목에 절대 해당하지 않거나, 가맹점명을 통해 용도를 전혀 유추할 수 없는 경우 (최후의 수단)";

        String userMessage = String.format("가맹점명: %s, 가게사업자번호: %s, 가게타입: %s", storeName, bizNo,storeType);

        Map<String, Object> schemaMap = Map.of(  //  JSON 스키마
                "type", "object",
                "properties", Map.of(
                        "category", Map.of(
                                "type", "string",
                                "enum", List.of("카페", "음식점", "쇼핑", "마트", "교통", "병원", "교육", "기타", "미용", "주거통신","여가","편의점")
                        )
                ),
                "required", List.of("category"),
                "additionalProperties", false
        );

        return completeJson(systemPrompt, userMessage, schemaMap);
    }
}

