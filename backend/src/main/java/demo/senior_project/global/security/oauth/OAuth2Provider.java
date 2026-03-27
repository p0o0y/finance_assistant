package demo.senior_project.global.security.oauth;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

@Getter
@RequiredArgsConstructor
public enum OAuth2Provider {
    NAVER("NAVER"),
    KAKAO("KAKAO");

    private final String provider;
}
