package demo.senior_project.test.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
@AllArgsConstructor
public class RewrittenQueryDto {
    private String original;          // 원본 질문: 지난주 스벅 얼마?
    private String normalizedMerchant; // 정규화된 상호명: 스타벅스
    private String category;           // 카테고리: 카페
    private String startDate;          // 시작일: 2026-03-01
    private String endDate;            // 종료일: 2026-03-07
    private String intent;             // 의도:  sum 같은
}
