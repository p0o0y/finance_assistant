

import json, os, re, asyncio
from concurrent.futures import ThreadPoolExecutor
from time import time
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"))

import torch
from llama_index.core import VectorStoreIndex, QueryBundle
from llama_index.core.schema import NodeWithScore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.postprocessor import SentenceTransformerRerank, LLMRerank
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core.vector_stores import MetadataFilters, MetadataFilter
from qdrant_client import QdrantClient

SCENARIO_PATH = os.path.join(BASE_DIR, "ch01", "data", "ground_truth", "hit_at_k_scenarios.json")
RESULT_PATH   = os.path.join(BASE_DIR, "ch01", "data", "ground_truth", "results_hit_at_k.json")

CARD_NAME_MAP = {
    "BC 밥바라밥 페이북머니 체크카드":      "BC_밥바라밥_체크카드",
    "KB ALL 카드":                          "KB_ALL카드_신용카드",
    "KB WE:SH All+ 카드":                  "KB_WESHALL_신용카드",
    "KB WE:SH Daily 카드":                 "KB_WESHDAILY_신용카드",
    "KB Youth Club 체크카드":              "KB_YouthClub_체크카드",
    "KB 국민노리2 체크카드":               "KB_국민노리2_체크카드",
    "KB 트래블러스 체크카드":              "KB_트래블러스_체크카드",
    "MG 더나은 체크카드":                  "MG_더나은_체크카드",
    "신한 K-패스 체크카드":                "신한_K-패스_체크카드",
    "신한 SOL트래블 체크카드":             "신한_SOL트래블_체크카드",
    "신한 Simple Plan 신용카드":           "신한_Simple Plan_신용카드",
    "신한 Simple Plan+ 신용카드":          "신한_Simple Plan+_신용카드",
    "신한 나라사랑카드 체크카드":          "신한_나라사랑카드_체크카드",
    "신한 처음 체크카드":                  "신한_처음_체크카드",
    "우리 UniMile 신용카드":               "우리_UniMile_신용카드",
    "우리 오하CHECK 체크카드":             "우리_오하CHECK_체크카드",
    "우리 위비트래블 체크카드":            "우리_위비트래블_체크카드",
    "우리 카드의정석 SHOPPING+ 신용카드":  "우리_카드의정석SHOPPING+_신용카드",
    "하나 Jade Classic 신용카드":          "하나_Jade_신용카드",
    "하나 트래블로그 신용카드":            "하나_트래블로그_신용카드",
    "하나 트래블로그 체크카드":            "하나_트래블로그_체크카드",
}

CREDIT_CARDS = {
    "KB ALL 카드", "KB WE:SH All+ 카드", "KB WE:SH Daily 카드",
    "신한 Simple Plan 신용카드", "신한 Simple Plan+ 신용카드",
    "우리 UniMile 신용카드", "우리 카드의정석 SHOPPING+ 신용카드",
    "하나 Jade Classic 신용카드", "하나 트래블로그 신용카드",
}
CHECK_CARDS = {
    "BC 밥바라밥 페이북머니 체크카드", "KB Youth Club 체크카드",
    "KB 국민노리2 체크카드", "KB 트래블러스 체크카드", "MG 더나은 체크카드",
    "신한 K-패스 체크카드", "신한 SOL트래블 체크카드",
    "신한 나라사랑카드 체크카드", "신한 처음 체크카드",
    "우리 오하CHECK 체크카드", "우리 위비트래블 체크카드",
    "하나 트래블로그 체크카드",
}

device = "cuda" if torch.cuda.is_available() else "cpu"
embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-m3", device=device)

qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=60.0
)

vector_store = QdrantVectorStore(
    client=qdrant_client,
    collection_name="card_benefits",
    enable_hybrid=True,
    fastembed_sparse_model="Qdrant/bm25"
)
index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)

slm_model = Ollama(model="qwen2.5:7b", request_timeout=60.0)
slm_filter = LLMRerank(llm=slm_model, top_n=15, choice_batch_size=5)

reranker = SentenceTransformerRerank(
    model="BAAI/bge-reranker-v2-m3", top_n=5, device=device
)

executor = ThreadPoolExecutor(max_workers=2)


def get_filters(query: str):
    if "신용" in query:
        return MetadataFilters(filters=[MetadataFilter(key="card_type", value="신용카드")])
    elif "체크" in query:
        return MetadataFilters(filters=[MetadataFilter(key="card_type", value="체크카드")])
    return None


async def search(query: str, user_report: str, mode: str, top_k: int = 5):
    enriched_query = f"사용자 소비 리포트: {user_report}\n질문: {query}"
    query_bundle = QueryBundle(enriched_query)
    filters = get_filters(query)

    if mode == "sparse":
        retriever = index.as_retriever(
            similarity_top_k=top_k,
            vector_store_query_mode="sparse",
            filters=filters
        )
        nodes = retriever.retrieve(query_bundle)

    elif mode == "dense":
        retriever = index.as_retriever(
            similarity_top_k=top_k,
            vector_store_query_mode="default",
            filters=filters
        )
        nodes = retriever.retrieve(query_bundle)

   
    else:  # hybrid, hybrid_rerank, hybrid_slm_rerank
        retriever = index.as_retriever(
            similarity_top_k=30,  
            sparse_top_k=30,
            vector_store_query_mode="hybrid",
            filters=filters
        )
        nodes = retriever.retrieve(query_bundle)

    loop = asyncio.get_running_loop()

    if mode == "hybrid_slm_rerank":
        try:
            slm_filter.top_n = 15
            nodes = await loop.run_in_executor(
                executor,
                lambda: slm_filter.postprocess_nodes(nodes, query_bundle)
            )
        except Exception as e:
            print(f"SLM 필터 오류: {e}")
            nodes = nodes[:20]

    #  Cross-Encoder Reranking
    if mode in ["hybrid_rerank", "hybrid_slm_rerank"]:
        try:
            nodes = await loop.run_in_executor(
                executor,
                lambda: reranker.postprocess_nodes(nodes, query_bundle)
            )
        except Exception as e:
            nodes = nodes[:top_k]

    card_names = []
    for node in nodes[:top_k]:
        name = node.metadata.get("card_name", "")
        if not name:
            match = re.match(r'\[(.+?)\]', node.node.text)
            name = match.group(1).strip() if match else "unknown"
        if name not in card_names and name != "unknown":
            card_names.append(name)

    return card_names[:top_k]

def normalize(name: str) -> str:
    return re.sub(r'[\s\-_()\[\]+:.]', '', name).lower()

def is_match(retrieved: str, answer: str) -> bool:
    r = normalize(retrieved)
    if normalize(answer) in r or r in normalize(answer):
        return True
    db_name = CARD_NAME_MAP.get(answer, "")
    if db_name and (normalize(db_name) in r or r in normalize(db_name)):
        return True
    return False


# Hit@K 평가

async def evaluate(scenarios, mode: str, k: int = 5, card_filter: str = "all"):
    hits = []
    latencies = []
    print_lock = asyncio.Lock()

    for s in scenarios:
        tier1 = s["relevant_cards"]["tier1"]

        if card_filter == "credit":
            tier1 = [c for c in tier1 if c in CREDIT_CARDS]
        elif card_filter == "check":
            tier1 = [c for c in tier1 if c in CHECK_CARDS]

        if not tier1:
            continue

        start_time = time.perf_counter()
        retrieved = await search(s["query"], s["user_report"], mode, top_k=k)
        end_time = time.perf_counter()

        latencies.append(end_time - start_time)
        hit = 0
        for ans in tier1:
            for ret in retrieved:
                if is_match(ret, ans):
                    hit = 1
                    break
            if hit:
                break
        hits.append(hit)
        label = "✅" if hit else "🔴"
        top_5_str = ", ".join(retrieved[:5]) if retrieved else "none"
        async with print_lock: 
            print(f"  [{label}] #{s['scenario_id']:2d} ({end_time - start_time:.2f}초) - 정답: {tier1[0][:15]:<15} | 추천 Top5: [{top_5_str}]")
    
    avg_hit = (sum(hits) / len(hits)) if hits else 0.0
    avg_latency = (sum(latencies) / len(latencies)) if latencies else 0.0
    return avg_hit, avg_latency 


async def main():
    with open(SCENARIO_PATH, "r", encoding="utf-8") as f:
        scenarios = json.load(f)

    print(f"총 {len(scenarios)}개")
  
    modes = [
        ("sparse",            "BM25"),
        ("dense",             "Dense"),
        ("hybrid",            "Hybrid"),
        ("hybrid_rerank",     "Hybrid+Reranker"),
        ("hybrid_slm_rerank", "Hybrid+SLM+Reranker"),  
    ]

    results = {}

    for mode_key, mode_name in modes:
        print(f"\n{'='*60}")
        is_current = mode_key == "hybrid_slm_rerank"
        print(f"[{mode_name}]{' 현재 시스템' if is_current else ''}")
        print('='*60)

        print("\n-----[1]전체-----")
        h_all, t_all = await evaluate(scenarios, mode_key, k=5, card_filter="all")

        print("\n-----[2]신용카드----")
        h_credit, t_credit = await evaluate(scenarios, mode_key, k=5, card_filter="credit")

        print("\n-----[3]체크카드-----")
        h_check, t_check = await evaluate(scenarios, mode_key, k=5, card_filter="check")

        results[mode_name] = {
            "전체 Hit@5": round(h_all,4),"전체 시간": round(t_all, 2),
            "신용카드 Hit@5": round(h_credit,4), "신용 시간": round(t_credit, 2),
            "체크카드 Hit@5": round(h_check,4), "체크 시간": round(t_check, 2),
        }

    print("\n\n" + "="*95)
    print("--------------------------------- 최종 실험 성적표 ---------------------------------")
    print("="*95)
    print(f"{'평가 대상 방법론 (Method)':<24} {'전체 Hit':>10} {'전체 시간':>10}  |  {'신용 Hit':>10} {'신용 시간':>10}  |  {'체크 Hit':>10} {'체크 시간':>10}")
    print("-"*95)

    for name, res in results.items():
        print(
            f"{name:<25} "
            f"{res['전체 Hit@5']*100:>8.1f}% {res['전체 시간']:>8.2f}s  |  "
            f"{res['신용카드 Hit@5']*100:>8.1f}% {res['신용 시간']:>8.2f}s  |  "
            f"{res['체크카드 Hit@5']*100:>8.1f}% {res['체크 시간']:>8.2f}s"
        )

    os.makedirs(os.path.dirname(RESULT_PATH), exist_ok=True)
    
    with open(RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n결과 저장: {RESULT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())