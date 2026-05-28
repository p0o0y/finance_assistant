
import json, random, os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
)

print("Qdrant 청크 로딩 중")
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
print(f"총 {len(all_chunks)}개 청크\n")


# 카테고리 키워드 (PDF 실제 텍스트 기반)

CATEGORY_KEYWORDS = {
    "카페": [
        "스타벅스","커피빈","투썸","이디야","메가커피","빽다방","컴포즈","매머드",
        "폴바셋","사이렌오더","커피전문점","카페","투썸플레이스","메가MGC"
    ],
    "편의점": [
        "GS25","CU","세븐일레븐","이마트24","편의점","씨유"
    ],
    "쇼핑": [
        "무신사","29CM","29cm","올리브영","지그재그","에이블리","W컨셉","쿠팡",
        "SSG","롯데ON","더현대","온라인쇼핑","쇼핑몰","오늘의집","야놀자","LOHB"
    ],
    "배달": [
        "배달의민족","쿠팡이츠","요기요","배달앱","B마트","컬리","마켓컬리","배달"
    ],
    "교통": [
        "버스","지하철","택시","철도","KTX","교통","카카오T","UT","후불교통",
        "대중교통","시내버스","시외버스","공항버스","ITX","새마을"
    ],
    "OTT": [
        "넷플릭스","유튜브","티빙","웨이브","디즈니플러스","스포티파이","멜론",
        "지니","FLO","OTT","구독","디즈니","유튜브 프리미엄"
    ],
    "주거통신": [
        "SKT","KT","LG U+","통신","이동통신","알뜰폰","LiivM","통신요금",
        "자동납부","SK텔레콤","헬로모바일","KTM모바일"
    ],
    "여가": [
        "대한항공","아시아나","제주항공","진에어","티웨이","이스타","에어부산",
        "하나투어","면세점","에버랜드","롯데월드","CGV","롯데시네마","메가박스",
        "라운지","공항라운지","항공","여행","호텔","아고다","익스피디아",
        "호텔스닷컴","신라면세점","롯데면세점","신세계면세점","서울랜드","캐리비안베이",
        "인터파크","YES24","티켓링크","공연","노래방","PC방"
    ],
    "마트": [
        "이마트","홈플러스","롯데마트","다이소","트레이더스","마트","슈퍼",
        "백화점","롯데백화점","신세계","현대백화점","아울렛","이케아","GS수퍼"
    ],
    "병원": [
        "병원","의원","약국","치과","의료","한방병원","동물병원"
    ],
    "주유": [
        "SK주유","GS칼텍스","S-OIL","현대오일","주유","주유소","LPG","충전소"
    ],
    "교육": [
        "독서실","도서","문구","서적","스터디","학원","알라딘","YES24",
        "스터디카페","TOEIC","OPIc","TOEFL","HSK","어학"
    ],
    "해외": [
        "해외","수수료 면제","외화","트래블","해외가맹","ATM","해외이용",
        "현지통화","외화하나머니","해외 수수료","국제브랜드 수수료"
    ],
    "간편결제": [
        "삼성페이","네이버페이","카카오페이","PAYCO","페이코","KB Pay",
        "하나페이","우리페이","SSG페이","쿠페이","SK페이","간편결제"
    ],
}


# 쿼리 템플릿 (100개+, PDF 실제 혜택 기반)

QUERY_TEMPLATES = [
    # ── 카페 ──
    {"query": "스타벅스 자주 가는데 할인 되는 카드 뭐야?", "target": ["카페"]},
    {"query": "커피 많이 마셔서 카페 혜택 좋은 카드 추천해줘", "target": ["카페"]},
    {"query": "이디야, 메가커피 할인 되는 카드 있어?", "target": ["카페"]},
    {"query": "투썸플레이스 자주 가는데 적립 카드 추천해줘", "target": ["카페"]},
    {"query": "카페 갈 때마다 아깝던데 카페 캐시백 카드 알려줘", "target": ["카페"]},
    {"query": "스타벅스 사이렌오더 쓰는데 혜택 있는 카드 있어?", "target": ["카페"]},
    {"query": "빽다방이나 컴포즈 자주 가는데 할인 카드 뭐야?", "target": ["카페"]},
    {"query": "카페 지출이 많은데 커피전문점 특화 카드 뭐가 있어?", "target": ["카페"]},

    # ── 편의점 ──
    {"query": "편의점 GS25, CU 자주 가는데 할인 카드 뭐야?", "target": ["편의점"]},
    {"query": "편의점 매일 들르는데 혜택 있는 체크카드 추천해줘", "target": ["편의점"]},
    {"query": "세븐일레븐 이마트24 할인 되는 카드 있어?", "target": ["편의점"]},
    {"query": "편의점에서 KB Pay 쓰면 할인 되는 카드 알려줘", "target": ["편의점"]},
    {"query": "편의점 행사상품 즉시할인 되는 카드 뭐야?", "target": ["편의점"]},
    {"query": "CU에서 할인 잘 되는 카드 추천해줘", "target": ["편의점"]},

    # ── 쇼핑 ──
    {"query": "무신사, 29CM 자주 쓰는데 쇼핑 할인 카드 추천해줘", "target": ["쇼핑"]},
    {"query": "올리브영 많이 가는데 혜택 있는 카드 뭐야?", "target": ["쇼핑"]},
    {"query": "온라인 쇼핑 많이 하는데 쿠팡 할인 카드 알려줘", "target": ["쇼핑"]},
    {"query": "지그재그, 에이블리 자주 쓰는데 패션앱 할인 카드 있어?", "target": ["쇼핑"]},
    {"query": "W컨셉, 29CM 같은 패션 플랫폼 할인 카드 뭐야?", "target": ["쇼핑"]},
    {"query": "SSG닷컴, 롯데ON 쇼핑몰 많이 쓰는데 할인 카드 추천해줘", "target": ["쇼핑"]},
    {"query": "온라인 쇼핑 캐시백 많이 주는 카드 알려줘", "target": ["쇼핑"]},
    {"query": "오늘의집이나 야놀자 할인 되는 카드 있어?", "target": ["쇼핑"]},
    {"query": "쇼핑 멤버십 쿠팡 로켓와우 할인 카드 뭐야?", "target": ["쇼핑"]},

    # ── 배달 ──
    {"query": "배달의민족 자주 쓰는데 배달 할인 카드 추천해줘", "target": ["배달"]},
    {"query": "배달 앱 많이 쓰는데 쿠팡이츠 할인되는 카드 있어?", "target": ["배달"]},
    {"query": "요기요, 배달의민족 자주 시키는데 배달비 아낄 카드 뭐야?", "target": ["배달"]},
    {"query": "컬리 마켓컬리 자주 쓰는데 캐시백 카드 추천해줘", "target": ["배달"]},
    {"query": "B마트 자주 이용하는데 혜택 있는 카드 알려줘", "target": ["배달"]},
    {"query": "배달앱 월 몇 만원씩 쓰는데 적립 카드 뭐가 좋아?", "target": ["배달"]},

    # ── 교통 ──
    {"query": "대중교통 매일 타는데 버스 지하철 할인 카드 알려줘", "target": ["교통"]},
    {"query": "출퇴근 지하철 많이 타는데 교통비 아낄 카드 추천", "target": ["교통"]},
    {"query": "택시 자주 타는데 카카오T 할인 카드 있어?", "target": ["교통"]},
    {"query": "KTX 자주 타는데 철도 할인 카드 뭐야?", "target": ["교통"]},
    {"query": "후불교통 기능 있는 카드 중에 혜택 좋은 거 추천해줘", "target": ["교통"]},
    {"query": "시외버스 고속버스 자주 타는데 할인 카드 알려줘", "target": ["교통"]},
    {"query": "교통비 10% 이상 할인 되는 체크카드 뭐야?", "target": ["교통"]},
    {"query": "UT 택시 카카오T 할인 되는 카드 추천해줘", "target": ["교통"]},

    # ── OTT ──
    {"query": "넷플릭스, 유튜브 구독 중인데 OTT 할인 카드 있어?", "target": ["OTT"]},
    {"query": "매달 OTT 구독비 나가는데 할인되는 카드 알려줘", "target": ["OTT"]},
    {"query": "티빙, 웨이브 구독 중인데 OTT 캐시백 카드 뭐야?", "target": ["OTT"]},
    {"query": "스포티파이, 멜론 구독료 할인 카드 추천해줘", "target": ["OTT"]},
    {"query": "디즈니플러스 유튜브 프리미엄 자동납부 할인 카드 알려줘", "target": ["OTT"]},
    {"query": "OTT 구독 많이 하는데 한 번에 할인 되는 카드 있어?", "target": ["OTT"]},
    {"query": "넷플릭스 50% 할인 되는 카드 뭐야?", "target": ["OTT"]},

    # ── 주거통신 ──
    {"query": "통신비 자동납부 할인 되는 카드 뭐야?", "target": ["주거통신"]},
    {"query": "KT 요금 매달 나가는데 통신비 할인 카드 알려줘", "target": ["주거통신"]},
    {"query": "SKT LG U+ 이동통신 요금 할인 카드 추천해줘", "target": ["주거통신"]},
    {"query": "알뜰폰 요금제 쓰는데 통신비 캐시백 카드 있어?", "target": ["주거통신"]},
    {"query": "핸드폰 요금 자동납부 하는데 할인 카드 뭐가 좋아?", "target": ["주거통신"]},
    {"query": "통신요금 30% 할인 되는 체크카드 알려줘", "target": ["주거통신"]},

    # ── 여가 ──
    {"query": "항공권 자주 사는데 마일리지 적립 카드 추천해줘", "target": ["여가"]},
    {"query": "여행 많이 다니는데 하나투어 할인 되는 카드 있어?", "target": ["여가"]},
    {"query": "영화 자주 보는데 CGV 할인 카드 추천해줘", "target": ["여가"]},
    {"query": "에버랜드 롯데월드 할인 되는 카드 뭐야?", "target": ["여가"]},
    {"query": "면세점 자주 이용하는데 면세점 할인 카드 알려줘", "target": ["여가"]},
    {"query": "해외여행 갈 때 공항라운지 이용 가능한 카드 뭐야?", "target": ["여가"]},
    {"query": "대한항공 아시아나 마일리지 쌓이는 카드 추천해줘", "target": ["여가"]},
    {"query": "아고다 호텔스닷컴 호텔 예약 할인 카드 있어?", "target": ["여가"]},
    {"query": "진에어 제주항공 국내선 할인 카드 뭐야?", "target": ["여가"]},
    {"query": "노래방 PC방 자주 가는데 여가 할인 카드 추천해줘", "target": ["여가"]},
    {"query": "공연 티켓 인터파크 YES24 할인 카드 알려줘", "target": ["여가"]},
    {"query": "롯데시네마 메가박스 할인 카드 있어?", "target": ["여가"]},

    # ── 마트/쇼핑 오프라인 ──
    {"query": "이마트 홈플러스 마트 할인 카드 뭐야?", "target": ["마트"]},
    {"query": "다이소 자주 가는데 할인 카드 추천해줘", "target": ["마트"]},
    {"query": "롯데마트 트레이더스 할인 카드 알려줘", "target": ["마트"]},
    {"query": "백화점 롯데 신세계 현대 할인 카드 있어?", "target": ["마트"]},
    {"query": "오프라인 쇼핑 많이 하는데 백화점 마트 할인 카드 추천해줘", "target": ["마트"]},

    # ── 병원 ──
    {"query": "병원 자주 가는데 의료비 할인 카드 있어?", "target": ["병원"]},
    {"query": "약국이랑 병원비 많이 쓰는데 혜택 있는 카드 뭐야?", "target": ["병원"]},
    {"query": "치과 자주 가는데 병원 캐시백 카드 추천해줘", "target": ["병원"]},
    {"query": "동물병원도 되는 의료 할인 카드 있어?", "target": ["병원"]},

    # ── 주유 ──
    {"query": "주유 자주 하는데 주유 할인 카드 뭐야?", "target": ["주유"]},
    {"query": "GS칼텍스 SK주유소 할인 카드 추천해줘", "target": ["주유"]},
    {"query": "주말 주유 할인 많이 되는 카드 알려줘", "target": ["주유"]},
    {"query": "리터당 할인 되는 카드 있어?", "target": ["주유"]},

    # ── 교육 ──
    {"query": "독서실 스터디카페 자주 가는데 할인 카드 있어?", "target": ["교육"]},
    {"query": "책 자주 사는데 알라딘 YES24 적립 카드 뭐야?", "target": ["교육"]},
    {"query": "토익 오픽 어학시험 할인 카드 추천해줘", "target": ["교육"]},
    {"query": "문구용품 자주 사는데 할인 카드 있어?", "target": ["교육"]},
    {"query": "학생인데 공부 관련 혜택 있는 카드 뭐야?", "target": ["교육"]},

    # ── 해외 ──
    {"query": "해외여행 자주 가는데 수수료 면제되는 카드 뭐야?", "target": ["해외"]},
    {"query": "해외에서 쓸 카드 찾는데 환전 수수료 없는 카드 추천해줘", "target": ["해외"]},
    {"query": "일본 여행 가는데 현지 결제 수수료 없는 카드 알려줘", "target": ["해외"]},
    {"query": "트래블 카드 중에 해외 수수료 없는 거 뭐야?", "target": ["해외"]},
    {"query": "해외 ATM 인출 수수료 없는 카드 추천해줘", "target": ["해외"]},
    {"query": "외화 하나머니로 해외 결제 되는 카드 뭐야?", "target": ["해외"]},
    {"query": "유럽 미국 여행 갈 때 수수료 없는 카드 알려줘", "target": ["해외"]},
    {"query": "해외 5% 캐시백 되는 트래블 카드 추천해줘", "target": ["해외"]},

    # ── 간편결제 ──
    {"query": "삼성페이 네이버페이 할인 되는 카드 뭐야?", "target": ["간편결제"]},
    {"query": "카카오페이 PAYCO 추가 할인 카드 알려줘", "target": ["간편결제"]},
    {"query": "KB Pay로 결제하면 할인 되는 카드 있어?", "target": ["간편결제"]},
    {"query": "간편결제 쓸 때 혜택 좋은 카드 추천해줘", "target": ["간편결제"]},

    # ── 복합 쿼리 ──
    {"query": "카페랑 쇼핑 많이 하는데 두 가지 혜택 다 있는 카드 뭐야?", "target": ["카페", "쇼핑"]},
    {"query": "편의점이랑 배달 자주 쓰는 20대인데 혜택 좋은 카드 추천해줘", "target": ["편의점", "배달"]},
    {"query": "해외여행 가면서 면세점도 자주 이용하는데 둘 다 되는 카드 있어?", "target": ["해외", "여가"]},
    {"query": "넷플릭스 구독에 통신비도 아끼고 싶은데 카드 뭐가 좋아?", "target": ["OTT", "주거통신"]},
    {"query": "학생인데 교통비랑 편의점 할인 되는 카드 추천해줘", "target": ["교통", "편의점"]},
    {"query": "카페 편의점 배달 다 할인 되는 카드 있어?", "target": ["카페", "편의점", "배달"]},
    {"query": "쇼핑이랑 OTT 구독 둘 다 혜택 있는 카드 뭐야?", "target": ["쇼핑", "OTT"]},
    {"query": "해외여행이랑 항공 마일리지 적립 되는 카드 추천해줘", "target": ["해외", "여가"]},
    {"query": "마트랑 주유 할인 다 되는 카드 알려줘", "target": ["마트", "주유"]},
    {"query": "교통비랑 OTT 구독 할인 카드 추천해줘", "target": ["교통", "OTT"]},
    {"query": "배달이랑 쇼핑 자주 하는데 둘 다 혜택 있는 카드 뭐야?", "target": ["배달", "쇼핑"]},
    {"query": "카페랑 통신비 할인 되는 카드 뭐가 있어?", "target": ["카페", "주거통신"]},
    {"query": "20대 학생인데 첫 카드 추천해줘 편의점 카페 많이 써", "target": ["편의점", "카페"]},
    {"query": "여행 자주 가고 OTT 많이 보는데 둘 다 혜택 있는 카드 있어?", "target": ["여가", "OTT"]},
    {"query": "무신사 올리브영 많이 쓰는 20대인데 쇼핑 특화 카드 추천해줘", "target": ["쇼핑"]},
    {"query": "배달이랑 넷플릭스 자주 쓰는데 혜택 같이 있는 카드 뭐야?", "target": ["배달", "OTT"]},
    {"query": "대중교통이랑 배달의민족 할인 카드 추천해줘", "target": ["교통", "배달"]},
    {"query": "군인인데 편의점 교통 혜택 좋은 카드 있어?", "target": ["편의점", "교통"]},
    {"query": "트래블 체크카드 중에 해외 수수료 없고 국내도 혜택 있는 거 뭐야?", "target": ["해외", "편의점"]},
    {"query": "스타벅스 자주 가고 OTT도 구독 중인데 둘 다 혜택 있는 카드 알려줘", "target": ["카페", "OTT"]},
    {"query": "주유랑 마트 할인 같이 되는 카드 있어?", "target": ["주유", "마트"]},
    {"query": "CGV 영화관이랑 카페 혜택 있는 카드 추천해줘", "target": ["여가", "카페"]},
    {"query": "배달이랑 통신비 같이 할인 되는 카드 뭐야?", "target": ["배달", "주거통신"]},
]



# 청크에서 카테고리 판단

def get_chunk_categories(text: str) -> list:
    matched = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                matched.append(category)
                break
    return matched


def get_node_text(chunk) -> str:
    payload = chunk.payload
    if "_node_content" in payload:
        try:
            node_content = json.loads(payload["_node_content"])
            return node_content.get("text", "")
        except:
            return str(payload["_node_content"])
    return payload.get("text", payload.get("content", ""))



# 정답 셋 생성

print(f"쿼리 {len(QUERY_TEMPLATES)}개 × 청크 {len(all_chunks)}개 조합 중...")
dataset = []

for query_item in QUERY_TEMPLATES:
    query = query_item["query"]
    target_cats = query_item["target"]

    for chunk in all_chunks:
        text = get_node_text(chunk)
        if not text or len(text) < 50:
            continue

        card_name = chunk.payload.get("card_name", "unknown")
        card_type = chunk.payload.get("card_type", "unknown")
        chunk_cats = get_chunk_categories(text)
        is_relevant = any(cat in target_cats for cat in chunk_cats)

        dataset.append({
            "query": query,
            "card_name": card_name,
            "card_type": card_type,
            "chunk_categories": chunk_cats,
            "chunk_text": text[:600],
            "label": 1 if is_relevant else 0
        })

pos = sum(1 for d in dataset if d["label"] == 1)
neg = sum(1 for d in dataset if d["label"] == 0)
print(f"\n원본: {len(dataset)}개 (P:{pos} N:{neg})")

# 균형 조정 1:2
random.seed(42)
positives = [d for d in dataset if d["label"] == 1]
negatives = [d for d in dataset if d["label"] == 0]
n_neg = min(len(negatives), len(positives) * 2)
balanced = positives + random.sample(negatives, n_neg)
random.shuffle(balanced)

n = len(balanced)
train_end = int(n * 0.70)
val_end   = int(n * 0.85)

splits = {
    "train": balanced[:train_end],
    "val":   balanced[train_end:val_end],
    "test":  balanced[val_end:],
    "full":  dataset,
}

print(f"\n균형 후 {len(balanced)}개")
for name, data in splits.items():
    if name == "full": continue
    p = sum(1 for d in data if d["label"] == 1)
    ng = sum(1 for d in data if d["label"] == 0)
    print(f"  {name}: {len(data)}개 (P:{p} N:{ng})")

os.makedirs("data/ground_truth", exist_ok=True)
for name, data in splits.items():
    path = f"data/ground_truth/{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"저장: {path}")

print("\n완료")