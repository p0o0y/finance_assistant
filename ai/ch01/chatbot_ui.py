import streamlit as st
import requests

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="카드 혜택 추천 챗봇",
    page_icon="💳",
    layout="centered",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', sans-serif;
    }
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        min-height: 100vh;
    }
    .main-header {
        text-align: center;
        padding: 24px 0 12px;
    }
    .main-header h1 {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #f093fb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
    }
    .main-header p {
        color: rgba(255,255,255,0.45);
        font-size: 0.9rem;
    }
    .user-bubble {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 12px 18px;
        border-radius: 18px 18px 4px 18px;
        margin: 8px 0 8px auto;
        max-width: 72%;
        width: fit-content;
        word-break: break-word;
        box-shadow: 0 4px 15px rgba(102,126,234,0.35);
        font-size: 0.95rem;
        line-height: 1.6;
    }
    .bot-bubble {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.15);
        color: #e8e8f0;
        padding: 14px 18px;
        border-radius: 18px 18px 18px 4px;
        margin: 8px auto 8px 0;
        max-width: 78%;
        width: fit-content;
        word-break: break-word;
        backdrop-filter: blur(8px);
        font-size: 0.95rem;
        line-height: 1.75;
    }
    .source-tag {
        display: inline-block;
        background: rgba(102,126,234,0.2);
        border: 1px solid rgba(102,126,234,0.45);
        color: #a0b4ff;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        margin: 3px 2px 0;
    }
    .stChatInput > div {
        background: rgba(255,255,255,0.07) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 16px !important;
    }
    .stChatInput textarea { color: white !important; }
    hr { border-color: rgba(255,255,255,0.1); }
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# 세션 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 헤더
st.markdown("""
<div class="main-header">
    <h1>💳 카드 혜택 추천 AI</h1>
    <p>내 소비 패턴에 맞는 최적의 카드 혜택을 찾아드려요</p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# 대화 렌더링
if not st.session_state.messages:
    st.markdown("""
    <div style="text-align:center;padding:50px 0;color:rgba(255,255,255,0.28);">
        <div style="font-size:3rem;">💬</div>
        <div style="margin-top:10px;font-size:0.88rem;line-height:1.8;">
            예시: "카페를 자주 가는데 할인 많이 되는 카드 추천해줘"<br>
            "신용카드 중에 OTT 구독 혜택 있는 거 뭐 있어?"<br>
            "체크카드로 편의점 혜택 뭐가 좋아?"
        </div>
    </div>
    """, unsafe_allow_html=True)

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(
            f'<div style="display:flex;justify-content:flex-end;">'
            f'<div class="user-bubble">🧑{msg["content"]}</div></div>',
            unsafe_allow_html=True
        )
    else:
        sources = msg.get("sources", [])
        source_html = ""
        if sources:
            tags = "".join([
                f'<span class="source-tag">💳 {s["card_name"]} ({s["score"]})</span>'
                for s in sources
            ])
            source_html = f"<div style='margin-top:10px;'>{tags}</div>"

        st.markdown(
            f'<div style="display:flex;justify-content:flex-start;">'
            f'<div class="bot-bubble">🤖 {msg["content"]}{source_html}</div></div>',
            unsafe_allow_html=True
        )

# 채팅 입력
if prompt := st.chat_input("카드 혜택에 대해 물어보세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("추천 카드를 찾는 중..."):
        try:
            res = requests.post(
                f"{API_BASE}/ask",
                json={"query": prompt, "user_report": ""},
                timeout=120
            )
            res.raise_for_status()
            data = res.json()
            st.session_state.messages.append({
                "role": "assistant",
                "content": data.get("answer", "응답을 받지 못했습니다."),
                "sources": data.get("source_nodes", []),
            })
        except requests.exceptions.ConnectionError:
            st.session_state.messages.append({
                "role": "assistant",
                "content": " FastAPI 서버에 연결할 수 없어요. `uvicorn main:app` 이 실행 중인지 확인해주세요.",
                "sources": [],
            })
        except Exception as e:
            st.session_state.messages.append({
                "role": "assistant",
                "content": f" 오류: {str(e)}",
                "sources": [],
            })

    st.rerun()

# 하단 초기화 버튼
st.markdown("<br>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([3, 1, 3])
with col2:
    if st.button("🗑️ 초기화"):
        st.session_state.messages = []
        st.rerun()
