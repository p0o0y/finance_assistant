package demo.senior_project.domain.user;


import lombok.Getter;
import lombok.RequiredArgsConstructor;

import javax.smartcardio.Card;
import java.util.Arrays;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

@Getter
@RequiredArgsConstructor
public enum CardCompany {
    KB("0301", "국민카드"),
    HYUNDAI("0302", "현대카드"),
    SAMSUNG("0303", "삼성카드"),
    NH("0304", "NH농협카드"),
    BC("0305", "BC카드"),
    SHINHAN("0306", "신한카드"),
    WOORI("0309", "우리카드"),
    LOTTE("0311", "롯데카드"),
    HANA("0313", "하나카드");

    private final String code;
    private final String description;

    private static final Map<String, CardCompany> CODE_MAP =
            Arrays.stream(values()).collect(Collectors.toMap(CardCompany::getCode,c->c));

    //description -> enum
    public static CardCompany findCardByDescription(String description) {
        //values -> [KB, HYUNDAI, SAMSUNG, ...]]
        return Arrays.stream(values())
                .filter(company -> company.getDescription().equals(description))
                .findFirst()
                .orElse(null);
    }

    public static CardCompany findByCode(String code) {
        if (code == null) return null;
        return CODE_MAP.get(code);
    }
}