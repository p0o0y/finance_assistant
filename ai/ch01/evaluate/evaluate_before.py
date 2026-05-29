"""
Binary Filter 성능 측정 (Before LoRA)
- test.json의 쿼리+청크를 현재 Qwen 7B LLMRerank에 넣어서
- Precision / Recall / F1 측정
"""

import json
from ollama import chat
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix


# 1. test 데이터 로드

with open("data/ground_truth/test.json", "r", encoding="utf-8") as f:
    test_data = json.load(f)

print(f"테스트 데이터: {len(test_data)}개")
print(f"  Positive(1): {sum(1 for d in test_data if d['label']==1)}")
print(f"  Negative(0): {sum(1 for d in test_data if d['label']==0)}\n")



# 2. 현재 Qwen Binary Filter 판단 함수

def predict_relevance(query: str, chunk_text: str) -> int:
    """
    현재 LLMRerank와 동일한 방식으로 관련성 판단
    1 = 관련있음, 0 = 관련없음
    """
    prompt = (
        f"사용자 질문과 카드 혜택 정보가 관련있는지 판단하세요.\n"
        f"관련있으면 1, 관련없으면 0만 출력하세요.\n\n"
        f"사용자 질문: {query}\n\n"
        f"카드 혜택 정보:\n{chunk_text}\n\n"
        f"답변 (1 또는 0):"
    )

    try:
        response = chat(
            model="qwen2.5:7b",
            messages=[
                {
                    "role": "system",
                    "content": "당신은 카드 혜택과 사용자 질문의 관련성을 판단하는 전문가입니다. 반드시 1 또는 0만 출력하세요."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options={"temperature": 0.0}
        )

        result = response.message.content.strip()

        # 1 또는 0 추출
        if "1" in result:
            return 1
        else:
            return 0

    except Exception as e:
        print(f"오류: {e}")
        return 0



# 3. 전체 테스트 실행

print("=== Before LoRA 성능 측정 시작 ===\n")

y_true = []  # 정답
y_pred = []  # 예측

for i, sample in enumerate(test_data):
    pred = predict_relevance(sample["query"], sample["chunk_text"])
    y_true.append(sample["label"])
    y_pred.append(pred)

    # 진행상황 출력
    if (i + 1) % 10 == 0:
        print(f"진행: {i+1}/{len(test_data)}")


# 4. 지표 계산

precision = precision_score(y_true, y_pred, zero_division=0)
recall    = recall_score(y_true, y_pred, zero_division=0)
f1        = f1_score(y_true, y_pred, zero_division=0)
cm        = confusion_matrix(y_true, y_pred)

print("\n" + "="*40)
print("=== Before LoRA 측정 결과 ===")
print("="*40)
print(f"Precision : {precision:.4f}  ({precision*100:.1f}%)")
print(f"Recall    : {recall:.4f}  ({recall*100:.1f}%)")
print(f"F1 Score  : {f1:.4f}  ({f1*100:.1f}%)")
print()
print("Confusion Matrix:")
print(f"  TN={cm[0][0]}  FP={cm[0][1]}")
print(f"  FN={cm[1][0]}  TP={cm[1][1]}")
print()
print("해석:")
print(f"  TP(맞게 통과): {cm[1][1]}  → 관련있는 카드를 맞게 통과시킨 것")
print(f"  FP(잘못 통과): {cm[0][1]}  → ⚠️관련없는 카드를 통과시킨 것 ")
print(f"  TN(맞게 차단): {cm[0][0]}  → 관련없는 카드를 맞게 걸러낸 것")
print(f"  FN(잘못 차단): {cm[1][0]}  → ⚠️관련있는 카드를 걸러낸 것 ")

# 결과 저장 (After LoRA 비교용)
result = {
    "model": "Qwen2.5-7B (Before LoRA)",
    "precision": round(precision, 4),
    "recall": round(recall, 4),
    "f1": round(f1, 4),
    "confusion_matrix": cm.tolist(),
    "total_samples": len(test_data)
}

with open("result_before.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("\n결과 저장: result_before.json")