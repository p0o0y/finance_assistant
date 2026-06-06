package demo.senior_project.global.security.oauth;


import demo.senior_project.global.security.jwt.JwtTokenProvider;
import demo.senior_project.global.security.util.CookieUtil;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseCookie;
import org.springframework.security.core.Authentication;
import org.springframework.security.web.authentication.SimpleUrlAuthenticationSuccessHandler;
import org.springframework.stereotype.Component;

import java.io.IOException;

@Component
@RequiredArgsConstructor
public class OAuthSuccessHandler extends SimpleUrlAuthenticationSuccessHandler {
    private final JwtTokenProvider jwtTokenProvider;
    private final CookieUtil cookieUtil;

    @Value("${oauth.redirect-url}")
    private String redirectUrl;

    @Override
    public void onAuthenticationSuccess(HttpServletRequest request, HttpServletResponse response, Authentication authentication) throws IOException, ServletException {
        CustomOauth2User user = (CustomOauth2User) authentication.getPrincipal();

        //jwt 생성
        String accessToken = jwtTokenProvider.createAccessToken(user.getUser().getUserId());

        //쿠키 저장
        ResponseCookie cookie = cookieUtil.createAccessTokenCookie(accessToken,60*60);
        response.addHeader(HttpHeaders.SET_COOKIE,cookie.toString());

        response.sendRedirect(redirectUrl+accessToken);
    }
}
