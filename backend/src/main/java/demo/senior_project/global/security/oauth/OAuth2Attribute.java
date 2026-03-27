package demo.senior_project.global.security.oauth;

import demo.senior_project.domain.user.domain.User;
import lombok.Builder;
import lombok.Getter;

import java.util.Map;
import java.util.Objects;

/*원본 정보*/
@Getter
@Builder
public class OAuth2Attribute {
    private Map<String, Object> attributes;
    private OAuth2Provider oAuth2Provider;
    private String oauthId;
    private String nickname;

    private static OAuth2Attribute fromKaKao(Map<String,Object> attributes){
        Map<String, Object> kakaoAccount  = (Map<String, Object>) attributes.get("kakao_account");
        Map<String, Object> profile = (Map<String, Object>) kakaoAccount.get("profile");

        return OAuth2Attribute.builder()
                .oAuth2Provider(OAuth2Provider.KAKAO)
                .oauthId(String.valueOf(attributes.get("id")))
                .nickname((String) profile.get("nickname"))
                .attributes(attributes) // 원본 데이터 저장
                .build();
    }

    private static OAuth2Attribute fromNaver(Map<String,Object> attributes){
        Map<String, Object> response = (Map<String, Object>) attributes.get("response");
        return OAuth2Attribute.builder()
                .oAuth2Provider(OAuth2Provider.NAVER)
                .oauthId((String) response.get("id"))
                .nickname((String) response.get("nickname"))
                .attributes(attributes) // 원본 데이터 저장
                .build();
    }

    //첫 가입
    public User createEntity(){
        return User.builder()
                .oauthId(this.oauthId)
                .oauthProvider(this.oAuth2Provider)
                .nickname(this.nickname)
                .build();
    }

    public static OAuth2Attribute from(String registrationId, Map<String, Object> attributes) {
        if ("kakao".equalsIgnoreCase(registrationId)) {
            return fromKaKao(attributes);
        }
        else if("naver".equalsIgnoreCase(registrationId)) return fromNaver(attributes);

        throw  new IllegalStateException("존재 하지 않는 로그인 방식 입니다");
    }
}
