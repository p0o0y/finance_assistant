package demo.senior_project.domain.report.batch;

import demo.senior_project.domain.report.ConsumptionReport;
import demo.senior_project.domain.report.dto.UserYearMonth;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.batch.core.job.Job;
import org.springframework.batch.core.job.JobExecution;
import org.springframework.batch.core.job.builder.JobBuilder;
import org.springframework.batch.core.listener.JobExecutionListener;
import org.springframework.batch.core.repository.JobRepository;
import org.springframework.batch.core.step.Step;
import org.springframework.batch.core.step.builder.StepBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.transaction.PlatformTransactionManager;

@Slf4j
@Configuration
@RequiredArgsConstructor
public class ReportJobConfig {
    private final UserItemReader userYearMonthReader;
    private final ReportItemProcessor reportItemProcessor;
    private final ReportItemWriter reportItemWriter;

    private final JobRepository jobRepository; // 배치 실행 상태 DB 저장
    private final PlatformTransactionManager transactionManager;

    @Bean
    public Job reportJob(){
        return new JobBuilder("reportJob",jobRepository)
                .listener(new JobExecutionListener() {
                    @Override
                    public void afterJob(JobExecution jobExecution) {
                      log.info("job 상태 {}",jobExecution.getStatus());
                    }

                    @Override
                    public void beforeJob(JobExecution jobExecution) {
                        userYearMonthReader.reset();
                    }
                })
                .start(reportStep())
                .build();
    }

    @Bean
    public Step reportStep(){
        return new StepBuilder("reportStep",jobRepository)
                .<UserYearMonth, ConsumptionReport>chunk(10,transactionManager)
                .reader(userYearMonthReader)
                .processor(reportItemProcessor)
                .writer(reportItemWriter)
                .build();
    }
}
