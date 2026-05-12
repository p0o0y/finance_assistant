package demo.senior_project.domain.report.batch;

import demo.senior_project.domain.report.ConsumptionReport;
import demo.senior_project.domain.report.dto.UserYearMonth;
import demo.senior_project.domain.transaction.domain.entity.CardTransaction;
import demo.senior_project.domain.transaction.repository.CardTransactionJdbcRepository;
import demo.senior_project.domain.transaction.repository.CardTransactionRepository;
import demo.senior_project.domain.user.domain.User;
import demo.senior_project.domain.user.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.jspecify.annotations.Nullable;
import org.springframework.batch.infrastructure.item.ItemProcessor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cglib.core.Local;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import tools.jackson.databind.ObjectMapper;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Slf4j
@Component
@RequiredArgsConstructor
public class ReportItemProcessor implements ItemProcessor<UserYearMonth, ConsumptionReport> {
    private final CardTransactionRepository cardTransactionRepository;
    private final ObjectMapper objectMapper;
    private final RestClient restClient = RestClient.create(); // 순차처리

    @Value("${seraph.report.url}")
    private String seraph_repot_url;

    @Override
    public  ConsumptionReport process(UserYearMonth item) throws Exception {
        User user = item.getUser();
        String yearMonth = item.getYearMonth();
        log.info("processor 시작 user {},{} ",user.getUserId(),yearMonth);

        LocalDate date = LocalDate.parse(yearMonth+"-01");
        LocalDateTime start = date.withDayOfMonth(1).atStartOfDay();
        LocalDateTime end = date.withDayOfMonth(date.lengthOfMonth()).atTime(23,59,59);


        List<CardTransaction> transactions = cardTransactionRepository.findByUserCard_UserAndApprovedAtBetween(user,start,end);

        if(transactions.isEmpty()){
            log.info("processor : User {} 거래내역 없음 -> 스킵",yearMonth);
            return null;
        }
        //1. total 총액
        long totalAmount = transactions.stream()
                .mapToLong(t->t.getAmount().longValue())
                .sum();

        //2. 카테고리 별 지출 groupingBy(기준, 집계방법)
        Map<String,Long> categoryStats = transactions.stream()
                .filter(t->t.getStoreType()!=null)
                .collect(Collectors.groupingBy(CardTransaction::getStoreType,
                        Collectors.summingLong(t->t.getAmount().longValue())));

        //3.자주 간 가맹점 Top 3
        List<Map<String, Object>> topStores = transactions.stream()
                .collect(Collectors.groupingBy(
                        CardTransaction::getStoreName,
                        Collectors.counting()
                ))
                .entrySet().stream()
                .filter(e->e.getValue()>=3)
                // 방문 횟수 내림차순
                .sorted(Map.Entry.<String, Long>comparingByValue().reversed())
                .limit(4)
                .map(e -> {
                    Map<String, Object> store = new LinkedHashMap<>();
                    store.put("name", e.getKey());
                    store.put("count", e.getValue());
                    String storeType = transactions.stream()
                            .filter(t -> e.getKey().equals(t.getStoreName()) && t.getStoreType() != null)
                            .map(CardTransaction::getStoreType)
                            .findFirst()
                            .orElse("기타");
                    store.put("type",storeType);
                    return store;
                })
                .toList();

        // 금액 기준 top  가게
        List<Map<String, Object>> topAmountStores = transactions.stream()
                .filter(t->t.getStoreName()!=null)
                .collect(Collectors.groupingBy(
                        CardTransaction::getStoreName,
                        Collectors.summingLong(t -> t.getAmount().longValue())
                ))
                .entrySet().stream()
                // 금액 내림차순
                .sorted(Map.Entry.<String, Long>comparingByValue().reversed())
                .limit(3)
                .map(e -> {
                    Map<String, Object> store = new LinkedHashMap<>();
                    store.put("name", e.getKey());
                    store.put("total_amount", e.getValue());
                    String storeType = transactions.stream()
                            .filter(t -> e.getKey().equals(t.getStoreName()) && t.getStoreType() != null)
                            .map(CardTransaction::getStoreType)
                            .findFirst()
                            .orElse("기타");
                    store.put("type", storeType);
                    return store;
                })
                .toList();

        // 정기결제
        List<String> autoPayments = transactions.stream()
                .map(CardTransaction::getStoreName)
                .filter(name -> name != null && (
                        name.contains("자동") || name.contains("정기") || name.contains("납부") ||
                                name.contains("넷플릭스") || name.contains("유튜브") ||
                                name.contains("티빙") || name.contains("스포티파이") ||
                                name.contains("디즈니") || name.contains("웨이브")
                ))
                .distinct()
                .toList();

        // report 호출
        Map<String ,Object> requestBody = new LinkedHashMap<>();
        requestBody.put("user_id",user.getUserId());
        requestBody.put("year_month",yearMonth);
        requestBody.put("total_amount",totalAmount);
        // 카테고리 top3만
        Map<String, Long> top3Categories = categoryStats.entrySet().stream()
                .sorted(Map.Entry.<String, Long>comparingByValue().reversed())
                .limit(3)
                .collect(Collectors.toMap(
                        Map.Entry::getKey,
                        Map.Entry::getValue,
                        (e1, e2) -> e1,
                        LinkedHashMap::new
                ));

        requestBody.put("category_stats",top3Categories);
        requestBody.put("top_stores",topStores);
        requestBody.put("top_stores_by_amount", topAmountStores);
        requestBody.put("auto_payments", autoPayments);
        String reportText;
        try {
            Map response = restClient.post()
                    .uri(seraph_repot_url)
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(requestBody)
                    .retrieve()
                    .body(Map.class);
            reportText = (String) response.get("report_text");
            log.info("process user {} 의 {} 리포트 생성 완료",user.getUserId(),yearMonth);
        }catch (Exception e){
            log.error("[Processor] User {} {} FastAPI 실패: {}",
                    user.getUserId(), yearMonth, e.getMessage());
            reportText = "리포트 생성 실패";
        }
        return ConsumptionReport.builder()
                .user(user)
                .yearMonth(yearMonth)
                .totalAmount(totalAmount)
                // Map → JSON 문자열로 변환해서 DB 저장
                // 조회 시 다시 Map으로 파싱
                .categoryStats(objectMapper.writeValueAsString(categoryStats))
                .topStores(objectMapper.writeValueAsString(topStores))
                .topStoresByAmount(objectMapper.writeValueAsString(topAmountStores))
                .reportText(reportText)
                .createdAt(LocalDateTime.now())
                .build();
    }
}
