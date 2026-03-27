package demo.senior_project.external.webclient;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;

@Configuration
public class WebClientConfig {
    @Value("${spring.ai.openai.api-key}")
    private String openaiApiKey;

    @Value("${spring.ai.ollama.base-url}")
    private String ollmaUrl;

    @Bean("openaiWebClient")
    public WebClient openaiWebClient(){
        return WebClient.builder()
                .baseUrl("https://api.openai.com/v1")
                .defaultHeader("Authorization", "Bearer " + openaiApiKey)
                .defaultHeader("Content-Type", "application/json")
                .build();
    }

//    spring.ai.mcp.server.protocol=streamable
//    spring.ai.ollama.base-url=http://localhost:11434
//    spring.ai.ollama.chat.options.model=qwen2.5:1.5b
//    spring.ai.ollama.chat.options.temperature=0.0
    @Bean("ollamaWebClient")
    public WebClient ollamaWebClient(){
        return WebClient.builder()
                .baseUrl(ollmaUrl)
                .defaultHeader("Content-Type", "application/json")
                .build();
    }
}
