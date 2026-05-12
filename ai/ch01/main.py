import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import torch
from llama_index.core import VectorStoreIndex, QueryBundle, set_global_handler
from llama_index.core.schema import NodeWithScore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.core.postprocessor import LLMRerank
from llama_index.llms.openai import OpenAI
from llama_index.llms.ollama import Ollama
from qdrant_client import QdrantClient
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core.vector_stores import MetadataFilters, MetadataFilter
from offreport import router as report_router

load_dotenv()
set_global_handler("simple") # 디버깅용 
app = FastAPI()
app.include_router(report_router)
device = "cuda" if torch.cuda.is_available() else "cpu"
embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-m3", device=device)

qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
)

vector_store = QdrantVectorStore(
    client=qdrant_client,
    collection_name="card_benefits",
    enable_hybrid=True,
    fastembed_sparse_model="Qdrant/bm25"
)

index = VectorStoreIndex.from_vector_store(
    vector_store,
    embed_model=embed_model
)


# slm binary filter 
slm_model = Ollama(model="qwen2.5:7b", request_timeout=60.0,system="You are a Korean financial document filter. Always respond in Korean. Answer only with Doc numbers and relevance scores in the exact format requested.")
slm_filter = LLMRerank(llm=slm_model,top_n=15,     choice_batch_size=5 )

# cross-encoder reranker
reranker = SentenceTransformerRerank(model="BAAI/bge-reranker-v2-m3",top_n=5,device=device) 

# gpt-4o
final_llm = OpenAI(model="gpt-4o-mini")

executor = ThreadPoolExecutor(max_workers=2)

class ChatRequest(BaseModel):
    query: str
    user_report: str = ""

def _run_slm_filter(nodes,query_bundle):
    return slm_filter.postprocess_nodes(nodes, query_bundle)

def _run_reranker(nodes, query_bundle):
    return reranker.postprocess_nodes(nodes, query_bundle)


@app.post("/ask")
async def ask_rag(request: ChatRequest):

    query = request.query

    filters = None

    if "신용" in query:
        filters = MetadataFilters(
        filters=[MetadataFilter(key="card_type", value="신용카드")]
    )
    elif "체크" in query:
        filters = MetadataFilters(
        filters=[MetadataFilter(key="card_type", value="체크카드")]
    )
        
    vector_retriever = index.as_retriever(
        similarity_top_k=60,
        sparse_top_k=40,
        vector_store_query_mode="hybrid",
    )   

    print(f"\n[요청] 사용자 query: {request.query}")
    enriched_query = (f"사용자 소비 리포트: {request.user_report}\n" f"질문: {request.query}")
    query_bundle = QueryBundle(enriched_query)

    # step 1 : hybrid retrieval 
    try:
        initial_nodes: List[NodeWithScore] = vector_retriever.retrieve(query_bundle)
        print(f"Hybrid Search: {len(initial_nodes)}개 후보 ")
        for i, n in enumerate(initial_nodes[:3]):  # 상위 3
            print(f"   Top{i+1}: score={round(n.score or 0, 4)} | {n.node.text[:400].strip()}")
    except Exception as e:
        print(f"DB 검색 에러: {e}")
        initial_nodes = []

    # step 2 - SLM Binary Filter
    try:
        loop = asyncio.get_running_loop()
        filtered_nodes = await loop.run_in_executor(
            executor,
            lambda: _run_slm_filter(initial_nodes, query_bundle)
        )
        print(f"🌤️ [SLM Filter] {len(filtered_nodes)}개 추출")
        for i, n in enumerate(filtered_nodes):
            print(f"  SLM [{i+1}]: score={round(n.score or 0, 4)} | 카드={n.metadata.get('card_name','?')} | {n.node.text[:400].strip()}")

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
            print(f"  최종 [{i+1}]: score={round(n.score or 0, 4)} | 카드={n.metadata.get('card_name','?')} | {n.node.text[:500].strip()}")
    except Exception as e:
        print(f"Reranker 실패, SLM 결과 사용: {e}")
        final_nodes = filtered_nodes[:5]  # fallback

    # step 4- gpt 답변 생성 
    context_str = "\n".join([n.get_content() for n in final_nodes])
    system_prompt = (
        f"당신은 금융 상품 추천 전문가입니다. 반드시 한국어로만 답변하세요.\n"
        f"아래 '추천 카드 정보'와 '사용자 소비 리포트'를 바탕으로 답변하세요.\n"
        f"전월 실적 조건과 혜택 제외 대상까지 꼼꼼히 대조하여 정확한 정보만 제공하세요.\n\n"
        f"사용자 소비 리포트:\n{request.user_report}\n\n"
        f"추천 카드 정보:\n{context_str}\n"
    )
    
    try:
        response = final_llm.complete(
            f"{system_prompt}\n질문: {request.query}\n답변:"
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
