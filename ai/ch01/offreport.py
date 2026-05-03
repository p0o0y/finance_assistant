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
    top_stores_by_amount: list

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

    # 금액 기준 top 5 가맹점 텍스트 변환
    amount_store_text = ", ".join([
        f"{s['name']}({s['total_amount']:,}원)" 
        for s in request.top_stores_by_amount[:5]
    ])

    prompt = (
    f"[{request.year_month} 카드 소비 데이터]\n"
    f"총 지출: {request.total_amount:,}원\n"
    f"카테고리별 지출:\n{category_text}\n"
    f"자주 방문한 가맹점: {store_text}\n"
    f"가장 많이 소비한 가맹점: {amount_store_text}\n\n"
    f"[지시사항]\n"
    f"카드 혜택 RAG 검색용 소비 프로파일을 작성하세요.\n\n"
    f"규칙:\n"
    f"1. 가맹점명은 브랜드로 통합 (GS25영통점→GS25, （주）스타벅스커피→스타벅스)\n"
    f"2. 반드시 아래 형식으로 출력하세요:\n\n"
    f"편의점: 해당 브랜드 (GS25/CU/세븐일레븐/이마트24)\n"
    f"카페: 해당 브랜드\n"
    f"쇼핑: 해당 브랜드 (29cm/무신사/쿠팡/올리브영/지그재그/W컨셉/에이블리)\n"
    f"배달: 해당 브랜드 (배달의민족/쿠팡이츠/컬리)\n"
    f"OTT/구독: 해당 브랜드 (넷플릭스/유튜브/티빙/스포티파이/쿠팡와우/네이버플러스)\n"
    f"교통: 해당 수단 (지하철/버스/택시/KTX/철도)\n"
    f"통신: 해당 통신사 (SKT/KT/LG U+)\n"
    f"영화: 해당 브랜드 (CGV/롯데시네마/메가박스)\n"
    f"여가: 해당 브랜드 (노래방/PC방/에버랜드/롯데월드/야놀자)\n"
    f"음식점: 해당 브랜드\n"
    f"마트: 해당 브랜드\n\n"
    f"[혜택 활용 가능성]\n"
    f"- 월 소비금액 {request.total_amount:,}원 \n"
    f"- 고액 결제 가맹점 ()\n"
    f"- 정기결제/구독/주거통신 항목 (OTT, 통신, 멤버십)\n"
    f"- 5줄로 요약\n"
)

    try:
        response = slm_model.complete(prompt,formatted=True,system="당신은 소비데이터를 분석하는 전문가입니다")
        return {"report_text": response.text.strip()}
    except Exception as e:
        return {"report_text": f"리포트 생성 실패: {e}"}