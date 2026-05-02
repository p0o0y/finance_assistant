from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from llama_index.llms.ollama import Ollama
import json

router = APIRouter()
slm_model = Ollama(model="qwen2.5:7b", request_timeout=120.0)

class ReportRequest(BaseModel):
    user_id:int
    year_month:str 
    total_amount:int
    category_stats: dict
    top_stores: list

@router.post("/report")
async def generate_report(request: ReportRequest):
    
    # 카테고리 지출 텍스트 변환
    category_text = "\n".join([
        f"- {k}: {v:,}원" 
        for k, v in sorted(request.category_stats.items(), 
                          key=lambda x: x[1], reverse=True)
    ])
    
    # 자주 간 가맹점 텍스트 변환
    store_text = ", ".join([
        f"{s['name']}({s['count']}회)" 
        for s in request.top_stores[:5]
    ])

    prompt = (
        f"아래는 {request.year_month} 카드 소비 데이터입니다.\n\n"
        f"총 지출: {request.total_amount:,}원\n"
        f"카테고리별 지출:\n{category_text}\n"
        f"자주 방문한 가맹점: {store_text}\n\n"
        f"위 데이터를 바탕으로 이 사용자의 소비 패턴을 5문장 이내로 요약하세요.\n"
        f"어떤 카테고리에 지출이 집중되는지, 어떤 혜택이 유용할지 포함하세요.\n"
        f"키워드와 의미 기반 벡터검색에 활용할 자료입니다"
    )

    try:
        response = slm_model.complete(prompt)
        return {"report_text": response.text.strip()}
    except Exception as e:
        return {"report_text": f"리포트 생성 실패: {e}"}