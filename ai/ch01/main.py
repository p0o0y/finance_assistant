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
from llama_index.llms.openai import OpenAI
from qdrant_client import QdrantClient
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core.vector_stores import MetadataFilters, MetadataFilter
from offreport import router as report_router

load_dotenv()
set_global_handler("simple")
app = FastAPI()
app.include_router(report_router)

device = "cuda" if torch.cuda.is_available() else "cpu"

# 임베딩 모델 (BGE-M3)
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

reranker = SentenceTransformerRerank(model="BAAI/bge-reranker-v2-m3", top_n=5, device=device)

def _run_reranker(nodes, query_bundle):
    return reranker.postprocess_nodes(nodes, query_bundle)

final_llm = OpenAI(model="gpt-4o-mini")

executor = ThreadPoolExecutor(max_workers=2)

class ChatRequest(BaseModel):
    query: str
    user_report: str = ""


@app.post("/ask")
async def ask_rag(request: ChatRequest):
    query = request.query
    user_report = request.user_report.strip()
    filters = None

    if "신용" in query:
        filters = MetadataFilters(
            filters=[MetadataFilter(key="card_type", value="신용카드")]
        )
    elif "체크" in query:
        filters = MetadataFilters(
            filters=[MetadataFilter(key="card_type", value="체크카드")]
        )
        
    # 소비리포트 있을 경우 
    if user_report:
        enriched_query = f"사용자 소비 리포트:\n{user_report}\n\n질문: {query}"
        query_bundle = QueryBundle(enriched_query)

        vector_retriever = index.as_retriever(
            similarity_top_k=15,       
            sparse_top_k=15,            
            vector_store_query_mode="hybrid",
            filters=filters
        )   

        #  Hybrid Retrieval 
        try:
            initial_nodes: List[NodeWithScore] = vector_retriever.retrieve(query_bundle)
            print(f"-> 추천용 Hybrid Search 완료: {len(initial_nodes)}개 후보 추출")
            for i, n in enumerate(initial_nodes[:5]):
                print(f"   Top{i+1}: score={round(n.score or 0, 4)} | {n.node.text[:100].strip()}...")
        except Exception as e:
            print(f"DB 검색 에러: {e}")
            initial_nodes = []

   
        final_nodes = initial_nodes[:5]
        
    #소비리포트 없이 순수 유저 쿼리
    else:
        query_bundle = QueryBundle(query)

        vector_retriever = index.as_retriever(
            similarity_top_k=10, 
            sparse_top_k=10, 
            vector_store_query_mode="hybrid",
            filters=filters
        )
        try:
            initial_nodes = vector_retriever.retrieve(query_bundle)
            print(f" 유저 쿼리 검색용 Hybrid Search 완료: {len(initial_nodes)}개 후보 추출")
        except Exception as e:
            print(f"DB 검색 에러: {e}")
            initial_nodes = []
            
        if not initial_nodes:
            raise HTTPException(status_code=404, detail="관련된 카드 조건 정보를 찾을 수 없습니다.")
            
        try:
            loop = asyncio.get_running_loop()
            final_nodes = await loop.run_in_executor(
                executor,
                lambda: _run_reranker(initial_nodes, query_bundle)
            )
            print(f" Cross-Encoder 예외 조건 순위 재정렬 완료 (최종 {len(final_nodes)}개 확정)")
        except Exception as e:
            print(f"Reranker 실패, 하이브리드 순위 사용: {e}")
            final_nodes = initial_nodes[:5]

    if not final_nodes:
        raise HTTPException(status_code=404, detail="관련 카드를 찾을 수 없습니다.")

    context_str = "\n".join([n.get_content() for n in final_nodes])
    
    if user_report:
         system_prompt = (
            f"당신은 금융 상품 추천 전문가입니다. 반드시 한국어로만 답변하세요.\n"
            f"아래 '추천 카드 정보'와 '사용자 소비 리포트'를 바탕으로 답변하세요.\n"
            f"전월 실적 조건과 혜택 제외 대상까지 꼼꼼히 대조하여 정확한 정보만 제공하세요.\n\n"
            f"사용자 소비 리포트:\n{user_report}\n\n"
            f"추천 카드 정보:\n{context_str}\n"
        )
    else:
        system_prompt = (
            f"당신은 카드혜택 정보에대한 약관 및 혜택 조건 분석 전문가입니다. 반드시 한국어로만 답변하세요.\n"
            f"아래 제공된 '카드 정보'를 극도로 꼼꼼하게 대조하여 사용자의 질문에 답변하세요.\n"
            f"특히 사용자가 '전월 실적', '혜택 제외 대상', '한도 조건' 등의 예외 처리를 물어본 경우, "
            f"문서에 적힌 수치와 예외 조항 텍스트를 왜곡 없이 있는 그대로 팩트만 전달해야 합니다.\n"
            f"만약 문서에 해당 내용이 명시되어 있지 않다면, 짐작해서 답변하지 말고 '확인이 어렵다'고 솔직하게 답하세요.\n\n"
            f"카드 정보:\n{context_str}\n"
        )
    
    try:
        response = final_llm.complete(f"{system_prompt}\n질문: {query}\n답변:")
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