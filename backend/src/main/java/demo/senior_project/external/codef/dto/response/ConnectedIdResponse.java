package demo.senior_project.external.codef.dto.response;

import lombok.Getter;
import lombok.NoArgsConstructor;
import org.antlr.v4.runtime.atn.ErrorInfo;

import java.util.List;

@Getter
@NoArgsConstructor
public class ConnectedIdResponse {
    private Data data;

    @Getter
    @NoArgsConstructor
    public static class Data{
        private String connectedId;
        private List<ResultInfo> successList;
        private List<ResultInfo> errorList;
    }

    @Getter
    @NoArgsConstructor
    public static class ResultInfo{
        private String code;
        private String message;
        private String countryCode;
        private String clientType;
        private String organization;
        private String businessType;
        private String loginType;
    }
}
