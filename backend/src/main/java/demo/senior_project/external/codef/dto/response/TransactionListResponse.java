package demo.senior_project.external.codef.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.List;

@Getter
@NoArgsConstructor
public class TransactionListResponse {
//    @JsonProperty("result")
    private Result result;
//    @JsonProperty("data")
    private List<TransactionInfo> data;

    @Getter
    @NoArgsConstructor
    public static class TransactionInfo {
        @JsonProperty("resMemberStoreName")
        private String storeName; // 가맹점명

        @JsonProperty("resUsedDate")
        private String date; // 사용한 날

        @JsonProperty("resUsedTime")
        private String time; // 승인시각

        @JsonProperty("resCardNo")
        private String resCardNo; //카드번호

        @JsonProperty("resUsedAmount")
        private String amount; // 사용금액

        @JsonProperty("resMemberStoreType")
        private String storeType; // 가맹점업종 * 우리카드 X

        @JsonProperty("resMemberStoreCorpNo")
        private String storeCorpNo; // 사업자 번호 -> 카테고리 분류

    }
    @Getter
    @NoArgsConstructor
    public static class Result{
        private String code;
        private String message;
        private String transactionId;
    }
    public List<TransactionInfo> getTransactionList() {
        return this.data;
    }

    public boolean isSuccess() {
        return "CF-00000".equals(this.result.getCode()) ? true :false;
    }
}
