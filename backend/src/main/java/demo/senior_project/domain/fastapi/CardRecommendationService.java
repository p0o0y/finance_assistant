package demo.senior_project.domain.fastapi;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;

import java.util.Map;
import java.time.Duration;
@Service
public class CardRecommendationService {
    private final String fastApiUrl;
    private final RestClient restClient;

    public CardRecommendationService( @Value("${seraph.url}") String url) {
        this.fastApiUrl = url;

        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(Duration.ofSeconds(10));
        factory.setReadTimeout(Duration.ofSeconds(120)); // RAG 파이프라인 대기

        this.restClient = RestClient.builder()
                .requestFactory(factory)
                .build();
    }

    public CardResponse getRecommendation(String query, String userReport) {
        Map<String, String> requestBody = Map.of(
                "query", query,
                "user_report", userReport
        );

        try {
            CardResponse response = restClient.post()
                    .uri(fastApiUrl)
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(requestBody)
                    .retrieve()
                    .body(CardResponse.class);

            if (response == null) {
                throw new RuntimeException("FastAPI 응답이 비어 있습니다.");
            }
            return response;

        } catch (ResourceAccessException e) {
            // 타임아웃 or 연결 실패
            throw new RuntimeException("카드 추천 서버 연결 실패 (타임아웃): " + e.getMessage());
        } catch (Exception e) {
            throw new RuntimeException("카드 추천 서비스 오류: " + e.getMessage());
        }
    }
}

