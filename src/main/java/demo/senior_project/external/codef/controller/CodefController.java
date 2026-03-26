package demo.senior_project.external.codef.controller;

import demo.senior_project.domain.user.domain.User;
import demo.senior_project.domain.user.repository.UserRepository;
import demo.senior_project.external.codef.CodefService;
import demo.senior_project.external.codef.dto.request.CreateConnectedIdRequestDto;
import demo.senior_project.global.error.BusinessException;
import demo.senior_project.global.error.ErrorCode;
import demo.senior_project.global.response.ApiResponse;
import demo.senior_project.global.security.oauth.CustomOauth2User;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;


@RestController
@RequiredArgsConstructor
@RequestMapping("/api/codef")
public class CodefController {
    private final CodefService codefService;
    private final UserRepository userRepository;

    // 특정 카드사 연동여부
    @GetMapping("/connect/status")
    public ApiResponse<Boolean> getCardConnectionStatus(
            @AuthenticationPrincipal CustomOauth2User principal,
            @RequestParam String cardCompanyCode){
        Integer userId = principal.getUserId().intValue();
        User user = userRepository.findByUserId(userId)
                .orElseThrow(() -> new BusinessException(ErrorCode.APP_USER_NOT_FOUNDUSER_NOT_FOUNT));
        boolean isConnected = user.getConnectedCompanyList().stream()
                .anyMatch(cardCompany -> cardCompany.getCode().equals(cardCompanyCode));
        return ApiResponse.success(isConnected);
    }

    //카드사 연동 - conntecId 발급 및 계정 추가
    @PostMapping("/connect")
    public ApiResponse<String> connectNewCard(
        @AuthenticationPrincipal CustomOauth2User principal,
        @RequestParam String cardCompanyCode ,
        @RequestBody CreateConnectedIdRequestDto requestDto){
        Integer userId = principal.getUserId().intValue();
        String connectedId = codefService.createConnectedAccount(userId, requestDto, cardCompanyCode);
        return ApiResponse.success(connectedId,"CO001","connectedID 발급 성공 ");
    }

    //사용자 보유 카드 목록
    @PostMapping("/cards/sync")
    public ApiResponse<Void> syncUserCards(
            @AuthenticationPrincipal CustomOauth2User principal,
            @RequestParam String cardCompanyCode){
        Integer userId = principal.getUserId().intValue();

        User user = userRepository.findByUserId(userId)
                .orElseThrow(() -> new BusinessException(ErrorCode.APP_USER_NOT_FOUNDUSER_NOT_FOUNT));

        validateConnectedId(user);
        codefService.saveCards(userId, user.getConnectedId(), cardCompanyCode);
        return ApiResponse.success(null);
    }

    // 카드 내역 가져오기
    @PostMapping("/transactions/sync")
    public ApiResponse<Void> syncTransactions(
       @AuthenticationPrincipal CustomOauth2User principal
     ) {
        Integer userId = principal.getUserId().intValue();
        User user = userRepository.findByUserId(userId)
                .orElseThrow(() -> new BusinessException(ErrorCode.APP_USER_NOT_FOUNDUSER_NOT_FOUNT));

    validateConnectedId(user);
    codefService.pullCardTransactions(userId, user.getConnectedId());
    return ApiResponse.success(null);
    }


    private void validateConnectedId(User user) {
        if (user.getConnectedId() == null || user.getConnectedId().isEmpty()) {
            throw new BusinessException(ErrorCode.CODEF_API_CONNECTEDID_ERROR);
        }
    }
}



