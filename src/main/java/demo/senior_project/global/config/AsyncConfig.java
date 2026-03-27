package demo.senior_project.global.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

import java.util.concurrent.Executor;

@Configuration
@EnableAsync
public class AsyncConfig {
    @Bean("llmTaskExecutor")
    public Executor llmTaskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(10);      // 최소 상주
        executor.setMaxPoolSize(30); // 스레드 최대치
        executor.setQueueCapacity(100); // 다 차면 MaxPool 도 적용
        executor.setThreadNamePrefix("llm-");
        executor.initialize();
        return executor;
    }

    @Bean("codefTaskExecutor")
    public Executor codefTaskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(5);    // 카드사 수 상한
        executor.setMaxPoolSize(10);
        executor.setQueueCapacity(20);
        executor.setThreadNamePrefix("codef-");
        executor.initialize();
        return executor;
    }
}
