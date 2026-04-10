package demo.senior_project.domain.fastapi;

import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/cards")
@RequiredArgsConstructor
public class CardRecommendController {
    private final CardRecommendationService cardRecommendationService;

    @PostMapping("/recommend")
    public CardResponse ask(@RequestBody Map<String, String> request) {
        String query = request.get("query");
        String userReport = request.get("user_report");
        return cardRecommendationService.getRecommendation(query, userReport);
    }
}
