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
    "편의점", "카페", "쇼핑", "OTT구독","배달",
    "교통", "통신", "영화", "여가", "마트,음식점","교육",
    "월소비", "고액가맹점", "정기결제"]


def parse_and_fix(text: str, total_amount: int) -> str:
    text = text.replace("```markdown", "").replace("```", "").strip()
    result = {}
    extras = []

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            k, _, v = line.partition(":")
            k = k.strip().lstrip("#- ").strip()  
            v = v.strip()
            if k in REQUIRED_FIELDS:
                result[k] = v if v else "없음"
            else:
                extras.append(line)
        else:
            extras.append(line)

    for f in REQUIRED_FIELDS:
        result.setdefault(f, "없음")
        
    result["월소비"] = f"{total_amount:,}원"

    ALWAYS_SHOW = {"월소비", "고액가맹점", "정기결제"}
    base = "\n".join(
        f"{k}: {v}" for k, v in result.items()
        if v != "없음" or k in ALWAYS_SHOW
    )
    extra = "\n".join(extras)
    return f"{base}\n{extra}".strip() if extras else base

@router.post("/askreport")
async def generate_report(request: ReportRequest):
    
    # 카테고리 top3 
    sorted_cats = sorted(request.category_stats.items(), key=lambda x: x[1], reverse=True)
    category_text = ", ".join([
        f"{k}(주요)" if i == 0 else k
        for i, (k, v) in enumerate(sorted_cats)
    ])
    
    # 빈도 top3 
    store_text = ", ".join([
        f"{s['name']}({s.get('type','기타')}/자주감)"
        for s in request.top_stores
    ]) if request.top_stores else "없음"


    # 고액 top3 + 가격
    amount_text = ", ".join([
        f"{s['name']}({s.get('type','기타')}/고액가맹점)"
        for s in request.top_stores_by_amount
    ]) if request.top_stores_by_amount else "없음"

    # 정기결제
    auto_text = ", ".join(request.auto_payments) if request.auto_payments else "없음"

    prompt = (
        f"아래 예시와 똑같은 형식으로 출력하고, 마지막에 소비패턴 한 줄 요약을 추가하세요.\n\n"

        f"[예시 입력]\n"
        f"카테고리: 카페,간식(주요), 쇼핑, 주거통신\n"
        f"방문 가맹점: 스타벅스(카페,간식/자주감), GS25(편의점/자주감)\n"
        f"고액 결제: 무신사(쇼핑/고액가맹점), 컬리(배달/고액가맹점)\n"
        f"정기결제: KT통신요금자동, 넷플릭스\n\n"
        f"[예시 출력]\n"
        f"편의점: GS25\n"        
        f"카페: 스타벅스\n"      
        f"쇼핑: 무신사\n"
        f"배달: 컬리\n"
        f"OTT구독: 넷플릭스\n"
        f"통신: KT\n"            
        f"월소비: 416,000원\n"
        f"정기결제: KT통신요금, 넷플릭스\n\n"
        f"소비패턴: 카페와 쇼핑 위주의 소비, OTT 정기구독 중\n\n"  

        f"---\n"
        f"[규칙]\n"
        f"1. 지점명/특수문자 제거하고 브랜드명으로만 출력\n"
        f"   (GS25영통점→GS25, 스타벅스커피→스타벅스, 이디야강남점->이디야)\n"
        f"2. 같은 브랜드 지점은 합산 (GS25영통점+GS25강남점 → GS25)\n"
        f"3. 편의점: GS25/CU/세븐일레븐/이마트24 중\n"
        f"4. 쇼핑: 무신사/29CM/올리브영/지그재그/에이블리/W컨셉 중\n"
        f"5. 배달: 배달의민족/쿠팡이츠/컬리 중\n"
        f"6. OTT구독: 넷플릭스/유튜브/티빙/스포티파이/디즈니플러스 중\n"
        f"7. 교통: 지하철/버스/택시/KTX 중\n"
        f"8. 통신: SKT/KT/LG U+ 중\n"
        f"9. 여가: 대한항공/하나투어/면세점/노래방/PC방/야놀자 중\n"
        f"10. 마트: 이마트/홈플러스/롯데마트/다이소/농협하나로마트 중\n"
        f"11. 자동/정기/납부 포함 가맹점은 정기결제로 분류\n"
        f"13. 해당 없는 필드는 출력하지 말 것\n\n"  

        f"[실제 입력]\n"
        f"카테고리: {category_text}\n"
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