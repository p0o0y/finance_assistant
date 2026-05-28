from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Dict
from ollama import chat
import json

router = APIRouter()

class NameRefinement(BaseModel):
    refined: Dict[str, str]  # {"GS25경희예술": "GS25"}

class ReportRequest(BaseModel):
    user_id: int
    year_month: str
    total_amount: int
    category_stats: dict
    categorized_stores: Dict[str, List[str]]
    categorized_amount_stores: Dict[str, List[str]]
    auto_payments: list


def step1_refine_names(all_stores: List[str]) -> Dict[str, str]:
    """SLM: 지점명 정제만"""
    if not all_stores:
        return {}

    input_list = "\n".join(f"- {s}" for s in all_stores)

    response = chat( #Ollama 라이브러리 함수 
        model="qwen2.5:7b",
        messages=[
    {
        "role": "system",
        "content": (
            "가게명 리스트를 받아서 지점명/특수문자를 제거한 브랜드명으로 매핑하세요.\n"
            "규칙:\n"
            "1. key는 반드시 입력에 있는 원본 그대로만 사용하세요 (예시 key 사용 금지)\n"
            "2. value는 정제된 브랜드명\n"
            "3. 정제할 게 없거나 모르면 원본을 그대로 value로 (빈 문자열 절대 금지)\n"
        )
    },
    {
        "role": "user",
        "content": (
            "[예시]\n"
            "입력:\n"
            "- GS25경희예술\n"
            "- (주）스타벅스커피\n"
            "- 씨유(CU)용인석성로점\n"
            "- OPIc\n"
            "- 교통요금\n"
            "출력:\n"
            "{\"GS25경희예술\": \"GS25\", \"（주）스타벅스커피\": \"스타벅스\", "
            "\"씨유(CU)용인석성로점\": \"CU\", \"OPIc\": \"OPIc\", \"교통요금\": \"교통요금\"}\n\n"  # ← } 와 \n\n 추가
            f"[실제 입력]\n{input_list}"
        )
    }
],
        format=NameRefinement.model_json_schema(),
        options={"temperature": 0.0}
    )

    # print(f"\n 1단계 LLM 원본:\n{response.message.content}")

    result = NameRefinement.model_validate_json(response.message.content)
    
    refined = {}

    for original in all_stores:
        value = result.refined.get(original, "")
        refined[original] = value if value.strip() else original

    return refined  


def step2_build_report(
    categorized_stores: Dict[str, List[str]],
    categorized_amount_stores: Dict[str, List[str]],
    name_map: Dict[str, str]
) -> Dict[str, str]:

    def refine(names: List[str]) -> str:
        seen = set()
        result = []
        for n in names:
            clean = name_map.get(n, n) 
            if clean not in seen:
                seen.add(clean)
                result.append(clean)
        return "/".join(result)

    report = {}

    for cat, names in categorized_stores.items():
        report[cat] = refine(names)

    # 고액결제 
    for cat, names in categorized_amount_stores.items():
        refined = refine(names)
        if cat in report:
            existing = set(report[cat].split("/"))
            new = [n for n in refined.split("/") if n not in existing]
            if new:
                report[cat] = report[cat] + "/" + "/".join(new)
        else:
            report[cat] = refined

    return report


def step3_summarize(report: Dict[str, str], auto_payments: List[str], category_stats: dict, total_amount: int) -> str:
    data_text = "\n".join(f"{k}: {v}" for k, v in report.items())
    auto_text = ", ".join(auto_payments) if auto_payments else "없음"

    # top3 비율 계산
    filtered = {k: v for k, v in category_stats.items() if k != "기타"}
    sorted_cats = sorted(filtered.items(), key=lambda x: x[1], reverse=True)
    cat_percent = "\n".join([f"{k}: {v:,}원 ({round(v / total_amount * 100)}%)"for k, v in sorted_cats])

    response = chat(
        model="qwen2.5:7b",
        messages=[
            {   "role": "system",
                "content": "소비 데이터를 보고 한두 문장으로 자연스럽게 요약하세요. 카테고리 비율과 가게이름을 자연스럽게 언급하세요. "
            },
            {   "role": "user",
                "content": (
                    f"[이용 가게]\n{data_text}\n\n"
                    f"[카테고리별 지출 비중]\n{cat_percent}\n\n"
                    f"[정기결제]\n{auto_text}"
                )
            }
        ],
        options={"temperature": 0.3}
    )


@router.post("/askreport")
async def generate_report(request: ReportRequest):

    sorted_cats = sorted(request.category_stats.items(), key=lambda x: x[1], reverse=True)
    
    category_text = ", ".join([
        f"{k}(주요)" if i == 0 else k
        for i, (k, v) in enumerate(sorted_cats)
    ])

    auto_text = ", ".join(request.auto_payments) if request.auto_payments else "없음"

    print(f"\n=== [{request.year_month}] 입력 데이터 ===")
    print(f"카테고리: {category_text}")
    print(f"자주방문: {request.categorized_stores}")
    print(f"고액결제: {request.categorized_amount_stores}")
    print(f"정기결제: {auto_text}")
    print(f"총소비: {request.total_amount:,}원")

    try:
        # 1단계: 지점명 정제
        all_stores = list(set(
            [s for names in request.categorized_stores.values() for s in names] +
            [s for names in request.categorized_amount_stores.values() for s in names]
        ))
     
        name_map = step1_refine_names(all_stores)

        # 2단계: 카테고리 매핑 
        report = step2_build_report(
            request.categorized_stores,
            request.categorized_amount_stores,
            name_map
        )
        print(f"\n 2단계 결과: {report}")

        # 3단계: 소비패턴 요약
        pattern = step3_summarize(report, request.auto_payments, request.category_stats, request.total_amount)

        report["소비패턴"] = pattern
        report["정기결제"] = auto_text if request.auto_payments else None
        report["월소비"] = f"{request.total_amount:,}원"

        report = {k: v for k, v in report.items() if v}
        report_text = "\n".join(f"{k}: {v}" for k, v in report.items())

        print(f"\n=== 리포트 === ")
        print(report_text)

        return {"report_text": report_text}

    except Exception as e:
        print(f"\n 오류: {e}")
        return {"report_text": f"리포트 생성 실패: {e}"}