package demo.senior_project.domain.transaction.repository;

import demo.senior_project.domain.transaction.domain.entity.CardTransaction;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.sql.Timestamp;
import java.util.List;

@Repository
@RequiredArgsConstructor
public class CardTransactionJdbcRepository {
    private final JdbcTemplate jdbcTemplate;

    public void batchUpdate(List<CardTransaction> transactions){
        String sql = "INSERT INTO card_transaction (amount, approved_at, store_name, store_type, user_card_id) VALUES (?, ?, ?, ?, ?)";
        jdbcTemplate.batchUpdate(sql, transactions, 100, (ps, tx) -> {
            ps.setBigDecimal(1, tx.getAmount());
            ps.setTimestamp(2, Timestamp.valueOf(tx.getApprovedAt()));
            ps.setString(3, tx.getStoreName());
            ps.setString(4, tx.getStoreType());
            ps.setLong(5, tx.getUserCard().getUserCardId());
        });
    }
}
