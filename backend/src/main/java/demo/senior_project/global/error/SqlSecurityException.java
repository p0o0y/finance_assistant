package demo.senior_project.global.error;

public class SqlSecurityException extends BusinessException {
  public SqlSecurityException(String message) {
    super(message, ErrorCode.SQL_SECURITY_VIOLATION);
  }
}
