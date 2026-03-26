package demo.senior_project.domain.transaction.domain;

import reactor.netty.transport.Transport;

import java.util.Arrays;
import java.util.List;

public enum CategoryGroup {
    CAFE("카페,간식", List.of("커피", "제과", "아이스크림", "디저트","스타벅스","투썸","이디야")),
    HOSPITAL("병원", List.of("치과", "한방병원", "병원", "의원", "약국")),
    MART("마트", List.of("마트", "편의점", "슈퍼", "유통","CU","GS25","세븐일레븐")),
    FOOD("음식점", List.of("패스트푸드", "휴게음식점", "식당", "한식", "중식", "일식", "양식", "분식")),
    SHOPPING("쇼핑", List.of("쇼핑", "전자상거래", "백화점", "아울렛","무신사","에이블리")),
    TRANSPORT("교통", List.of("교통", "택시", "버스", "철도", "주유")),
    EDUCATION("교육", List.of("학원", "학교", "독서실")),
    BEAUTY("미용", List.of("미용실", "헤어", "네일")),
    HOUSING("주거통신", List.of("통신", "관리비", "전기", "수도","가스")),
    HOBBY("취미,여가",List.of("놀이동산","오락","게임","웹툰"));
    private final String categoryName;
    private final List<String> keywords;

    CategoryGroup(String categoryName, List<String> keywords) {
        this.categoryName = categoryName;
        this.keywords = keywords;
    }

    public static String classify(String storeType , String storeName){
        if(storeName==null) storeName ="";
        if(storeType==null) storeType ="";

        String finalType = storeType;
        String finalName = storeName;

        return Arrays.stream(CategoryGroup.values())
                .filter(categoryGroup -> categoryGroup.keywords.stream().anyMatch(
                        keyword->finalType.contains(keyword) || finalName.contains(keyword)))
                .map(group->group.categoryName)
                .findFirst()
                .orElse(null); // 매칭되는게 없으면 DB나 LLM 전달
    }
}
