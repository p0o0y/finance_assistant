from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Dict
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
    소비패턴: Optional[str] = None

class ReportRequest(BaseModel):
    user_id: int
    year_month: str
    total_amount: int
    category_stats: dict
    categorized_stores: Dict[str, List[str]]
    categorized_amount_stores: Dict[str, List[str]]
    auto_payments: list


@router.post("/askreport")
async def generate_report(request: ReportRequest):

    sorted_cats = sorted(request.category_stats.items(), key=lambda x: x[1], reverse=True)
    category_text = ", ".join([
        f"{k}(주요)" if i == 0 else k
        for i, (k, v) in enumerate(sorted_cats)
    ])

    store_text = "\n".join([
        f"{cat}: {', '.join(names)}"
        for cat, names in request.categorized_stores.items()
    ]) if request.categorized_stores else "없음"

    amount_text = "\n".join([
        f"{cat}: {', '.join(names)}"
        for cat, names in request.categorized_amount_stores.items()
    ]) if request.categorized_amount_stores else "없음"

    auto_text = ", ".join(request.auto_payments) if request.auto_payments else "없음"

    print(f"\n=== [{request.year_month}] 입력 데이터 ===")
    print(f"카테고리: {category_text}")
    print(f"자주방문:\n{store_text}")
    print(f"고액결제:\n{amount_text}")
    print(f"정기결제: {auto_text}")
    print(f"총소비: {request.total_amount:,}원")

    messages = [
        {
            "role": "system",
            "content": (
                "당신은 소비데이터 분석 전문가입니다. 반드시 JSON 형식으로만 출력하세요.\n"
                "규칙:\n"
                "1. 지점명/특수문자/주식회사 제거 후 브랜드명만 남기기\n"
                "   예) GS25경희예술점 → GS25, （주）스타벅스커피 → 스타벅스, 씨유(CU)용인점 → CU\n"
                "2. 같은 브랜드 다른 지점은 하나로 합산 (GS25경희예술+GS25경희국제 → GS25)\n"
                "3. 여러 브랜드는 /로 구분 (스타벅스/이디야)\n"
                "4. 자주방문과 고액결제의 모든 가게를 빠짐없이 해당 카테고리 필드에 넣기\n"
                "5. 카테고리는 절대 바꾸지 말 것 (입력에 없는 카테고리 필드는 null)\n"
                "6. 소비패턴은 한두 줄 자연스러운 문장으로 요약\n"
            )
        },
        {
            "role": "user",
            "content": (
                f"[예시]\n"
                f"자주방문:\n"
                f"편의점: GS25경희예술점, GS25경희국제점\n"
                f"카페: （주）스타벅스커피강남점, 이디야역삼점\n"
                f"고액결제:\n"
                f"마트: 홈플러스（주）\n\n"
                f"출력:\n"
                f"편의점: GS25\n"
                f"카페: 스타벅스/이디야\n"
                f"마트: 홈플러스\n\n"
                f"[실제 데이터]\n"
                f"자주방문:\n{store_text}\n\n"
                f"고액결제:\n{amount_text}\n"
            )
        }
    ]

    try:
        response = chat(
            model="qwen2.5:7b",
            messages=messages,
            format=ConsumptionReport.model_json_schema(),
            options={"temperature": 0.0}
        )

        print(f"\n🤖 LLM 원본 출력:\n{response.message.content}")

        report = ConsumptionReport.model_validate_json(response.message.content)
        report_dict = report.model_dump(exclude_none=True)

        # 월소비/정기결제는 LLM 안 거치고 직접 붙이기
        report_dict["정기결제"] = auto_text if request.auto_payments else None
        report_dict["월소비"] = f"{request.total_amount:,}원"

        report_dict = {k: v for k, v in report_dict.items() if v and str(v).strip() and v != "없음"}

        report_text = "\n".join([f"{k}: {v}" for k, v in report_dict.items()])

        print(f"\n📜=== 리포트 ===")
        print(report_text)
        print(f"==================\n")

        return {"report_text": report_text}

    except Exception as e:
        print(f"\n❌ 오류: {e}")
        return {"report_text": f"리포트 생성 실패: {e}"}