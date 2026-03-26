package demo.senior_project.test.service.sql;

import demo.senior_project.global.error.SqlSecurityException;
import org.springframework.stereotype.Service;

import java.util.regex.Pattern;

@Service
public class sqlGuardService {
    private static final Pattern DANGEROUS_PATTERN = Pattern.compile(
            "(?i)\\b(DROP|DELETE|UPDATE|INSERT|TRUNCATE|ALTER|CREATE|EXEC|GRANT|REVOKE)\\b|--|/\\*|;"
    );

    public void validate(String sql){
        String trimmedSql = sql.trim().toUpperCase();
        if(!trimmedSql.startsWith("SELECT")){
            throw new SqlSecurityException("SELECT 쿼리만 실행 가능합니다.");
        }
        // 위험 패턴 검사
        if (DANGEROUS_PATTERN.matcher(sql).find()) {
            throw new SqlSecurityException("비정상적인 SQL 키워드가 감지되었습니다.");
        }

        // 다중 쿼리 방지
        if (sql.contains(";") && !sql.trim().endsWith(";")) {
            throw new SqlSecurityException("다중 쿼리는 실행할 수 없습니다.");
        }
    }
}
