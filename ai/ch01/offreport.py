from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional,Dict
from ollama import chat

router = APIRouter()

class ConsumptionReport(BaseModel):
    카페: Optional[str] = None
    병원: Optional[str] = None
    마트: Optional[str] = None
    편의점: Optional[str] = None
    음식점: Optional[str] = None
    쇼핑: Optional[str] = None
    교통: Optional[str] = None
    주거통신: Optional[str] = None
    OTT: Optional[str] = None
    여가: Optional[str] = None
    배달: Optional[str] = None
    교육: Optional[str] = None
    월소비: Optional[str] = None
    고액가맹점: Optional[str] = None
    정기결제: Optional[str] = None
    소비패턴: Optional[str] = None  
# slm_model = Ollama(model="qwen2.5:7b", 
#                    request_timeout=120.0,
#                    temperature=0.0,
#                    system="당신은 소비데이터 분석하는 역할입니다. 지시된 형식 외 어떤 문장도 추가하지 마세요.")

class ReportRequest(BaseModel):
    user_id:int
    year_month:str 
    total_amount:int
    category_stats: dict
    categorized_stores: Dict[str, List[str]]         # 카테고리별 자주방문
    categorized_amount_stores: Dict[str, List[str]]  # 카테고리별 고액결제
    auto_payments: list


@router.post("/askreport")
async def generate_report(request: ReportRequest):
    
    # 카테고리 top3 
    sorted_cats = sorted(request.category_stats.items(), key=lambda x: x[1], reverse=True)
    category_text = ", ".join([
        f"{k}(주요)" if i == 0 else k
        for i, (k, v) in enumerate(sorted_cats)
    ])
    
    # 빈도 top3  {"교통": ["카카오T강남", "카카오T역삼"], "카페,간식": ["이디야역삼점"]}
    store_text = "\n".join([
        f"{cat}: {', '.join(names)}"
        for cat, names in request.categorized_stores.items()
    ]) if request.categorized_stores else "없음"


    amount_text = "\n".join([
        f"{cat}: {', '.join(names)}"
        for cat, names in request.categorized_amount_stores.items()
    ]) if request.categorized_amount_stores else "없음"


    # 정기결제
    auto_text = ", ".join(request.auto_payments) if request.auto_payments else "없음"
    
     # 로그
    print(f"\n=== [{request.year_month}] 입력 데이터 ===")
    print(f"카테고리: {category_text}")
    print(f"자주방문:\n{store_text}")
    print(f"고액결제:\n{amount_text}")
    print(f"정기결제: {auto_text}")
    print(f"총소비: {request.total_amount:,}원")

    messages=[
        {"role": "system",
        "content": "당신은 소비데이터 분석하는 역할입니다.반드시 json형식으로만 출력하세요"
          "1. 지점명/특수문자 제거 후 브랜드명만 남기기\n"
            "2. 같은 브랜드 지점 합산\n"
            "3. 소비패턴 한 두줄 요약 추가\n"
            "절대로 카테고리를 바꾸지 마세요."
        },
        {"role": "user",
         "content": (
            f"[카테고리명 변환]\n"
            f"카페,간식→카페 / 주거통신→통신 / 구독OTT→OTT구독\n"
            f"취미,여가→여가 / 항공,여행→여가\n\n"

            f"[예시]\n"
            f"입력 - 카페,간식: 스타벅스커피영통점, 이디야강남점\n"
            f"출력 - 카페: 스타벅스/이디야\n\n"
            f"입력 - 교통: 카카오T강남, 카카오T역삼\n"
            f"출력 - 교통: 카카오T\n\n"

            f"[실제 데이터]\n"
            f"자주방문:\n{store_text}\n\n"
            f"고액결제:\n{amount_text}\n\n"
            f"정기결제: {auto_text}\n"
            
         )}
    ] 
    

    try:
        response = chat(model="qwen2.5:7b", messages=messages, format=ConsumptionReport.model_json_schema(),options={"temperature": 0.0})
        print(f"=== 모델 raw 응답 ===\n{response.message.content}")
        
        # validate json and fix if needed
        report = ConsumptionReport.model_validate_json(response.message.content)
        report_dict = report.model_dump(exclude_none=True)
        report_dict["월소비"]= f"{request.total_amount:,}원"
        report_text = "\n".join([f"{k}: {v}" for k, v in report_dict.items()])
        
        print(f"\n=== 리포트 ===")
        print(report_text)
        print(f"==================\n")

        return {"report_text": report_text}
    except Exception as e:
        return {"report_text": f"리포트 생성 실패: {e}"}