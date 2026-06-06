package demo.senior_project.domain.fastapi;

import java.util.List;

record CardResponse(String answer, List<SourceNode> source_nodes) {
} // 전체 응답
