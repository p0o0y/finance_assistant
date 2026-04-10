import pickle

# 1. 파일 열기 (rb: Read Binary 모드)
with open("../data/nodes.pkl", "rb") as f:
    nodes = pickle.load(f)

# 2. 전체 요약 보기
print(f"📊 총 노드 개수: {len(nodes)}개")
print("-" * 50)

# 3. 첫 번째 노드 내용 상세 확인
if nodes:
    sample_node = nodes[0]
    print(f"[노드 ID] {sample_node.id_}")
    print(f"[메타데이터] {sample_node.metadata}")
    print(f"[텍스트 일부]\n{sample_node.text[:555]}...") # 너무 길어서 200자만 출력
    print("-" * 50)

# 4. 카드별로 몇 개의 조각이 생겼는지 확인
card_counts = {}
for node in nodes:
    name = node.metadata.get("card_name", "Unknown")
    card_counts[name] = card_counts.get(name, 0) + 1

print("📇 카드별 노드 생성 현황:")
for name, count in card_counts.items():
    print(f" - {name}: {count}개 조각")