package demo.senior_project.test.controller;

import demo.senior_project.test.service.ChatPipelineService;
import demo.senior_project.global.response.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class ChatController {
    private final ChatPipelineService chatPipelineService;

    @GetMapping("/api/ask")
    public ApiResponse<String> ask(@RequestParam String question) {
        String answer = chatPipelineService.process(question);
        return ApiResponse.success(answer);
    }
}
