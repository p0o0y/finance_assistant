package demo.senior_project.domain.transaction.serevice;

import demo.senior_project.domain.transaction.domain.entity.CardTransaction;
import demo.senior_project.domain.transaction.domain.entity.MerchantCategory;
import demo.senior_project.domain.transaction.repository.CardTransactionJdbcRepository;
import demo.senior_project.domain.transaction.repository.MerchantCategoryJdbcRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
public class TransactionsSaveService {
    private final MerchantCategoryJdbcRepository merchantCategoryJdbcRepository;
    private final CardTransactionJdbcRepository cardTransactionJdbcRepository;

    @Transactional
    public void saveAll(List<MerchantCategory> merchants, List<CardTransaction> transactions) {
        if (!merchants.isEmpty()) {
            merchantCategoryJdbcRepository.batchUpdate(merchants);
        }
        cardTransactionJdbcRepository.batchUpdate(transactions);
    }
}