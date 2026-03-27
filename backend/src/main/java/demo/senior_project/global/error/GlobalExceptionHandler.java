package demo.senior_project.global.error;

import demo.senior_project.global.response.ApiResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.validation.BindingResult;
import org.springframework.web.HttpRequestMethodNotSupportedException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.nio.file.AccessDeniedException;
import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {
    // 1. businessException 처리
    @ExceptionHandler(BusinessException.class)
    protected ResponseEntity<ApiResponse<?>> handleBusinessException(BusinessException e) {
        log.warn("BusinessException: {}", e.getMessage(), e);
        ErrorCode errorCode = e.getErrorCode();
        // ErrorResponse 없이 ApiResponse를 직접 생성
        ApiResponse<?> apiResponse = ApiResponse.error(errorCode);
        return new ResponseEntity<>(apiResponse, errorCode.getHttpStatus());
    }

    // 2. @Valid 유효성 검사 실패 처리
    @ExceptionHandler(MethodArgumentNotValidException.class)
    protected ResponseEntity<ApiResponse<?>> handleMethodArgumentNotValidException(MethodArgumentNotValidException e) {
        log.warn("MethodArgumentNotValidException: {}", e.getMessage());

        ErrorCode errorCode = ErrorCode.INVALID_INPUT_VALUE;
        BindingResult bindingResult = e.getBindingResult();

        // ErrorResponse.FieldError -> ApiResponse.FieldError 로 변경
        List<ApiResponse.FieldError> fieldErrors = bindingResult.getFieldErrors().stream()
                .map(fieldError -> new ApiResponse.FieldError(
                        fieldError.getField(),
                        fieldError.getRejectedValue() == null ? "" : fieldError.getRejectedValue().toString(),
                        fieldError.getDefaultMessage()
                ))
                .collect(Collectors.toList());

        // fieldErrors를 포함하는 ApiResponse.error() 오버로딩 메소드 사용
        ApiResponse<?> apiResponse = ApiResponse.error(errorCode, fieldErrors);
        return new ResponseEntity<>(apiResponse, errorCode.getHttpStatus());
    }


    // 4. 403 (권한) 에러 처리 (Spring Security)
    @ExceptionHandler(AccessDeniedException.class)
    protected ResponseEntity<ApiResponse<?>> handleAccessDeniedException(AccessDeniedException e) {
        log.warn("AccessDeniedException: {}", e.getMessage());
        ErrorCode errorCode = ErrorCode.ACCESS_DENIED;

        ApiResponse<?> apiResponse = ApiResponse.error(errorCode);
        return new ResponseEntity<>(apiResponse, errorCode.getHttpStatus());
    }

    // 5. 405 (HTTP Method) 에러 처리
    @ExceptionHandler(HttpRequestMethodNotSupportedException.class)
    protected ResponseEntity<ApiResponse<?>> handleHttpRequestMethodNotSupported(HttpRequestMethodNotSupportedException e) {
        log.warn("HttpRequestMethodNotSupportedException: {}", e.getMessage());
        ErrorCode errorCode = ErrorCode.METHOD_NOT_ALLOWED;

        ApiResponse<?> apiResponse = ApiResponse.error(errorCode);
        return new ResponseEntity<>(apiResponse, errorCode.getHttpStatus());
    }

    // 6. 400 (JSON 형식) 에러 처리
    @ExceptionHandler(HttpMessageNotReadableException.class)
    protected ResponseEntity<ApiResponse<?>> handleHttpMessageNotReadable(HttpMessageNotReadableException e) {
        log.warn("HttpMessageNotReadableException: {}", e.getMessage());
        ErrorCode errorCode = ErrorCode.INVALID_JSON;

        ApiResponse<?> apiResponse = ApiResponse.error(errorCode);
        return new ResponseEntity<>(apiResponse, errorCode.getHttpStatus());
    }

    // 7. 그 외 모든 예외 처리 (최후의 보루)
    @ExceptionHandler(Exception.class)
    protected ResponseEntity<ApiResponse<?>> handleException(Exception e) {
        // 중요: 예측하지 못한 예외는 Error 레벨로 로그.
        log.error("UnhandledException: {}", e.getMessage(), e);
        ErrorCode errorCode = ErrorCode.INTERNAL_SERVER_ERROR;

        ApiResponse<?> apiResponse = ApiResponse.error(errorCode);
        return new ResponseEntity<>(apiResponse, errorCode.getHttpStatus());
    }
}
