package demo.senior_project.domain.report;

import demo.senior_project.domain.user.domain.User;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Entity
@Getter
@NoArgsConstructor
@AllArgsConstructor
@Builder
@Table(name = "consumption_report",
    indexes = @Index(name="idx_user_year_month",
            columnList = "user_id,year_month"))
public class ConsumptionReport {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name="user_id",nullable = false) // fk 정의
    private User user;

    @Column(nullable = false)
    private String yearMonth;

    @Column(nullable = false)
    private Long totalAmount;

    @Column(columnDefinition = "TEXT")
    private String categoryStats;  // JSON {"카페": 150000, "교통": 80000}

    @Column(columnDefinition = "TEXT")
    private String topStores;  // JSON [{"name":"스타벅스","count":12}]

    @Column(columnDefinition = "TEXT")
    private String reportText;

    @Column(nullable = false)
    private LocalDateTime createdAt;

    public void update(String reportText,String categoryStats,String topStores, Long totalAmount){
        this.reportText=reportText;
        this.categoryStats=categoryStats;
        this.topStores=topStores;
        this.totalAmount=totalAmount;
    }
}
