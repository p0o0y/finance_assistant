package demo.senior_project.test.domain.transaction;


import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.time.LocalTime;

@Entity
@NoArgsConstructor
@Getter
@Table(name = "transactions")
public class Transaction {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    //날짜와 시간
    @Column(name = "tran_date")
    private LocalDate tranDate; // resAccountTrDate (20160125->2016-01-25)

    @Column(name = "tran_time")
    private LocalTime tranTime; // resAccountTrTime (004219 -> 00:42:19)

    // 2. 금액
    @Column(name = "out_amount")
    private Integer outAmount; // resAccountOut (소비액)

    @Column(name = "in_amount")
    private Integer inAmount;  // resAccountIn (수입액)

    // 3. 위치 (어디서 썼는지)
    @Column(name = "content")
    private String content;    // resAccountDesc2 (예: 스타벅스, 이자원가)

    // 4. 카테고리 (AI가 '식비', '문화비' 통계 낼 때 사용)
    @Column(name = "category")
    private String category;   // 초기엔 null, 나중에 AI가 분류해서 채워넣음

    // 5. 계좌 정보 (여러 계좌일 경우 대비)
    @Column(name = "account_display")
    private String accountDisplay; // resAccountDisplay (020-0413-...)

    // 생성자나 빌더는 생략 (필요에 따라 추가)
}
