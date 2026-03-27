package demo.senior_project.domain.user.repository;

import demo.senior_project.domain.transaction.domain.entity.Card;
import demo.senior_project.domain.user.domain.User;
import demo.senior_project.domain.user.domain.UserCard;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface UserCardRepository extends JpaRepository<UserCard,Long> {

    Optional<UserCard> findByUserAndIsMainTrue(User user);

    Optional<UserCard> findByUserAndCard(User user, Card card);
}
