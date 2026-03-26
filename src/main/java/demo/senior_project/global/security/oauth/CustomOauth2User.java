package demo.senior_project.global.security.oauth;

import demo.senior_project.domain.user.domain.User;
import lombok.Getter;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.oauth2.core.user.OAuth2User;

import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.Map;

/*oauth -> customoauth */
@Getter
@RequiredArgsConstructor
public class CustomOauth2User implements OAuth2User {
    private final User user;
    private final Map<String,Object> attributes;

    public Long getUserId() {
        return user.getUserId();
    }

    @Override
    public Map<String, Object> getAttributes() {
        return this.attributes;
    }

    @Override
    public String getName() {
        return String.valueOf(user.getUserId());
    }

    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        return Collections.emptyList();
    }
}
