package demo.senior_project.external.codef.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.List;

@Getter
@NoArgsConstructor
public class CardListResponse {
    private List<Data> data;
    private Result result;

    @Getter
    @NoArgsConstructor
    public static class Data{
        @JsonProperty("resCardNo")
        private String cardNo;

        @JsonProperty("resSleepYN")
        private String sleepYN; //휴면 여부

        @JsonProperty("resCardName")
        private String CardName;

        @JsonProperty("resCardType")
        private String cardType;

        @JsonProperty("resTrafficYN")
        private String trafficYN;

        @JsonProperty("resImageLink")
        private String imageLink;

        @JsonProperty("resState")
        private String resState;

    }

    @Getter
    @NoArgsConstructor
    public static class Result{
        private String code;
        private String message;
    }

    public boolean isSuccess(){
        return "CF-00000".equals(this.result.getCode());
    }
}
