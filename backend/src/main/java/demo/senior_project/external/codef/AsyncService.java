package demo.senior_project.external.codef;

import demo.senior_project.domain.transaction.repository.MerchantCategoryRepository;
import demo.senior_project.external.openai.OpenAIService;
import lombok.RequiredArgsConstructor;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import demo.senior_project.domain.transaction.repository.MerchantCategoryRepository;
import demo.senior_project.external.openai.OpenAIService;

import java.util.concurrent.CompletableFuture;


@Service
@RequiredArgsConstructor
public class AsyncService {
    private final OpenAIService openAIService;

    public CompletableFuture<String> classifyAsync(String storeName, String bizNo, String storeType) {
        return openAIService.classifyTransaction(storeName, bizNo, storeType).toFuture();
    }
}
