package demo.senior_project.test.repository;

import demo.senior_project.test.domain.transaction.Transaction;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface TransactionRepository  extends JpaRepository<Transaction,Long> {
    // 카테고리가 비어있는 내역
    List<Transaction> findByCategoryIsNull();
}
