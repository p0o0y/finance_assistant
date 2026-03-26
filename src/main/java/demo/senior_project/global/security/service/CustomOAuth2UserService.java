package demo.senior_project.global.security.service;

import demo.senior_project.domain.user.domain.User;
import demo.senior_project.domain.user.repository.UserRepository;
import demo.senior_project.global.security.oauth.CustomOauth2User;
import demo.senior_project.global.security.oauth.OAuth2Attribute;
import lombok.*;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.oauth2.client.userinfo.DefaultOAuth2UserService;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserRequest;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/*유저 저장 , 조회 -> CustomOauth 생성*/
@Service
@RequiredArgsConstructor
@Slf4j
public class CustomOAuth2UserService extends DefaultOAuth2UserService {
    private final UserRepository userRepository;

    @Override
    @Transactional
    public OAuth2User loadUser(OAuth2UserRequest userRequest) throws OAuth2AuthenticationException {
        OAuth2User oAuth2User = super.loadUser(userRequest);

        String registrationId = userRequest.getClientRegistration().getRegistrationId();
        OAuth2Attribute attributes = OAuth2Attribute.from(registrationId,oAuth2User.getAttributes());

        User user = findUser(attributes);

        return new CustomOauth2User(user,oAuth2User.getAttributes());
    }

    private User findUser(OAuth2Attribute attribute){
        return userRepository.findByOauthIdAndOauthProvider(
                attribute.getOauthId(),
                attribute.getOAuth2Provider())
                .orElseGet(() ->{
                    User newUser = attribute.createEntity();
                    return userRepository.save(newUser);
        });
    }
}
