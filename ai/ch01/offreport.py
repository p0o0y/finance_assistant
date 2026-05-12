from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from llama_index.llms.ollama import Ollama
import json

router = APIRouter()
slm_model = Ollama(model="qwen2.5:7b", 
                   request_timeout=120.0,
                   temperature=0.0,
                   system="당신은 소비데이터 분석하는 역할입니다. 지시된 형식 외 어떤 문장도 추가하지 마세요.")

class ReportRequest(BaseModel):
    user_id:int
    year_month:str 
    total_amount:int
    category_stats: dict
    top_stores: list
    top_stores_by_amount: list
    auto_payments: list

REQUIRED_FIELDS = [
    "편의점", "카페", "쇼핑", "배달", "OTT구독",
    "교통", "통신", "영화", "여가", "마트",
    "월소비", "고액가맹점", "정기결제"
]
def parse_and_fix(text: str, total_amount: int) -> str:
    text = text.replace("```markdown", "").replace("```", "").strip()
    result = {}
    for line in text.split("\n"):
        line = line.strip()
        if ":" in line:
            k, _, v = line.partition(":")
            k = k.strip().lstrip("#- ").strip()
            v = v.strip()
            if k in REQUIRED_FIELDS:
                result[k] = v if v else "없음"

    for f in REQUIRED_FIELDS:
        result.setdefault(f, "없음")
        
    result["월소비"] = f"{total_amount:,}원"
    return "\n".join(f"{k}: {v}" for k, v in result.items())

@router.post("/report")
async def generate_report(request: ReportRequest):
    
    # 카테고리 top3 
    category_text = "\n".join([
        f"- {k}: {v:,}원" 
        for k, v in sorted(request.category_stats.items(), 
                          key=lambda x: x[1], reverse=True)
    ])
    
    # 빈도 top3 
    store_text = ", ".join([
        f"{s['name']}({s['count']}회)" 
        for s in request.top_stores[:5]
    ])

    # 고액 top3 + 가격
    amount_text = ", ".join([
        f"{s['name']}({s['total_amount']:,}원)" 
        for s in request.top_stores_by_amount[:5]
    ])

    # 정기결제
    auto_text = ", ".join(request.auto_payments) if request.auto_payments else "없음"

    prompt = (
        f"아래 예시와 똑같은 형식으로만 출력하세요. 예시 외 문장 절대 추가 금지.\n\n"

        f"[예시 입력]\n"
        f"카테고리 참고: 카페,간식(62,000원), 쇼핑(45,000원), 주거통신(19,910원)\n"
        f"방문 가맹점: 스타벅스커피영통점(9회), GS25영통점(3회), GS25강남점(2회)\n"
        f"고액 결제: 무신사(45,000원), 컬리(32,000원), KT통신요금자동(19,910원)\n"
        f"정기결제 항목: KT통신요금자동, 넷플릭스\n\n"
        f"[예시 출력]\n"
        f"편의점: GS25\n"
        f"카페: 스타벅스\n"
        f"쇼핑: 무신사\n"
        f"배달: 컬리\n"
        f"OTT구독: 넷플릭스\n"
        f"교통: 없음\n"
        f"통신: KT\n"
        f"영화: 없음\n"
        f"여가: 없음\n"
        f"마트: 없음\n"
        f"월소비: 416,000원\n"
        f"고액가맹점: 무신사\n"
        f"정기결제: KT통신요금, 넷플릭스\n\n"

        f"---\n"
        f"[규칙]\n"
        f"1. 같은 브랜드 지점은 합산 (GS25영통점+GS25강남점 → GS25)\n"
        f"2. 지점명/특수문자 제거하고 브랜드명으로 통합\n"
        f"   (GS25영통점→GS25, 스타벅스커피→스타벅스, ＫＴ통신요금자동→KT)\n"
        f"3. 편의점: GS25/CU/세븐일레븐/이마트24 중\n"
        f"4. 쇼핑: 무신사/29CM/쿠팡/올리브영/지그재그/에이블리 중\n"
        f"5. 배달: 배달의민족/쿠팡이츠/컬리 중\n"
        f"6. OTT구독: 넷플릭스/유튜브/티빙/스포티파이/디즈니플러스 중\n"
        f"7. 교통: 지하철/버스/택시/KTX 중\n"
        f"8. 통신: SKT/KT/LG U+ 중\n"
        f"9. 자동/정기/납부 포함 가맹점은 정기결제로 분류\n"
        f"10. 총소비의 20% 이상이면 고액가맹점\n"
        f"11. 없으면 없음 작성\n\n"

        f"[실제 입력]\n"
        f"카테고리 참고: {category_text}\n"
        f"방문 가맹점: {store_text}\n"
        f"고액 결제: {amount_text}\n"
        f"정기결제 항목: {auto_text}\n\n"
        f"[실제 출력]\n"
    )

    try:
        response = slm_model.complete(prompt)
        raw = response.text.strip()
        report_text = parse_and_fix(raw, request.total_amount)  # 추가
        return {"report_text": report_text}
    except Exception as e:
        return {"report_text": f"리포트 생성 실패: {e}"}