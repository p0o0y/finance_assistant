package demo.senior_project;

import org.springframework.ai.model.ollama.autoconfigure.OllamaEmbeddingAutoConfiguration;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication(exclude = {
        OllamaEmbeddingAutoConfiguration.class // Ollama 임베딩 자동 설정 제외
})
public class SeniorProjectApplication {

    public static void main(String[] args) {
        SpringApplication.run(SeniorProjectApplication.class, args);
    }

}
