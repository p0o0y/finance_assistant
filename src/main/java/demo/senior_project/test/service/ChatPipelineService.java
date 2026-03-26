package demo.senior_project.test.service;

import demo.senior_project.test.dto.RewrittenQueryDto;
import demo.senior_project.test.dto.RouterDecisionDto;
import demo.senior_project.external.openai.OpenAIService;
import demo.senior_project.test.service.sql.sqlGuardService;
import demo.senior_project.test.service.router.LlmRouterService;
import demo.senior_project.test.service.sql.DbQueryService;
import demo.senior_project.test.service.sql.QueryRewriteService;
import demo.senior_project.test.service.sql.TextToSqlService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class ChatPipelineService {

    private final LlmRouterService routerService;
    private final QueryRewriteService queryRewriteService;
    private final TextToSqlService textToSqlService;
    private final DbQueryService dbQueryService;
    private final sqlGuardService sqlGuardService;
    private final OpenAIService openAIService;

    public String process(String question) {
     // 질문 분류
        RouterDecisionDto decision = routerService.route(question);
        // SQL 경로일 경우
        if (decision.getQueryType() == RouterDecisionDto.QueryType.SQL) {
            return handleSqlFlow(question);
        }
        // RAG 경로일 경우 (현재는 메시지만 반환, 나중에 RAG 서비스 연결)
        return "RAG 모듈은 현재 준비 중입니다. SQL 기반 조회만 가능합니다.";
    }

    private String handleSqlFlow(String question) {
        log.info("=== [Step 2] Rewrite: 질문 정제 및 조건 추출 ===");
        RewrittenQueryDto rewritten = queryRewriteService.rewrite(question);
        log.info("=== [Step 3] Text-to-SQL: SQL 생성 ===");
        String generatedSql = textToSqlService.generateSql(rewritten);
        log.info("=== [Step 4] SQL Guard: 보안 검증 ===");
        // 여기서 예외(SqlSecurityException)가 발생하면 GlobalExceptionHandler로 날아감
        sqlGuardService.validate(generatedSql);
        log.info("=== [Step 5] DB Query: 데이터 조회 ===");
        List<Map<String, Object>> rows = dbQueryService.execute(generatedSql);
        String jsonContext = dbQueryService.formatResults(rows);

        log.info("=== [Step 6] Final Answer: 자연어 답변 생성 ===");
        return generateFinalAnswer(question, jsonContext);
    }

    private String generateFinalAnswer(String question, String context) {
        String systemPrompt = """
                당신은 친절한 금융 비서입니다. 제공된 [데이터]를 참고하여 사용자의 질문에 답변하세요.
                - 데이터가 비어있다면 "해당하는 내역을 찾을 수 없어요"라고 답변하세요.
                - 숫자는 가독성 좋게 콤마를 찍어 표현하세요 (예: 10,000원).
                """;

        String userMessage = String.format("질문: %s\n\n[데이터]\n%s", question, context);

        return openAIService.complete(systemPrompt, userMessage);
    }
    // RAG 경로 생략 (비슷한 구조로 추상화 가능)
}