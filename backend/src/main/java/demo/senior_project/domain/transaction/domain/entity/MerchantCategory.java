package demo.senior_project.domain.transaction.domain.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Getter
@NoArgsConstructor
@AllArgsConstructor
@Builder
@Table(indexes = @Index(name ="inx_biz_no",columnList = "bizNo,storeName"))
public class MerchantCategory {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    Long id;
    private String bizNo;
    private String storeName;
    private String category;
}
