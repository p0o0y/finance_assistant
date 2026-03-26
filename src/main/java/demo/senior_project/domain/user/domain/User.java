package demo.senior_project.domain.user.domain;


import demo.senior_project.domain.user.CardCompany;
import demo.senior_project.global.security.oauth.OAuth2Provider;
import jakarta.persistence.*;
import jakarta.persistence.criteria.CriteriaBuilder;
import lombok.*;

import java.util.*;
import java.util.stream.Collectors;

@Entity
@Table(name="users")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
@Builder
public class User {
    @Id
    @GeneratedValue(strategy=GenerationType.IDENTITY)
    @Column(name="user_id")
    private Long userId;

    @Column(unique = true ,nullable = false)
    private String oauthId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private OAuth2Provider oauthProvider;

    @Column(nullable = false)
    private String nickname;

    @Column //codef connected id
    private String connectedId;


    @Column(name = "connected_company")
    private String connectedCompany; // CODEF에 연결된 카드사 목록  "0301,0303"

    // User 1 : 카드 여러장
    @Builder.Default // lombok builder 쓸 때 초기화한 코드가 무시되지 않게 null에러 방지
    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<UserCard> userCards = new ArrayList<>();

    public List<CardCompany> getConnectedCompanyList() {
        if (connectedCompany == null || connectedCompany.isEmpty())
            return new ArrayList<>();

        return Arrays.stream(connectedCompany.split(","))
                .map(code -> Arrays.stream(CardCompany.values())
                        .filter(c -> c.getCode().equals(code))
                        .findFirst().orElse(null))
                .filter(Objects::nonNull)
                .collect(Collectors.toList());
    }

    //새로운 카드 등록 - 중복 방지 , 추가
    public void addConnectedCompany(CardCompany company) {
        Set<String> codes = (connectedCompany == null || connectedCompany.isEmpty())
                ? new HashSet<>()
                : new HashSet<>(Arrays.asList(connectedCompany.split(",")));

        if (!codes.contains(company.getCode())) {
            codes.add(company.getCode());
            connectedCompany = String.join(",", codes);
        }
    }

    public void updateConnectedId(String connectedId) {
        this.connectedId = connectedId;
    }


}
