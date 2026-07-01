#  💳 거래 데이터 기반 Context-Aware RAG 시스템 



> 내 소비 패턴에 딱 맞는 카드, AI가 찾아드립니다 

<br>

## 1. 프로젝트 개요

기존 서비스는 단순 인기순 나열 또는 수동 카테고리 선택에 의존하여
개인의 실제 소비 패턴을 정밀하게 반영하지 못하는 한계가 있습니다.
본 프로젝트는 실제 거래 내역을 기반으로 소비 리포트를 생성하고,
RAG 파이프라인으로 맞춤형 카드를 추천하는 것을 목표로 합니다.
 
|  | 기존 방식 | 제안 방식 |
|------|-----------|-----------|
| 정보 접근성 | 카드사별 웹사이트 직접 탐색 | 자연어 질의로 즉시 접근 |
| 비교 분석 | 사용자가 직접 대조 | 거래 데이터 기반 자동 매칭 |
| 개인화 | 범용적 혜택 안내 | 소비 패턴 기반 맞춤 추천 |

---

## 2. 기술 스택

| 영역 | 기술 |
|------|------|
| Backend | FastAPI, Spring |
| Vector DB | Qdrant (Hybrid Search) |
| Embedding | BAAI/bge-m3  |
| Reranker | BAAI/bge-reranker-v2-m3 |
| SLM | Qwen 2.5 (Ollama 로컬 실행) |
| LLM | GPT-4o-mini |
| OCR | PyMuPDF + CLOVA OCR |
| API | Codef API |


---

##  3. 시스템 아키텍처
<img width="628" height="415" alt="image" src="https://github.com/user-attachments/assets/b38666cd-739f-4d59-9d3c-c1d5a1b252aa" />

**메타데이터 설계**
- card_name, card_type 구조화로 신용/체크 카드 사전 필터링
- overlap 청킹 적용으로 문맥 손실 최소화

---
##  4. 파이프라인 선택

### LLM-as-a-Judge 테스트

| | Hybrid | Hybrid+Reranker | Hybrid+SLM+Reranker |
|--|--|--|--|
| Hybrid 검색 수 | 30개 | 30개 | 30개 |
| SLM 필터 | - | - | top 10 추출 |
| Reranker | top 5 추출 | top 5 추출 | top 5 추출 |

정량 평가의 한계(다차원 추천 특성, 이진 평가 불가)로 인해 Gemini를 평가자로 사용하여 4개 지표(소스 충실도,쿼리 의도,리포트 반영,조건 정확성)로 상호 대조 평가

> 카드 추천은 반복적이지 않은 일회성 서비스로 속도보다 정확도가 중요하다고 판단,
> **최종 선택: Hybrid + SLM + Reranker**

---
## 5. 최종 UI
<img width="540" height="380" alt="image" src="https://github.com/user-attachments/assets/36b368fd-8e0e-464f-ba73-2b1ac280429c" />
<img width="540" height="380" alt="image" src="https://github.com/user-attachments/assets/9aa23bb2-d0f0-40b3-ae0f-13c7e70c65d4" />
<img width="540" height="380" alt="image" src="https://github.com/user-attachments/assets/abbc2ab5-3e05-4325-9497-9c640a6cf71a" />
<img width="540" height="380" alt="image" src="https://github.com/user-attachments/assets/e8c90aca-eab5-4925-a13c-c7f9530ac139" />


## 🎬 데모 영상
  소비패턴 반영 모드  [영상](https://drive.google.com/file/d/1H9jBrbgkDxLSGWRUz0ZoPsM6mVR2EYBJ/view?usp=sharing) 


---
