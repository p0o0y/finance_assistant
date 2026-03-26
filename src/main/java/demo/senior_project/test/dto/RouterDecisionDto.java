package demo.senior_project.test.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RouterDecisionDto {
    private QueryType queryType;
    public enum QueryType{
        SQL,
        RAG
    }
}
