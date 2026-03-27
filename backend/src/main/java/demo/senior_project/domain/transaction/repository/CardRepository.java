package demo.senior_project.domain.transaction.repository;

import demo.senior_project.domain.transaction.domain.entity.Card;
import demo.senior_project.domain.user.CardCompany;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface CardRepository extends JpaRepository<Card,Long> {
    //현재 등록 카드 조회
    Optional<Card> findByCardCompanyAndCardName(CardCompany cardCompany,String name);
    Optional<Card> findByCardName(String name);
}
