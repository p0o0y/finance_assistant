package demo.senior_project.domain.user.repository;

import demo.senior_project.domain.user.domain.User;
import demo.senior_project.global.security.oauth.OAuth2Provider;
import jakarta.persistence.criteria.CriteriaBuilder;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface UserRepository extends JpaRepository<User, Integer> {
    Optional<User> findByOauthIdAndOauthProvider(String oauthId, OAuth2Provider oauthProvider);
    Optional<User> findByUserId(int userId);
}
