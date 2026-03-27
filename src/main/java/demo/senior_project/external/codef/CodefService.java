package demo.senior_project.external.codef;

import demo.senior_project.domain.transaction.domain.entity.CategoryGroup;
import demo.senior_project.domain.transaction.domain.entity.Card;
import demo.senior_project.domain.transaction.domain.entity.CardTransaction;
import demo.senior_project.domain.transaction.domain.entity.MerchantCategory;
import demo.senior_project.domain.transaction.repository.*;
import demo.senior_project.domain.transaction.serevice.TransactionsSaveService;
import demo.senior_project.domain.user.CardCompany;
import demo.senior_project.domain.user.domain.User;
import demo.senior_project.domain.user.domain.UserCard;
import demo.senior_project.domain.user.repository.UserCardRepository;
import demo.senior_project.domain.user.repository.UserRepository;
import demo.senior_project.external.codef.dto.ParsedTransaction;
import demo.senior_project.external.codef.dto.request.CreateConnectedIdRequestDto;
import demo.senior_project.external.codef.dto.response.CardListResponse;
import demo.senior_project.external.codef.dto.response.ConnectedIdResponse;
import demo.senior_project.external.codef.dto.response.TransactionListResponse;
import demo.senior_project.global.error.BusinessException;
import demo.senior_project.global.error.ErrorCode;
import io.codef.api.EasyCodef;
import io.codef.api.EasyCodefServiceType;
import io.codef.api.EasyCodefUtil;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import tools.jackson.databind.ObjectMapper;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.List;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class CodefService {
    private final ObjectMapper objectMapper;
    private final EasyCodef easyCodef;
    private final EasyCodefUtil EasyCodefUtil;
    private final UserRepository userRepository;
    private final CardRepository cardRepository;
    private final UserCardRepository userCardRepository;
    private final CardTransactionRepository cardTransactionRepository;
    private final MerchantCategoryRepository merchantCategoryRepository;
    private  final AsyncService asyncService;
    private final TransactionsSaveService transactionsSaveService;
    private final Executor codefTaskExecutor;

    private static final String CREATE_CONNECTED_ID_PATH = "/v1/account/create";
    private static final String CREATE_CONNECTED_ID_ADD_PATH = "/v1/account/add";
    //connecteID 발급 , 계정 추가
    public String createConnectedAccount(Integer userId, CreateConnectedIdRequestDto requestDto, String cardComponyCode) {
        User user = userRepository.findByUserId(userId).orElseThrow(() -> new BusinessException(ErrorCode.USER_NOT_FOUNT));

        List<HashMap<String, Object>> accountList = new ArrayList<>();
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
        HashMap<String, Object> parameterMap = new HashMap<>();
        parameterMap.put("accountList", accountList);

        boolean hasConnectedId = user.getConnectedId() != null && !user.getConnectedId().isEmpty();

        String pathOfAPI = hasConnectedId ? CREATE_CONNECTED_ID_ADD_PATH : CREATE_CONNECTED_ID_PATH;

        if (hasConnectedId)
            parameterMap.put("connectedId", user.getConnectedId());

        try {
            String response = easyCodef.requestProduct(pathOfAPI, EasyCodefServiceType.DEMO, parameterMap);
            ConnectedIdResponse connectedIdResponse = objectMapper.readValue(response, ConnectedIdResponse.class);
            String connectedId = hasConnectedId ? user.getConnectedId() : connectedIdResponse.getData().getConnectedId();

            if (connectedId == null || connectedId.isEmpty()) {
                throw new BusinessException(ErrorCode.CODEF_API_CONNECTEDID_ERROR);
            }
            //업데이트
            user.updateConnectedId(connectedId);
            user.addConnectedCompany(CardCompany.findByCode(cardComponyCode));
            userRepository.save(user);

            return connectedId;
        } catch (Exception e) {
            throw new BusinessException(ErrorCode.CODEF_API_CONNECTEDID_ERROR);
        }
    }

    //보유카드 API
    private static final String CARD_LIST_PATH = "/v1/kr/card/p/account/card-list";

    @Transactional
    public void saveCards(Integer userId, String connectedId, String cardCompanyCode) {
        User user = userRepository.findByUserId(userId).orElseThrow(() -> new BusinessException(ErrorCode.USER_NOT_FOUNT));
        try {
            //메인 카드 보유 여부 - 최초 등록 카드 설정
            boolean alreadyHasMain = userCardRepository.findByUserAndIsMainTrue(user).isPresent();
            final AtomicBoolean needsMainCard = new AtomicBoolean(!alreadyHasMain);
            // codef
            HashMap<String, Object> parameterMap = new HashMap<>();
            parameterMap.put("organization", cardCompanyCode);
            parameterMap.put("connectedId", connectedId);
            String response = easyCodef.requestProduct(CARD_LIST_PATH, EasyCodefServiceType.DEMO, parameterMap);
            CardListResponse responseDto = objectMapper.readValue(response, CardListResponse.class);

            for (CardListResponse.Data data : responseDto.getData()) {
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
        } catch (Exception e) {
            log.error("카드 저장 중 오류 발생: {}", e.getMessage());
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }
    }

    // 승인 거래내역
    public void pullCardTransactions(Integer userId, String connectedId) {
        User user = userRepository.findById(userId).orElseThrow(() -> new BusinessException(ErrorCode.USER_NOT_FOUNT));
        List<CardCompany> connectedCompanies = user.getConnectedCompanyList();
        if (connectedCompanies.isEmpty()) return;

        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyyMMdd");
        String endDate = LocalDate.now().format(formatter);
        String startDate = LocalDate.now().minusYears(1).format(formatter);

        //사용자 카드 번호 4개
        Map<String, UserCard> cardMap = user.getUserCards().stream()
                .filter(c -> c.getLastFourDigits() != null)
                .collect(Collectors.toMap(UserCard::getLastFourDigits, c -> c));

        List<CompletableFuture<Void>> codefFutures = connectedCompanies.stream()
                .map(company -> CompletableFuture.runAsync(() -> {
                    HashMap<String, Object> parameterMap = new HashMap<>();
                    parameterMap.put("organization", company.getCode());
                    parameterMap.put("connectedId", connectedId);
                    parameterMap.put("startDate", startDate);
                    parameterMap.put("endDate", endDate);
                    parameterMap.put("orderBy", "0");
                    parameterMap.put("inquiryType", "1");
                    parameterMap.put("memberStoreInfoType", "1");
            try {
                log.info("🔢main ) codef api 호출 {}  ",company.getDescription());  //codef 호출 네트워크 IO
                String response = easyCodef.requestProduct(
                        "/v1/kr/card/p/account/approval-list", EasyCodefServiceType.DEMO, parameterMap);
                TransactionListResponse responseDto = objectMapper.readValue(response, TransactionListResponse.class);
                if (responseDto.isSuccess() && responseDto.getData() != null)
                    SaveTransactions(responseDto.getData(), cardMap);
            } catch (Exception e) {
                log.error("{} 카드사 동기화 실패: {}", company.getCode(), e.getMessage());}
            }, codefTaskExecutor))
            .toList();

            CompletableFuture.allOf(codefFutures.toArray(new CompletableFuture[0]))
                    .thenRun(()->{
                        log.info("👩‍🎤 sub thread 모든 카드사 거래내역 동기화 및 llm 분류 완료 ");
                    })
                    .exceptionally(ex->{
                        log.error("동기화 중 오류 발생");
                        return null;}
                    );
            log.info("🔢main ) 할 일 끝 접수만 ok");

    }

    // 외부데이터 ->1차필터 (우리 시스템 형식 ) -> 2차 (DB대조) 이미 있는지 ->3차 새로 저장할거 중에 이미 카테고리 아는건지 ->최종처리는 분류가 필요한 데이터만 가지고감
    private void SaveTransactions(List<TransactionListResponse.TransactionInfo> transactions, Map<String, UserCard> cardMapByLast4) {
        DateTimeFormatter dtf = DateTimeFormatter.ofPattern("yyyyMMddHHmmss");

        List<ParsedTransaction> parsed = transactions.stream()
                .map(info -> {
                    String last4 = info.getResCardNo().substring(info.getResCardNo().length() - 4);
                    UserCard card = cardMapByLast4.get(last4);
                    try {
                        return new ParsedTransaction(
                                info,
                                card,
                                LocalDateTime.parse(info.getDate() + info.getTime(), dtf),
                                new BigDecimal(info.getAmount())
                        );
                    } catch (Exception e) {
                        return null;
                    }
                })
                .filter(Objects::nonNull)
                .toList();

        //2 . DB 기존 데이터 불러오기 (N->1쿼리) for X
        Set<String> existingKeys = cardTransactionRepository
                .findByUserCardInAndApprovedAtIn(
                        parsed.stream().map(p -> p.getCard()).distinct().toList(),
                        parsed.stream().map(p -> p.getTransactionDateTime()).toList()
                )
                .stream()
                .map(t -> t.getUserCard().getUserCardId() + "_" + t.getApprovedAt() + "_" + t.getStoreName())
                .collect(Collectors.toSet());

        // DB에 없는 거래내역만
        List<ParsedTransaction> newOnes = parsed.stream()
                .filter(p -> !existingKeys.contains(
                        p.getCard().getUserCardId() + "_" + p.getTransactionDateTime() + "_" + p.getInfo().getStoreName()))
                .toList();


        // 가맹점 카테고리 캐싱하기
        List<String> bizNos  = newOnes.stream().map(p -> p.getInfo().getStoreCorpNo()).distinct().toList();
        List<String> storeNames = newOnes.stream().map(p -> p.getInfo().getStoreName()).distinct().toList();

        Map<String, String> merchantCache = merchantCategoryRepository
                .findAllByBizNoInAndStoreNameIn(bizNos, storeNames)
                .stream()
                .collect(Collectors.toMap(
                        m -> m.getBizNo() + "|" + m.getStoreName(),
                        MerchantCategory::getCategory
                ));
        // 4. 카테고리 분류 + LLM 배치 처리
        classifyAndSave(newOnes, merchantCache);
    }


    public void classifyAndSave(List<ParsedTransaction> newOnes, Map<String, String> merchantCache) {
        // LLM 호출이 필요한 항목들을 정보를 포함해서 담아둘 임시 맵
        log.info("🔢 sub 분류 프로세스 시작 - 대상 건수: {}건", newOnes.size());

        Map<String, PendingLLM> pendingLLMs = new HashMap<>(); //LLM에 보낼 것
        List<MerchantCategory> toSaveMerchants = new ArrayList<>(); // DB에 저장할 것

        for (ParsedTransaction p : newOnes) {
            String bizNo = p.getInfo().getStoreCorpNo();
            String storeName = p.getInfo().getStoreName();
            String storeType = p.getInfo().getStoreType();
            String key = bizNo + "|"+storeName;

            // 1) DB 이미 캐시에 있거나
            if (merchantCache.containsKey(key)) continue;

            // 2) 로컬 캐시 cpu 탐색
            String enumResult = CategoryGroup.classify(storeType, storeName);
            if (enumResult != null) {
                merchantCache.put(key, enumResult);
                toSaveMerchants.add(MerchantCategory.builder()
                        .bizNo(bizNo)
                        .storeName(storeName)
                        .category(enumResult)
                        .build());
                continue;
            }

            // 3) LLM 비동기 실행 예약 (중복 방지)
            if (!pendingLLMs.containsKey(key)) {
                log.info("⏩ sub 비동기 요청 예약: {}", storeName);
                CompletableFuture<String> future = asyncService.classifyAsync(storeName, bizNo, storeType);
                pendingLLMs.put(key, new PendingLLM(bizNo, storeName, future));
            }
        }
        log.info("⏳⏩⏩ sub ) 모든 비동기 결과 수집 시작 (future.get 구간)");
        long collectStart = System.currentTimeMillis();
        // 비동기 결과 수집 및 MerchantCategory 생성 기본 라틴 문자로 변환

        CompletableFuture<Void> allFutures = CompletableFuture.allOf( // future다 채워질 때 까지 기다리는 메서드 , 배열만 받음
                pendingLLMs.values().stream()
                        .map(PendingLLM::future)
                        .toArray(CompletableFuture[]::new)
        );
        //main 이 여기서 처음으로 멈춤 - 최대 15초 대기  allfuture.get 대기
        try {
            allFutures.get(15, TimeUnit.SECONDS);
        } catch (TimeoutException e) {
            log.warn(" LLM 전체 타임아웃 - 미완료 건은 기타 처리");
        }catch (Exception e){
            log.warn(" LLM 결과 수집 중 오류: {}", e.getMessage());
        }

        // 이미 완료된 상태에서 결과 수집 (블로킹 없이 즉시 수집
        pendingLLMs.forEach((key, pending) -> {
            String category = pending.future().getNow("기타"); // 완료됐으면 즉시 반환

            merchantCache.put(key, category);

            toSaveMerchants.add(MerchantCategory.builder()
                    .bizNo(pending.bizNo())
                    .storeName(pending.storeName())
                    .category(category)
                    .build());
        });
        log.info("⏱️ [Main] 결과 수집 완료! 소요시간: {}ms", (System.currentTimeMillis() - collectStart));

        // 5) 최종 CardTransaction , mercant  batch insert
        List<CardTransaction> toSave = newOnes.stream()
                .map(p -> CardTransaction.builder()
                        .userCard(p.getCard())
                        .approvedAt(p.getTransactionDateTime())
                        .amount(p.getAmount())
                        .storeName(p.getInfo().getStoreName())
                        .storeType(merchantCache.getOrDefault(
                                p.getInfo().getStoreCorpNo() + "|"+p.getInfo().getStoreName(), "기타"))
                        .build())
                .toList();

        transactionsSaveService.saveAll(toSaveMerchants, toSave);

        log.info("💾 [Main] DB 저장 완료");
    }

    //  (정보 보관용)
    private record PendingLLM(String bizNo, String storeName, CompletableFuture<String> future) {}
}

