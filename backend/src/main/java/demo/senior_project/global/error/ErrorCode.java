package demo.senior_project.global.error;

import lombok.Getter;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;

@Getter
@RequiredArgsConstructor
public enum ErrorCode {
    //1. @valid 유효성 검사 실패
    INVALID_INPUT_VALUE(HttpStatus.BAD_REQUEST, "C001", "Invalid input value"),
    // 2. HTTP 메소드가 잘못되었을 때
    METHOD_NOT_ALLOWED(HttpStatus.METHOD_NOT_ALLOWED, "C002", "HTTP method not allowed"),
    // 3. Request body의 JSON 형식이 잘못되었을 때
    INVALID_JSON(HttpStatus.BAD_REQUEST, "C003", "Malformed JSON in request body"),
    // 4. NOT Authenticated
    AUTHENTICATION_REQUIRED(HttpStatus.UNAUTHORIZED, "C005", "Authentication is required"),
    // 5. NOT Authorized (e.g., 남의 글 수정)
    ACCESS_DENIED(HttpStatus.FORBIDDEN, "C006", "You do not have permission to perform this action"),
    // 6. 요청한 리소스가 존재하지 않을 때
    RESOURCE_NOT_FOUND(HttpStatus.NOT_FOUND, "C008", "Resource not found"),
    // 7. 위 모든 것에 해당하지 않는, 예상치 못한 서버 내부 에러
    INTERNAL_SERVER_ERROR(HttpStatus.INTERNAL_SERVER_ERROR, "C010", "An unexpected server error occurred"),

    // ErrorCode.java 에 추가
    SQL_SECURITY_VIOLATION(HttpStatus.FORBIDDEN, "S001", "보안 정책에 위배되는 쿼리가 감지되었습니다."),
    SQL_GENERATION_FAILED(HttpStatus.INTERNAL_SERVER_ERROR, "S002", "SQL 문장 생성 중 오류가 발생했습니다."),
    APP_USER_NOT_FOUNDUSER_NOT_FOUNT(HttpStatus.NOT_FOUND,"U000","존재하지 않는 사용자 입니다"),
    // codef 관련
    USER_NOT_FOUNT(HttpStatus.NOT_FOUND,"U001","codef connecteID 미등록 사용자입니다"),
    CODEF_API_CONNECTEDID_ERROR(HttpStatus.BAD_REQUEST,"C001","비밀번호 암호화 실패"),
    CODEF_API_CARD_ERROR(HttpStatus.BAD_REQUEST,"CD002","카드 관련 CODEF API 연결 실패"),
    CARD_NOT_FOUND(HttpStatus.BAD_REQUEST,"CD001","카드를 찾을 수 없습니다"),

    CATEGORY_LLM_FAIL(HttpStatus.INTERNAL_SERVER_ERROR, "L001", "llm 카테고리 파싱 실패 "),
    CATEGORY_LLM_FAIL2(HttpStatus.INTERNAL_SERVER_ERROR, "L002", "llm 카테고리 파싱 시간 초과");
    private final HttpStatus httpStatus;
    private final String errorCode;
    private final String errorMessage;
}
