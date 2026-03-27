package demo.senior_project.domain.transaction.repository;
import demo.senior_project.domain.transaction.domain.entity.CardTransaction;
import demo.senior_project.domain.transaction.domain.entity.MerchantCategory;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
@RequiredArgsConstructor
public class MerchantCategoryJdbcRepository {
    private final JdbcTemplate jdbcTemplate;

    public void batchUpdate(List<MerchantCategory> merchantCategories){
        String sql = "insert  into merchant_category (biz_no , store_name , category) values (?,?,?)";
        jdbcTemplate.batchUpdate(sql, merchantCategories, 50, (ps, tx) -> {
            ps.setString(1, tx.getBizNo());
            ps.setString(2, tx.getStoreName());
            ps.setString(3, tx.getCategory());
        });
    }
}