package demo.senior_project.external.codef.dto;

import demo.senior_project.domain.user.domain.UserCard;
import demo.senior_project.external.codef.dto.response.TransactionListResponse;
import lombok.AllArgsConstructor;
import lombok.Getter;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Getter
@AllArgsConstructor
public class ParsedTransaction {
    private final TransactionListResponse.TransactionInfo info;
    private final UserCard card;
    private final LocalDateTime transactionDateTime;
    private final BigDecimal amount;
}