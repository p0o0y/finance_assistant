package demo.senior_project.domain.report.batch;

import demo.senior_project.domain.report.ConsumptionReport;
import demo.senior_project.domain.report.ConsumptionReportRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.batch.infrastructure.item.Chunk;
import org.springframework.batch.infrastructure.item.ItemWriter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@RequiredArgsConstructor
public class ReportItemWriter implements ItemWriter<ConsumptionReport> {
    private final ConsumptionReportRepository consumptionReportRepository;
    /*   chunk 단위로 처리
     * 1개씩 저장하면 DB 커넥션 N번 → 비효율
     * 10개씩 묶어서 저장 → DB 커넥션 줄이기
     */
    @Override
    public void write(Chunk<? extends ConsumptionReport> chunk) throws Exception {
        for(ConsumptionReport report : chunk){
            log.info("[writer 저장] -user {}/{}",report.getUser().getUserId(),report.getYearMonth());
            consumptionReportRepository.save(report);
        }
    }
}
