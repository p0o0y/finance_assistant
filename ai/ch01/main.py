import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
import pickle
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import torch
from llama_index.core import VectorStoreIndex, QueryBundle, set_global_handler
from llama_index.core.schema import NodeWithScore
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.core.postprocessor import LLMRerank
from llama_index.llms.openai import OpenAI
from llama_index.llms.ollama import Ollama
from llama_index.retrievers.bm25 import BM25Retriever


load_dotenv()
set_global_handler("simple") # 디버깅용 
app = FastAPI()


device = "cuda" if torch.cuda.is_available() else "cpu"
embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-m3", device=device)


vector_store = PGVectorStore.from_params(
    host=os.getenv("DB_HOST"), 
    port=os.getenv("DB_PORT"),
    database=os.getenv("DB_NAME"), 
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"), 
    table_name="financial_knowledge",
    embed_dim=1024,
    hybrid_search=True,
)
index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)
vector_retriever = index.as_retriever(similarity_top_k=60)

#  BM25
NODES_PATH = "./data/nodes.pkl"
bm25_retriever = None
if os.path.exists(NODES_PATH):
    with open(NODES_PATH, "rb") as f:
        nodes_from_pkl = pickle.load(f)
    bm25_retriever = BM25Retriever.from_defaults(
        nodes=nodes_from_pkl, 
        similarity_top_k=40
        )
    print(f" BM25 리트리버 준비 완료 (노드 수: {len(nodes_from_pkl)})")
else:
    print(" nodes.pkl이 존재하지 않습니다. dense 검색만 사용 ")
   

# slm binary filter 
slm_model = Ollama(model="qwen2.5:7b", request_timeout=60.0)
slm_filter = LLMRerank(
    llm=slm_model,
    top_n=15,     
    choice_batch_size=5 
)

# cross-encoder reranker
reranker = SentenceTransformerRerank(
    model="BAAI/bge-reranker-v2-m3",
      top_n=5,
      device=device
    ) 

# gpt-4o
final_llm = OpenAI(model="gpt-4o-mini")


# threadpoll 
executor = ThreadPoolExecutor(max_workers=2)

class ChatRequest(BaseModel):
    query: str
    user_report: str = ""

def _run_slm_filter(nodes,query_bundle):
    """slm필터링"""
    return slm_filter.postprocess_nodes(nodes, query_bundle)

def _run_reranker(nodes, query_bundle):
    """cross-encoder 리랭킹"""
    return reranker.postprocess_nodes(nodes, query_bundle)


@app.post("/ask")
async def ask_rag(request: ChatRequest):
    print(f"\n[요청] 질문: {request.query}")
    enriched_query = request.query
    if request.user_report:
        enriched_query = (
            f"사용자 요청: {request.query}\n"
            f"사용자 소비 패턴: {request.user_report}"
        )
    query_bundle = QueryBundle(enriched_query)
    
    # step 1 : hybrid retrieval 
    try:
        vector_nodes: List[NodeWithScore] = vector_retriever.retrieve(query_bundle)
        print(f"[의미 벡터] 검색 완료")
        for i, n in enumerate(vector_nodes[:3]):  # 상위 3
            print(f" 📜Dense Top{i+1}: score={round(n.score or 0, 4)} | {n.node.text[:400].strip()}")
    except Exception as e:
        print(f"벡터 검색 에러: {e}")
        vector_nodes = []

    try:
        bm25_nodes : List[NodeWithScore] =(
            bm25_retriever.retrieve(request.query)
            if bm25_retriever else []
        )
        print(f"[BM25] 검색 완료")
        for i, n in enumerate(bm25_nodes[:3]):  # 상위 3
            print(f" 📜 BM25 Top{i+1}: score={round(n.score or 0, 4)} | {n.node.text[:400].strip()}")
    
    except Exception as e:
        print(f"BM25 실패, Dense만 사용: {e}")
        bm25_nodes = []

    #  병합+중복 제거
    all_nodes_dict = {}
    for res in (vector_nodes + bm25_nodes):
        key = res.node.text[:100].strip()
        if key not in all_nodes_dict:
            all_nodes_dict[key] = res
    

    initial_nodes = list(all_nodes_dict.values())
    print(f"병합 : 총 {len(initial_nodes)}개 후보 (중복 제거)")

    # step 2 - SLM Binary Filter
    try:
        loop = asyncio.get_event_loop()
        filtered_nodes = await loop.run_in_executor(
            executor,
            lambda: _run_slm_filter(initial_nodes, query_bundle)
        )
        print(f"🌤️ [SLM Filter] {len(filtered_nodes)}개 추출")
        for i, n in enumerate(filtered_nodes):
            print(f" ✔️SLM [{i+1}]: score={round(n.score or 0, 4)} | 카드={n.metadata.get('card_name','?')} | {n.node.text[:500].strip()}")
   
    except Exception as e:
        print(f" SLM 필터 실패, 전체 후보 사용: {e}")
        filtered_nodes = initial_nodes[:20]  # fallback

    # step 3: Cross-Encoder Rerank 
    try:
        final_nodes = await loop.run_in_executor(
            executor,
            lambda: _run_reranker(filtered_nodes, query_bundle)
        )
        print(f"[Reranker] 최종 {len(final_nodes)}개 확정")
        for i, n in enumerate(final_nodes):
            print(f"  최종 [{i+1}]: score={round(n.score or 0, 4)} | 카드={n.metadata.get('card_name','?')} | {n.node.text[:80].strip()}")
    
    except Exception as e:
        print(f"Reranker 실패, SLM 결과 사용: {e}")
        final_nodes = filtered_nodes[:5]  # fallback

    # step 4- gpt 답변 생성 
    context_str = "\n".join([n.get_content() for n in final_nodes])
    
    system_prompt = (
        f"당신은 금융 상품 추천 전문가입니다. 아래 '추천 카드 정보'와 '사용자 소비'를 바탕으로 답변하세요.\n"
        f" 전월 실적 조건과 혜택 제외 대상까지도 꼼꼼히 대조하여 정확한 정보만 제공하세요.\n\n"
        f"사용자 소비 리포트: {request.user_report}\n"
        f"추천 카드 정보: {context_str}\n"
    )
    
    try:
        response = final_llm.complete(
            f"{system_prompt}\n\n질문: {request.query}\n답변:"
        )
        answer = response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM 응답 실패: {e}")

    return {
        "answer": answer,
        "source_nodes": [
            {
                "card_name": n.metadata.get("card_name", "unknown"),
                "score": round(float(n.score or 0.0), 4)
            }
            for n in final_nodes
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 



