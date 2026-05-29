"""
Hit@5 평가 스크립트 - main.py 구조 그대로 반영
경로: ch01/evaluate/evaluate_hit_at_k.py
시나리오: ch01/data/ground_truth/hit_at_k_scenarios.json
"""

import json, os, re, asyncio
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ch01/
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

SCENARIO_PATH = os.path.join(BASE_DIR, "data", "ground_truth", "hit_at_k_scenarios.json")
RESULT_PATH   = os.path.join(BASE_DIR, "data", "ground_truth", "results_hit_at_k.json")

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
print(f"완료 (device={device})\n")


def get_filters(query: str):
    """main.py와 동일한 신용/체크 키워드 감지 필터"""
    if "신용" in query:
        return MetadataFilters(
            filters=[MetadataFilter(key="card_type", value="신용카드")]
        )
    elif "체크" in query:
        return MetadataFilters(
            filters=[MetadataFilter(key="card_type", value="체크카드")]
        )
    return None


async def search(query: str, user_report: str, mode: str, top_k: int = 5):
    enriched_query = f"사용자 소비 리포트: {user_report}\n질문: {query}"
    query_bundle = QueryBundle(enriched_query)

    filters = get_filters(query)

    if mode == "hybrid_slm_rerank":
        retrieve_k = 60
    elif mode == "hybrid_rerank":
        retrieve_k = 10
    else:
        retrieve_k = top_k


    if mode == "sparse":
        retriever = index.as_retriever(
            similarity_top_k=retrieve_k,
            vector_store_query_mode="sparse",
            filters=filters
        )
    elif mode == "dense":
        retriever = index.as_retriever(
            similarity_top_k=retrieve_k,
            vector_store_query_mode="default",
            filters=filters
        )
    else:  
        retriever = index.as_retriever(
            similarity_top_k=retrieve_k,
            sparse_top_k=40,
            vector_store_query_mode="hybrid",
            filters=filters
        )

    nodes = retriever.retrieve(query_bundle)

    loop = asyncio.get_running_loop()

    # SLM Filter (main.py와 동일: LLMRerank)
    if mode == "hybrid_slm_rerank":
        try:
            nodes = await loop.run_in_executor(
                executor,
                lambda: slm_filter.postprocess_nodes(nodes, query_bundle)
            )
        except Exception as e:
            print(f"    SLM 실패: {e}")
            nodes = nodes[:20]

    if mode in ["hybrid_rerank", "hybrid_slm_rerank"]:
        try:
            nodes = await loop.run_in_executor(
                executor,
                lambda: reranker.postprocess_nodes(nodes, query_bundle)
            )
        except Exception as e:
            print(f"    Reranker 실패: {e}")
            nodes = nodes[:top_k]

    card_names = []
    for node in nodes[:top_k]:
        name = node.metadata.get("card_name", "")
        if not name:
            match = re.match(r'\[(.+?)\]', node.node.text)
            name = match.group(1).strip() if match else "unknown"
        if name not in card_names:
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

    for s in scenarios:
        tier1 = s["relevant_cards"]["tier1"]
        if card_filter == "credit":
            tier1 = [c for c in tier1 if c in CREDIT_CARDS]
        elif card_filter == "check":
            tier1 = [c for c in tier1 if c in CHECK_CARDS]
        if not tier1:
            continue
        retrieved = await search(s["query"], s["user_report"], mode, top_k=k)
        hit = 0
        for ans in tier1:
            for ret in retrieved:
                if is_match(ret, ans):
                    hit = 1
                    break
            if hit:
                break
        hits.append(hit)
        label = "✅" if hit else "X"
        print(f"  [{label}] #{s['scenario_id']:2d} - 정답: {tier1[0][:22]:<22} | 검색1: {retrieved[0][:22] if retrieved else 'none'}")

    return (sum(hits) / len(hits)) if hits else 0.0


async def main():
    with open(SCENARIO_PATH, "r", encoding="utf-8") as f:
        scenarios = json.load(f)

    print(f"총 {len(scenarios)}개")
    credit_count = sum(1 for s in scenarios if any(c in CREDIT_CARDS for c in s["relevant_cards"]["tier1"]))
    check_count  = sum(1 for s in scenarios if any(c in CHECK_CARDS  for c in s["relevant_cards"]["tier1"]))
    print(f"  신용카드 tier1 포함: {credit_count}개")
    print(f"  체크카드 tier1 포함: {check_count}개\n")

    modes = [
        ("sparse",            "BM25 단독"),
        ("dense",             "Dense 단독"),
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

        print("\n전체")
        h_all = await evaluate(scenarios, mode_key, k=5, card_filter="all")

        print("\n신용카드")
        h_credit = await evaluate(scenarios, mode_key, k=5, card_filter="credit")

        print("\n체크카드")
        h_check = await evaluate(scenarios, mode_key, k=5, card_filter="check")

        results[mode_name] = {
            "전체 Hit@5":     round(h_all,4),
            "신용카드 Hit@5": round(h_credit,4),
            "체크카드 Hit@5": round(h_check,4),
        }

    # 결과 출력
    print("\n\n" + "="*70)
    print("--------최종 결과------")
    print("="*70)
    print(f"{'방법':<26} {'전체 Hit@5':>12} {'신용 Hit@5':>12} {'체크 Hit@5':>12}")
    print("-"*66)
    for name, res in results.items():
        marker = " ★" if name == "Hybrid+SLM+Reranker" else ""
        print(
            f"{name+marker:<28}"
            f"{res['전체 Hit@5']*100:>11.1f}%"
            f"{res['신용카드 Hit@5']*100:>11.1f}%"
            f"{res['체크카드 Hit@5']*100:>11.1f}%"
        )

    os.makedirs(os.path.dirname(RESULT_PATH), exist_ok=True)
    with open(RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n결과 저장: {RESULT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())