package demo.senior_project.domain.user.domain;


import demo.senior_project.domain.transaction.domain.entity.Card;
import jakarta.persistence.*;
import lombok.*;



@Entity
@Getter
@Builder
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
// 한 사람이 동일 카드를 중복해서 등록 x
@Table(name = "user_card", uniqueConstraints = {
        @UniqueConstraint(
                name = "user_card_unique",
                columnNames = {"user_id", "card_id"}
        )
})
public class UserCard {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "user_card_id")
    private Long userCardId;

    // UserCard(N) : User(1)
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    // UserCard(N) : Card(1)
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "card_id", nullable = false)
    private Card card;

    @Column(name = "last4_digit", length = 4)
    private String lastFourDigits;

    // 승인내역 조회에 사용
    @Column(nullable = false)
    private String codefCardNo;

    @Column
    private boolean isMain;

    @Column(name = "card_company_code", nullable = false)  // 추가
    private String cardCompanyCode;
}
