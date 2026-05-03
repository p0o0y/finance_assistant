package demo.senior_project.domain.transaction.repository;

import demo.senior_project.domain.transaction.domain.entity.CardTransaction;
import demo.senior_project.domain.user.domain.User;
import demo.senior_project.domain.user.domain.UserCard;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;


public interface CardTransactionRepository extends JpaRepository<CardTransaction,Long> {
    boolean existsByUserCardAndApprovedAtAndAmountAndStoreName(UserCard userCard, LocalDateTime approvedAt, BigDecimal amount, String storeName);

    // 중복내역 한꺼번에
    @Query("select t from CardTransaction t where t.userCard in :cards and t.approvedAt in :dates")
    List<CardTransaction> findByUserCardInAndApprovedAtIn(
            @Param("cards") List<UserCard> cards,
            @Param("dates") List<LocalDateTime> dates
    );

    List<CardTransaction>findByUserCard_UserAndApprovedAtBetween(User user, LocalDateTime start, LocalDateTime end);
}
