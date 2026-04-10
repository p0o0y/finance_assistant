package demo.senior_project.domain.fastapi;

import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.util.List;
import java.util.Map;

@Service
public class CardRecommendationService {
    private final String fastApiUrl;
    private final RestClient restClient;

    public CardRecommendationService( @Value("${seraph.url}") String url) {
        this.fastApiUrl = url;
        this.restClient =  RestClient.create();
    }

    public CardResponse getRecommendation(String query, String userReport) {
        Map<String, String> requestBody = Map.of(
                "query", query,
                "user_report", userReport
        );

        return restClient.post()
                .uri(fastApiUrl)
                .contentType(MediaType.APPLICATION_JSON)
                .body(requestBody)
                .retrieve()
                .body(CardResponse.class);
    }
}

record CardResponse(String answer, List<SourceNode> source_nodes) {} // 전체 응답
record SourceNode(String card_name, Double score) {} // 카드 정보 응답

