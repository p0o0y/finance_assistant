package demo.senior_project.domain.fastapi;

import demo.senior_project.domain.report.ConsumptionReport;
import demo.senior_project.domain.report.ConsumptionReportRepository;
import demo.senior_project.domain.user.domain.User;
import demo.senior_project.global.security.oauth.CustomOauth2User;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/cards")
@RequiredArgsConstructor
public class CardRecommendController {
        private final CardRecommendationService cardRecommendationService;
        private final ConsumptionReportRepository consumptionReportRepository;

        @PostMapping("/recommend")
        public CardResponse ask(@AuthenticationPrincipal CustomOauth2User principal, @RequestBody Map<String, String> request) {
            String query = request.get("query");
            String incomingReport = request.get("user_report");

            String finalUserReport = "";
            if(incomingReport!=null && !incomingReport.strip().isEmpty()){
                User user = principal.getUser();
                List<ConsumptionReport> reports = consumptionReportRepository.findTop3ByUserOrderByYearMonthDesc(user);

                finalUserReport = reports.stream()
                        .map(r -> "[" + r.getYearMonth() + "]\n" + r.getReportText())
                        .collect(Collectors.joining("\n\n"));
            }
            else {
                finalUserReport = "";
            }

            return cardRecommendationService.getRecommendation(query, finalUserReport);
        }
    }

