import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
import subprocess
import time 
from typing import Any, Dict, List
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
set_global_handler("simple") 
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
slm_model = Ollama(model="qwen2.5:7b", request_timeout=60.0, system_prompt="You are a Korean financial product expert. Always respond in Korean.")
slm_filter = LLMRerank(llm=slm_model, top_n=10, choice_batch_size=5)


reranker = SentenceTransformerRerank(
    model="BAAI/bge-reranker-v2-m3",top_n=5,device="cuda:0"
)

# gpt-4o-mini
final_llm = OpenAI(model="gpt-4o-mini")

executor = ThreadPoolExecutor(max_workers=4) 


# ── VRAM 측정 유틸 ──────────────────────────────────────────
def get_nvidia_smi_vram():
    """nvidia-smi로 전체 GPU VRAM 사용량 반환 (MB)"""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True
        )
        used, total = result.stdout.strip().split(", ")
        return float(used), float(total)
    except Exception:
        return 0.0, 0.0


# ── SLM 필터 (nvidia-smi로 VRAM 측정) ──────────────────────
def _run_slm_filter(nodes, query_bundle):
    vram_before, total = get_nvidia_smi_vram()
    t = time.perf_counter()

    result = slm_filter.postprocess_nodes(nodes, query_bundle)

    elapsed = time.perf_counter() - t
    vram_after, _ = get_nvidia_smi_vram()

    print(f"[측정] SLM 실행시간:    {elapsed:.4f}초 | {len(nodes)}개 → {len(result)}개")
    print(f"[측정] SLM VRAM 전:    {vram_before:.1f}MB / {total:.1f}MB")
    print(f"[측정] SLM VRAM 후:    {vram_after:.1f}MB / {total:.1f}MB")
    print(f"[측정] SLM VRAM 증가:  {vram_after - vram_before:.1f}MB")
    return result


# ── Cross-Encoder 리랭커 (torch + nvidia-smi 동시 측정) ─────
def _run_reranker(nodes, query_bundle):
    # torch로 reranker 자체 VRAM 측정
    torch.cuda.reset_peak_memory_stats(device)
    vram_torch_before = torch.cuda.memory_allocated(device) / 1024**2

    #전체 GPU VRAM 측정
    vram_smi_before, total = get_nvidia_smi_vram()

    t = time.perf_counter()
    result = reranker.postprocess_nodes(nodes, query_bundle)
    elapsed = time.perf_counter() - t

    vram_torch_after = torch.cuda.memory_allocated(device) / 1024**2
    vram_torch_peak  = torch.cuda.max_memory_allocated(device) / 1024**2
    vram_smi_after, _ = get_nvidia_smi_vram()

    print(f"[측정] Cross-Encoder 실행시간:       {elapsed:.4f}초 | {len(nodes)}개 → {len(result)}개")
    print(f"[측정] Cross-Encoder torch VRAM 전:  {vram_torch_before:.1f}MB")
    print(f"[측정] Cross-Encoder torch VRAM 후:  {vram_torch_after:.1f}MB")
    print(f"[측정] Cross-Encoder torch VRAM 피크: {vram_torch_peak:.1f}MB") 
    print(f"[측정] Cross-Encoder smi VRAM 전:    {vram_smi_before:.1f}MB / {total:.1f}MB")
    print(f"[측정] Cross-Encoder smi VRAM 후:    {vram_smi_after:.1f}MB / {total:.1f}MB")
    print(f"[측정] Cross-Encoder smi VRAM 증가:  {vram_smi_after - vram_smi_before:.1f}MB")
    return result


class ChatRequest(BaseModel):
    query: str
    user_report: str = ""


@app.post("/ask")
async def ask_rag(request: ChatRequest):
    query = request.query
    user_report = request.user_report.strip()
    filters = None

    loop = asyncio.get_running_loop()
    if "신용" in query:
        filters = MetadataFilters(filters=[MetadataFilter(key="card_type", value="신용카드")])
    elif "체크" in query:
        filters = MetadataFilters(filters=[MetadataFilter(key="card_type", value="체크카드")])

    print(f"\n" + "="*60)
    print(f"사용자 Query: {query}")
    print("="*60)

    t0 = time.perf_counter()

    if user_report:
        enriched_query = f"사용자가 요구하는 질문: {query}{query}\n\n사용자 참고 소비 리포트:\n{user_report}"
        query_bundle = QueryBundle(enriched_query)

        vector_retriever = index.as_retriever(
            similarity_top_k=30,
            sparse_top_k=30,
            vector_store_query_mode="hybrid",
            filters=filters
        )

        # STEP 1
        try:
            initial_nodes: List[NodeWithScore] = vector_retriever.retrieve(query_bundle)
            print(f"[STEP1] Retrieval 완료 | 걸린시간: {time.perf_counter() - t0:.4f}초 | 후보: {len(initial_nodes)}개")
        except Exception as e:
            print(f"[STEP1] DB 검색 실패: {e}")
            initial_nodes = []

        current_nodes = initial_nodes

        # STEP 2
        # t2_start = time.perf_counter()
        # try:
        #     current_nodes = await loop.run_in_executor(
        #         executor,
        #         lambda: _run_slm_filter(current_nodes, query_bundle)
        #     )
        #     print(f"[STEP2] SLM Filter 완료 | 걸린시간: {time.perf_counter() - t2_start:.4f}초 | 남은 노드: {len(current_nodes)}개")
        # except Exception as e:
        #     print(f"[STEP2] 오류: {e}")
        #     current_nodes = current_nodes[:20]

        # STEP 3
        t3_start = time.perf_counter()
        try:
            print(f"[STEP3] Cross-Reranker 시작 | 후보 노드: {len(current_nodes)}개")
            current_nodes = await loop.run_in_executor(
                executor,
                lambda: _run_reranker(current_nodes, query_bundle)
            )
            print(f"[STEP3] Cross-Reranker 완료 | 걸린시간: {time.perf_counter() - t3_start:.4f}초 | 최종 노드: {len(current_nodes)}개")
        except Exception as e:
            print(f"[STEP3] 오류: {e}")
            current_nodes = current_nodes[:5]

        final_nodes = current_nodes

    # 일반 모드 
    else:
        print("[일반모드] 유저 질의 일반 모드 가동")
        query_bundle = QueryBundle(query)

        vector_retriever = index.as_retriever(
            similarity_top_k=15,
            sparse_top_k=15,
            vector_store_query_mode="hybrid",
            filters=filters
        )
        try:
            initial_nodes = vector_retriever.retrieve(query_bundle)
            print(f"[일반모드 STEP1] Retrieval 완료 | 걸린시간: {time.perf_counter() - t0:.4f}초 | 후보: {len(initial_nodes)}개")
        except Exception as e:
            print(f"[일반모드 STEP1] DB 검색 실패: {e}")
            initial_nodes = []

        if not initial_nodes:
            raise HTTPException(status_code=404, detail="관련된 카드 조건 정보를 찾을 수 없습니다.")

        final_nodes = initial_nodes[:4]

    
    if not final_nodes:
        raise HTTPException(status_code=404, detail="관련 카드를 찾을 수 없습니다.")

    t4_start = time.perf_counter()
    context_str = "\n".join([n.get_content() for n in final_nodes])

    if user_report:
        system_prompt = (
            f"당신은 금융 상품 추천자입니다. 실제 유저의 질문에 최대한 정확하고 유용한 정보를 제공하세요.\n"
            f"카드정보에 명시된 card_name과 실제 내용이 불일치하면 절대 포함하지 마세요.\n"
            f"'사용자 요구사항'과 '카드 정보'와 '사용자 소비 리포트'를 바탕으로 사용자의 소비패턴을 근거하여 2개정도의 카드로 답변하세요.\n"
            f"전월 실적 조건과 혜택 제외 대상까지 꼼꼼히 대조하여 정확한 정보만 제공하세요. 리포트에 없는 내용은 절대 절대 포함하지마세요.\n\n"
            f"해당 카드를 추천한 이유를 사용자 소비에 기반하여 설명하세요.\n\n"
            f"사용자 소비 리포트:\n{user_report}\n\n"
            f"카드 정보:\n{context_str}\n"
        )
    else:
        system_prompt = (
            f"당신은 카드혜택 pdf에서 정보를 분석합니다. 반드시 한국어로만 답변하세요.\n"
            f"아래 제공된 '카드 정보'를 극도로 꼼꼼하게 대조하여 사용자의 질문에 답변하세요.\n"
            f"특히 사용자가 '전월 실적', '혜택 제외 대상', '한도 조건' 등의 예외 처리를 물어본 경우, "
            f"문서에 적힌 수치와 예외 조항 텍스트를 왜곡 없이 있는 그대로 팩트만 전달해야 합니다.\n"
            f"만약 문서에 해당 내용이 명시되어 있지 않다면, 짐작해서 답변하지 말고 '확인이 어렵다'고 솔직하게 답하세요.\n\n"
            f"카드 정보:\n{context_str}\n"
        )

    try:
        response = final_llm.complete(f"{system_prompt}\n사용자의 요구사항: {query}\n답변:")
        answer = response.text
        t4_end = time.perf_counter()
        print(f"[STEP4] GPT 생성 완료 | 걸린시간: {t4_end - t4_start:.4f}초")
        print(f"[전체] 파이프라인 총 지연시간: {t4_end - t0:.4f}초")
        print("="*60 + "\n")
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