package demo.senior_project.external.ollama;

import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.HashMap;
import java.util.Map;


@Service
public class OllamaCategoryClassifier implements CategoryClassifier{
    private final WebClient webClient;

    public OllamaCategoryClassifier( @Qualifier("ollamaWebClient") WebClient webClient) {
        this.webClient = webClient;
    }
    @Override
    public String classify(String storeName, String businessNo) {
        String promt = """
                너는 카드 소비 카테고리 분류기다
                카테고리:[카페,음식점,쇼핑,마트,교통,병원,교육,기타,미용,주거통신]
                  가맹점명: %s
                  사업자번호: %s
                반드시 카테고리 이름만 한 단어로만 답해라
                """.formatted(storeName,businessNo);

        try{
            Map<String,Object> request = new HashMap<>();
            request.put("model","qwen2.5");
            request.put("promt",promt);
            request.put("stream",false);

            Map<String,Object> response = webClient.post()
                    .uri("/api/generate")
                    .bodyValue(request)
                    .retrieve()
                    .bodyToMono(Map.class)
                    .block();
            String result = (String) response.get("response");

            return result;
        }catch (Exception e){
            return "기타";
        }
    }


}
