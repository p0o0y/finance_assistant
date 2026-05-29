import json, os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
)

all_chunks = []
offset = None
while True:
    results, offset = client.scroll(
        collection_name="card_benefits",
        limit=100, offset=offset,
        with_payload=True, with_vectors=False
    )
    all_chunks.extend(results)
    if offset is None:
        break

print(f"총 {len(all_chunks)}개 청크")

# 텍스트 추출
def get_node_text(chunk):
    payload = chunk.payload
    if "_node_content" in payload:
        try:
            node_content = json.loads(payload["_node_content"])
            return node_content.get("text", "")
        except:
            return str(payload["_node_content"])
    return payload.get("text", payload.get("content", ""))

output = []
for i, chunk in enumerate(all_chunks):
    text = get_node_text(chunk)
    if not text or len(text) < 50:
        continue
    output.append({
        "chunk_id": i,
        "card_name": chunk.payload.get("card_name", "unknown"),
        "card_type": chunk.payload.get("card_type", "unknown"),
        "chunk_text": text
    })

with open("data/chunks_only.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"저장 완료: {len(output)}개 청크 → data/chunks_only.json")