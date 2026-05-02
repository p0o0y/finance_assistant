package demo.senior_project.domain.report.dto;

import demo.senior_project.domain.user.domain.User;
import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public class UserYearMonth {
    private User user;
    private String yearMonth;
}
