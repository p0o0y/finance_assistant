package demo.senior_project.external.webclient;

import io.codef.api.EasyCodef;
import io.codef.api.EasyCodefUtil;
import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
public class RSA {
    private final EasyCodef easyCodef;
    private final EasyCodefUtil easyCodefUtil;

    public static void main(String[] args) {
        // 1. 도구 준비
        EasyCodefUtil easyCodefUtil = new EasyCodefUtil();

        // 2. 공개키와 비번 (예시)
        String myPassword = "wpffltkfkd12!";
        String publicKey = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAt9LLA60vLIv4s9PT9KO7aZ3FP2FVp4PcdDo1CnkWs5irEQMuvqanmrFPTck5OJ7XhoFt6YfXj8Caa8Y/vwP37jtyCnY38SN1m1jtGSQOInVrNP1gR9FA/JgqwnC3zNVsWJk0Lmtlf0t9eR4gjXWOblic4tea/C/udsCdFyVrAnCQW9IYr0uONhNlSg1p1NtR7tLlvT1JnQm3u9B2vwfVeiXlTkxkhjXeDVw4HckVf6ULZvVY5nNoAExN8tqIqZqpUWYBZ4wFcJwMOwKsxDuek84+OOaHmuakPygp5jENKUS86GLgO2t2Vxzrmt44vq73ZOsQBmwwck/w/bpM9nbRswIDAQAB";

        try {
            // 3. 암호화 실행
            String encryptedPassword = easyCodefUtil.encryptRSA(myPassword, publicKey);

            System.out.println("--- 암호화 성공! 아래 값을 복사하세요 ---");
            System.out.println(encryptedPassword);
            System.out.println("---------------------------------------");

        } catch (Exception e) {
            System.err.println("암호화 중 에러 발생!");
            e.printStackTrace();
        }
    }
}
