package demo.senior_project.global.response;


import com.fasterxml.jackson.annotation.JsonInclude;
import demo.senior_project.global.error.ErrorCode;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

import java.util.List;



@Getter
@Builder
@AllArgsConstructor(access = AccessLevel.PRIVATE)
@JsonInclude(JsonInclude.Include.NON_NULL)
public class ApiResponse<T> {
    private final boolean success;
    private final String code;
    private final String message;
    private final T data; // 성공 시에만 포함됨
    @Schema(hidden = true)
    private final List<FieldError> fieldErrors; // @Valid 유효성 검사 에러 시에만 포함됨

    // --- 성공 응답 ---
    // 1. [성공] data만 있는 경우 (code: S200, message: 기본 메시지)
    public static <T> ApiResponse<T> success(T data) {
        return new ApiResponse<>(true, "S200", "정상 처리되었습니다", data, null);
    }

    // 2. [성공] data와 커스텀 메시지가 있는 경우 (code: S200)
    public static <T> ApiResponse<T> success(T data, String message) {
        return new ApiResponse<>(true, "S200", message, data, null);
    }

    // 3. [성공] data와 커스텀 코드, 메시지가 있는 경우 (e.g., 글 생성 S201)
    public static <T> ApiResponse<T> success(T data, String code, String message) {
        return new ApiResponse<>(true, code, message, data, null);
    }

    // --- 실패 응답 ---

    // 4. [실패] ErrorCode만 사용하는 경우 (가장 일반적인 에러)
    public static <T> ApiResponse<T> error(ErrorCode errorCode) {
        return new ApiResponse<>(false, errorCode.getErrorCode(), errorCode.getErrorMessage(), null, null);
    }

    // 5. [실패] ErrorCode와 커스텀 메시지를 사용하는 경우 (e.g., 동적 메시지)
    public static <T> ApiResponse<T> error(ErrorCode errorCode, String message) {
        return new ApiResponse<>(false, errorCode.getErrorCode(), message, null, null);
    }

    // 6. [실패] @Valid 유효성 검사 에러인 경우 (fieldErrors 포함)
    public static <T> ApiResponse<T> error(ErrorCode errorCode, List<FieldError> fieldErrors) {
        return new ApiResponse<>(false, errorCode.getErrorCode(), errorCode.getErrorMessage(), null, fieldErrors);
    }

    @Getter
    @AllArgsConstructor
    public static class FieldError {
        private final String field;
        private final Object rejectedValue;
        private final String reason;
    }

}
