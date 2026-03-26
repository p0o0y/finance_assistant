package demo.senior_project.test.service.sql;

import demo.senior_project.test.dto.RewrittenQueryDto;
import demo.senior_project.external.openai.OpenAIService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

// 순수 sql 추출
@Service
@Slf4j
@RequiredArgsConstructor
public class TextToSqlService {
    private final OpenAIService openAiService;

    public String generateSql(RewrittenQueryDto query) {
        // AI가 SQL을 더 잘 짜도록 'Few-shot'(예시)을 포함한 프롬프트 구성
        String systemPrompt = String.format("""
            너는 PostgreSQL 전문가야. 아래 조건을 만족하는 SELECT SQL 하나만 생성해.
            - 테이블: transactions (tran_date, out_amount, in_amount, content, category)
            - 기간: %s ~ %s
            - 상호명: %s (content ILIKE '%%값%%' 사용)
            - 의도: %s (SUM이면 합계조회, LIST면 전체조회)
            
            [주의] 마크다운 코드블록 없이 순수 SQL만 출력할 것.
            """, query.getStartDate(), query.getEndDate(), query.getNormalizedMerchant(), query.getIntent());

        String rawSql = openAiService.complete(systemPrompt, query.getOriginal());

        // 기술적 포인트: LLM이 보낸 문자열에서 SQL만 깔끔하게 도려냄
        return extractSql(rawSql);
    }

    private String extractSql(String text) {
        if (text == null) return "";
        return text.replaceAll("(?s).*?```sql\\s*(.*?)\\s*```.*", "$1") // ```sql 내역 추출
                .replaceAll("(?s).*?```\\s*(.*?)\\s*```.*", "$1")    // ``` 내역 추출
                .replaceAll(";", "")                                 // 세미콜론 일단 제거 (Guard에서 처리)
                .trim();
    }
}
