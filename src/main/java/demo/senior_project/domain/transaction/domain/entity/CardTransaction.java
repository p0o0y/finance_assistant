package demo.senior_project.domain.transaction.domain.entity;

import demo.senior_project.domain.user.CardCompany;
import demo.senior_project.domain.user.domain.UserCard;
import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Getter
@Builder
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
public class CardTransaction {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long transactionId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_card_id", nullable = false)
    private UserCard userCard; // 이 거래에 사용한 카드

    @Column(nullable = false, precision = 10, scale = 0)
    private BigDecimal amount; // 승인 금액

    @Column(nullable = false)
    private String storeName; // 가맹점명

    @Column(nullable = false)
    private String storeType; // 가맹점업종

    @Column(nullable = false)
    private LocalDateTime approvedAt; // 승인 일시
}
