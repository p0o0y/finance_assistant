package demo.senior_project.external.codef;

import demo.senior_project.domain.transaction.domain.CategoryGroup;
import demo.senior_project.domain.transaction.domain.entity.Card;
import demo.senior_project.domain.transaction.domain.entity.CardTransaction;
import demo.senior_project.domain.transaction.domain.entity.MerchantCategory;
import demo.senior_project.domain.transaction.repository.CardRepository;
import demo.senior_project.domain.transaction.repository.CardTransactionRepository;
import demo.senior_project.domain.transaction.repository.MerchantCategoryRepository;
import demo.senior_project.domain.user.CardCompany;
import demo.senior_project.domain.user.domain.User;
import demo.senior_project.domain.user.domain.UserCard;
import demo.senior_project.domain.user.repository.UserCardRepository;
import demo.senior_project.domain.user.repository.UserRepository;
import demo.senior_project.external.codef.dto.request.CreateConnectedIdRequestDto;
import demo.senior_project.external.codef.dto.response.CardListResponse;
import demo.senior_project.external.codef.dto.response.ConnectedIdResponse;
import demo.senior_project.external.codef.dto.response.TransactionListResponse;
import demo.senior_project.external.openai.OpenAIService;
import demo.senior_project.global.error.BusinessException;
import demo.senior_project.global.error.ErrorCode;
import demo.senior_project.global.response.ApiResponse;
import io.codef.api.EasyCodef;
import io.codef.api.EasyCodefServiceType;
import io.codef.api.EasyCodefUtil;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.servlet.LocaleResolver;
import tools.jackson.databind.ObjectMapper;

import java.awt.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional
public class CodefService {
    private final ObjectMapper objectMapper;
    private final EasyCodef easyCodef;
    private final EasyCodefUtil EasyCodefUtil;
    private final UserRepository userRepository;
    private final CardRepository cardRepository;
    private final UserCardRepository userCardRepository;
    private final CardTransactionRepository cardTransactionRepository;
    private final OpenAIService openAIService;
    private final MerchantCategoryRepository merchantCategoryRepository;


    private static final String CREATE_CONNECTED_ID_PATH = "/v1/account/create";
    private static final String CREATE_CONNECTED_ID_ADD_PATH = "/v1/account/add";
    private final LocaleResolver localeResolver;

    //connecteID 발급 , 계정 추가
    public String createConnectedAccount(Integer userId, CreateConnectedIdRequestDto requestDto ,String cardComponyCode) {
        User user = userRepository.findByUserId(userId).orElseThrow(() -> new BusinessException(ErrorCode.USER_NOT_FOUNT));

        List<HashMap<String, Object>> accountList = new ArrayList<HashMap<String, Object>>();
        HashMap<String, Object> accountMap = new HashMap<>();
        accountMap.put("countryCode", "KR");
        accountMap.put("businessType", "CD");
        accountMap.put("organization", cardComponyCode);
        accountMap.put("clientType", "P");
        accountMap.put("loginType", "1");
        accountMap.put("id", requestDto.getLoginId());

        try {
            log.info("codef 연결 시작");
            String publicKey = easyCodef.getPublicKey();
            // 디버깅용 로그 추가
            log.info("Public Key 존재 여부: {}", (publicKey != null && !publicKey.isEmpty()));
            accountMap.put("password", EasyCodefUtil.encryptRSA(requestDto.getLoginPW(), easyCodef.getPublicKey())); // RSA암호화가 필요한 필드는 encryptRSA(String plainText, String publicKey) 메서드를 이용해 암호화
        } catch (Exception e) {
            e.printStackTrace();
            throw new BusinessException(ErrorCode.CODEF_API_CONNECTEDID_ERROR);
        }

        accountList.add(accountMap);
        HashMap<String, Object> parameterMap = new HashMap<String, Object>();
        parameterMap.put("accountList", accountList);

        boolean hasConnectedId = user.getConnectedId() != null && !user.getConnectedId().isEmpty();

        String pathOfAPI = hasConnectedId ? CREATE_CONNECTED_ID_ADD_PATH : CREATE_CONNECTED_ID_PATH;

        if (hasConnectedId)
            parameterMap.put("connectedId", user.getConnectedId());

        try{

            String response = easyCodef.requestProduct(pathOfAPI,EasyCodefServiceType.DEMO,parameterMap);

            log.info("📢 호출 API response: {}", response);
            ConnectedIdResponse connectedIdResponse = objectMapper.readValue(response, ConnectedIdResponse.class);
            String connectedId = hasConnectedId ? user.getConnectedId() : connectedIdResponse.getData().getConnectedId();

            if(connectedId ==null || connectedId.isEmpty()){
                throw new BusinessException(ErrorCode.CODEF_API_CONNECTEDID_ERROR);
            }
            //업데이트
            user.updateConnectedId(connectedId);
            user.addConnectedCompany(CardCompany.findByCode(cardComponyCode));
            userRepository.save(user);

            return connectedId;

        }catch (Exception e){
            throw new BusinessException(ErrorCode.CODEF_API_CONNECTEDID_ERROR);
        }
    }

    //보유카드 API
    private static final String CARD_LIST_PATH = "/v1/kr/card/p/account/card-list";
    @Transactional
    public void saveCards(Integer userId, String connectedId, String cardCompanyCode){
        User user = userRepository.findByUserId(userId).orElseThrow(()->new BusinessException(ErrorCode.USER_NOT_FOUNT));
        try{
            //메인 카드 보유 여부 - 최초 등록 카드 설정
            boolean alreadyHasMain = userCardRepository.findByUserAndIsMainTrue(user).isPresent();
            final AtomicBoolean needsMainCard = new AtomicBoolean(!alreadyHasMain);
            // codef
            HashMap<String,Object> parameterMap = new HashMap<String,Object>();
            parameterMap.put("organization",cardCompanyCode);
            parameterMap.put("connectedId",connectedId);
            String response = easyCodef.requestProduct(CARD_LIST_PATH,EasyCodefServiceType.DEMO,parameterMap);
            log.info("✒️CODEF Response for 0304: {}", response);
            CardListResponse responseDto = objectMapper.readValue(response, CardListResponse.class);

            for(CardListResponse.Data data : responseDto.getData()){
                if ("분실·도난".equals(data.getResState())) {
                    log.info("분실 카드 제외: {}", data.getCardName());
                    continue;
                }
                // Card 엔티티 관리 (Master Card 정보)
                // 카드 이름이 동일하면 기존 Card 엔티티를 사용, 없으면 생성
                Card cardMaster = cardRepository.findByCardName(data.getCardName())
                        .orElseGet(() -> cardRepository.save(
                                Card.builder()
                                        .cardName(data.getCardName())
                                        .cardCompany(CardCompany.findByCode(cardCompanyCode))
                                        .build()
                        ));
                // UserCard 중복 체크 및 저장 (특정 유저의 실제 카드 정보)
                userCardRepository.findByUserAndCard(user, cardMaster)
                        .ifPresentOrElse(
                                existing -> log.info("등록된 카드: {}", data.getCardName()),
                                () -> {
                                    String fullMaskedNo = data.getCardNo();
                                    if (fullMaskedNo == null) return;
                                    // 첫 카드라면 메인으로 설정
                                    boolean isMain = needsMainCard.getAndSet(false);
                                    UserCard newUserCard = UserCard.builder()
                                            .user(user)
                                            .card(cardMaster)
                                            .codefCardNo(fullMaskedNo) // 전체 마스킹 번호 저장
                                            .lastFourDigits(fullMaskedNo.substring(fullMaskedNo.length() - 4)) // 끝 4자리 추출
                                            .cardCompanyCode(cardCompanyCode)
                                            .isMain(isMain)
                                            .build();
                                    userCardRepository.save(newUserCard);
                                    log.info("카드 등록 성공: {}", data.getCardName());
                                }
                        );
            }
        }catch (Exception e){
            log.error("카드 저장 중 오류 발생: {}", e.getMessage());
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }
    }

    // 승인 거래내역
    @Transactional
    public void pullCardTransactions(Integer userId, String connectedId) {
        User user = userRepository.findById(userId).orElseThrow(() -> new BusinessException(ErrorCode.USER_NOT_FOUNT));
        List<CardCompany> connectedCompanies = user.getConnectedCompanyList();
        if (connectedCompanies.isEmpty()) return;

        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyyMMdd");
        String endDate = LocalDate.now().format(formatter) ;        // 오늘
        String startDate = LocalDate.now().minusYears(1).format(formatter);  // 1년 전

        //사용자 카드 번호 4개
        Map<String , UserCard> cardMap = user.getUserCards().stream()
                .filter(c->c.getLastFourDigits()!=null)
                .collect(Collectors.toMap(UserCard::getLastFourDigits,c->c));

        for(CardCompany company : connectedCompanies){
            HashMap<String,Object> parameterMap = new HashMap<>();
            parameterMap.put("organization", company.getCode());
            parameterMap.put("connectedId", connectedId);
            parameterMap.put("startDate", startDate);
            parameterMap.put("endDate", endDate);
            parameterMap.put("orderBy", "0");
            parameterMap.put("inquiryType", "1");
            parameterMap.put("memberStoreInfoType", "1");

            //codef 호출
            try{
                String response = easyCodef.requestProduct("/v1/kr/card/p/account/approval-list",EasyCodefServiceType.DEMO,parameterMap);
                TransactionListResponse responseDto = objectMapper.readValue(response, TransactionListResponse.class);
                if(responseDto.isSuccess() && responseDto.getData()!=null)
                    SaveTransactions(responseDto.getData(),cardMap);
            }catch (Exception e){
                log.error("{} 카드사 동기화 실패: {}", company.getCode(), e.getMessage());

            }
        }
    }

    private void SaveTransactions(List<TransactionListResponse.TransactionInfo> transactions ,Map<String,UserCard> cardMapByLast4) {

        DateTimeFormatter dtf = DateTimeFormatter.ofPattern("yyyyMMddHHmmss");

        //루프 동안 가맹점 분류 결과 기억
        Map<String,String> categoryLocalCache = new HashMap<>();

        for (TransactionListResponse.TransactionInfo info : transactions) {
            String lastFourDigits = info.getResCardNo().substring(info.getResCardNo().length() - 4);
            UserCard parentCard = cardMapByLast4.get(lastFourDigits);
            if (parentCard == null) continue;

            try {
                LocalDateTime approvedAt = LocalDateTime.parse(info.getDate() + info.getTime(), dtf);
                BigDecimal amount = new BigDecimal(info.getAmount());

                boolean exists = cardTransactionRepository.existsByUserCardAndApprovedAtAndAmountAndStoreName(
                        parentCard, approvedAt, amount, info.getStoreName());

                //거래 내역 없음
                if(!exists){
                    String bizNo = info.getStoreCorpNo();
                    String storeName = info.getStoreName();
                    String cacheKey = bizNo+storeName;
                    // 캐시 먼저 확인
                    String finalStoreType = categoryLocalCache.get(cacheKey);

                    //llm호출
                    if(finalStoreType == null) {
                        finalStoreType = getOrClassifyCategory(storeName, bizNo, info.getStoreType());
                        categoryLocalCache.put(cacheKey,finalStoreType);
                    }
                    CardTransaction transaction = CardTransaction.builder()
                            .userCard(parentCard)
                            .approvedAt(approvedAt)
                            .amount(amount)
                            .storeName(info.getStoreName())
                            .storeType(finalStoreType)
                            .build();
                    log.info("❤️ 가게이름 : {},가게타입 DB 저장:{}",info.getStoreName(),finalStoreType);
                    cardTransactionRepository.save(transaction);
                }
            } catch (Exception e) {
                log.error("거래 저장 중 오류: {}", info.getStoreName(), e);
            }
        }
    }

    private String getOrClassifyCategory(String storeName , String bizNo ,String storeType){
        // [1] Enum 키워드 매핑
        String fistCategory = CategoryGroup.classify(storeType,storeName);
        if(fistCategory!=null){
            log.info("🗒enum 키워드 매핑️'{}' -> {}", storeName, fistCategory);
            return fistCategory;
        }

        //[2] DB에 이미 저장된 가맹점인지 (사업자+이름) index
        Optional<MerchantCategory> cached = merchantCategoryRepository.findByBizNoAndStoreName(bizNo,storeName);
        if(cached.isPresent()) return cached.get().getCategory();
        // / [3] 없으면 LLM 호출
        log.info("🔍 DB에 없는 가맹점이라 LLM 호출합니다: {}", storeName);
        String classifiedCategory = openAIService.classifyTransaction(storeName,bizNo,storeType);

                    MerchantCategory newMapping = MerchantCategory.builder()
                            .bizNo(bizNo)
                            .storeName(storeName)
                            .category(classifiedCategory)
                            .build();

                    merchantCategoryRepository.save(newMapping);
                    log.info("⚠️mechant DB 저장 {} , {}",storeName,classifiedCategory);
                    return classifiedCategory;
    }

}
