package demo.senior_project.domain.transaction.domain.entity;

import demo.senior_project.domain.user.CardCompany;
import jakarta.persistence.*;
import lombok.*;

@Entity
@Getter
@Builder
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
public class Card {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "card_id")
    private Long cardId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private CardCompany cardCompany; // 카드사 (Enum 타입)

    @Column(nullable = false)
    private String cardName;

}
