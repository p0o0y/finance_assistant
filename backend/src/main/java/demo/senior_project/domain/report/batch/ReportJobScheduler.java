package demo.senior_project.domain.report.batch;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.batch.core.job.Job;
import org.springframework.batch.core.job.parameters.JobParameters;
import org.springframework.batch.core.job.parameters.JobParametersBuilder;
import org.springframework.batch.core.launch.JobLauncher;
import org.springframework.batch.core.launch.JobOperator;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Slf4j
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/batch")
public class ReportJobScheduler {
    private final JobLauncher jobLauncher;
    private final Job reportJob;

    @PostMapping("/report")
    public String runReportJob() {
        try {
            JobParameters params = new JobParametersBuilder()
                    .addLong("time", System.currentTimeMillis())
                    .toJobParameters();

            jobLauncher.run(reportJob, params);
            return "배치 실행 완료";

        } catch (Exception e) {
            log.error("[BatchController] 실행 실패: {}", e.getMessage());
            return "배치 실행 실패: " + e.getMessage();
        }
    }
}
