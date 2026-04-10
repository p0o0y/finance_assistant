import os
import pickle
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import torch

# LlamaIndex 핵심 컴포넌트
from llama_index.core import VectorStoreIndex, QueryBundle, set_global_handler
from llama_index.core.schema import NodeWithScore
from llama_index.core.retrievers import BM25Retriever
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.postprocessor import LLMNodePostprocessor, SentenceTransformerRerank
from llama_index.llms.openai import OpenAI
from llama_index.llms.ollama import Ollama

# 설정 로드
load_dotenv()
set_global_handler("simple") # 디버깅용 로그 활성화
app = FastAPI()

# 1. 모델 및 장치 설정
device = "cuda" if torch.cuda.is_available() else "cpu"
embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-m3", device=device)

# 2. DB 및 인덱스 연결 (BGE-M3용)
vector_store = PGVectorStore.from_params(
    host=os.getenv("DB_HOST"), 
    port=os.getenv("DB_PORT"),
    database=os.getenv("DB_NAME"), 
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"), 
    table_name="financial_knowledge",
    hybrid_search=False 
)
index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)
vector_retriever = index.as_retriever(similarity_top_k=50)

# 3. BM25용 노드 로드 및 리트리버 설정 
NODES_PATH = "./data/nodes.pkl"
if os.path.exists(NODES_PATH):
    with open(NODES_PATH, "rb") as f:
        nodes_from_pkl = pickle.load(f)
    bm25_retriever = BM25Retriever.from_defaults(nodes=nodes_from_pkl, similarity_top_k=50)
    print(f" BM25 리트리버 준비 완료 (노드 수: {len(nodes_from_pkl)})")
else:
    print("존재하는 nodes.pkl이 없습니다.")
    bm25_retriever = None

# 4. 3-Step 고도화 컴포넌트
slm_model = Ollama(model="qwen2.5:3b", request_timeout=60.0)
reranker = SentenceTransformerRerank(model="BAAI/bge-reranker-v2-m3", top_n=4, device=device) # STEP 3: 정밀 리랭킹
slm_filter = LLMNodePostprocessor(
    llm=slm_model, 
    top_n=20  # 추출된 100개 중 Qwen이 보기에 진짜 괜찮은 20개만 남김
)
final_llm = OpenAI(model="gpt-4o") # 최종 답변 생성

class ChatRequest(BaseModel):
    query: str
    user_report: str = ""

@app.post("/ask")
async def ask_rag(request: ChatRequest):
    print(f"\n[로그] 질문 수신: {request.query}")
    query_bundle = QueryBundle(request.query)

    #  BGE-M3 Dense
    vector_nodes = vector_retriever.retrieve(query_bundle)
    
    # B. BM25 Sparse 
    bm25_nodes = []
    if bm25_retriever:
        bm25_nodes = bm25_retriever.retrieve(request.query)

    #  결과 병합 및 중복 제거
    all_nodes_dict = {}
    for res in (vector_nodes + bm25_nodes):
        all_nodes_dict[res.node.node_id] = res
    
    initial_nodes = list(all_nodes_dict.values())
    print(f"[로그] STEP 1 병합 완료: 총 {len(initial_nodes)}개 후보 추출")

    
    # SLM Binary Filter
    filtered_nodes = slm_filter.postprocess_nodes(initial_nodes, query_bundle)
    print(f"[로그] STEP 2 필터링 완료: {len(filtered_nodes)}개 잔류")

    # STEP 3: Cross-Encoder Rerank (Top 4)

    # 가장 정답에 가까운 4개를 최상단으로 재정렬
    final_nodes = reranker.postprocess_nodes(filtered_nodes, query_bundle)
    print(f"[로그] STEP 3 리랭킹 완료: 최종 4개 확정")

    # --------------------------------------------------
    # 최종 단계: 컨텍스트 결합 및 답변 생성
    # --------------------------------------------------
    context_str = "\n".join([n.get_content() for n in final_nodes])
    
    system_prompt = (
        f"당신은 금융 상품 추천 전문가입니다. 아래 제공된 '추천 카드 정보'와 '사용자 소비 리포트'를 바탕으로 답변하세요.\n"
        f"특히 전월 실적 조건과 혜택 제외 대상까지도 꼼꼼히 대조하여 정확한 정보만 제공하세요.\n\n"
        f"사용자 소비 리포트: {request.user_report}\n"
        f"추천 카드 정보: {context_str}\n"
    )
    
    response = final_llm.complete(f"{system_prompt}\n질문: {request.query}\n답변:")
    
    return {
        "answer": response.text,
        "source_nodes": [
            {"card_name": n.metadata.get("card_name"), "score": n.score} 
            for n in final_nodes
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)