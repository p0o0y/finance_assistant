import streamlit as st
import requests


SPRING_BASE = "http://163.180.160.37:8080"
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
    background: linear-gradient(135deg, #f4f7fb, #dbeafe, #eff6ff);
    min-height: 100vh;
    }
    .main-header {
        text-align: center;
        padding: 24px 0 12px;
    }
    .main-header h1 {
        font-size: 2rem; font-weight: 700;
        background: linear-gradient(135deg, #667eea, #f093fb);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .main-header p { color: rgba(255,255,255,0.45); font-size: 0.9rem; }
    .user-bubble {
        background: linear-gradient(135deg, #667eea, #764ba2); color: white;
        padding: 12px 18px; border-radius: 18px 18px 4px 18px;
        margin: 8px 0 8px auto; max-width: 72%; width: fit-content;
        word-break: break-word; box-shadow: 0 4px 15px rgba(102,126,234,0.35);
        font-size: 0.95rem; line-height: 1.6;
    }
    .bot-bubble {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.15);
        color: #1e3a5f;
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
        display: inline-block; background: rgba(102,126,234,0.2);
        border: 1px solid rgba(102,126,234,0.45); color: #a0b4ff;
        padding: 3px 10px; border-radius: 20px; font-size: 0.75rem; margin: 3px 2px 0;
    }
    .token-box {
        background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.15);
        border-radius: 12px; padding: 14px; margin-bottom: 16px;
    }
    .stChatInput > div {
        background: rgba(255,255,255,0.07) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 16px !important;
    }
    .stChatInput textarea { color: black !important; }
    hr { border-color: rgba(255,255,255,0.1); }
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# 세션 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "access_token" not in st.session_state:
    st.session_state.access_token = ""

# ── 사이드바: JWT 토큰 입력 ──
with st.sidebar:
    st.markdown("## 🔑 인증")
    st.markdown("Postman에서 복사한 accessToken을 붙여넣으세요.")
    token_input = st.text_area(
        "Access Token",
        value=st.session_state.access_token,
        height=120,
        placeholder="eyJhbGciOiJIUzI1NiJ9...",
        label_visibility="collapsed"
    )
    if st.button("✅ 토큰 저장", use_container_width=True):
        st.session_state.access_token = token_input.strip()
        st.success("토큰이 저장됐어요!")

    st.markdown("---")
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    # 토큰 상태 표시
    if st.session_state.access_token:
        st.markdown("🟢 토큰 입력됨")
    else:
        st.markdown("🔴 토큰 없음 — 요청이 거부될 수 있어요")

# ── 메인: 헤더 ──
st.markdown("""
<div class="main-header">
    <h1>💳 카드 혜택 추천 AI</h1>
    <p>내 소비 패턴에 맞는 최적의 카드 혜택을 찾아드려요</p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# ── 대화 렌더링 ──
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

# ── 채팅 입력 ──
if prompt := st.chat_input("카드 혜택에 대해 물어보세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("추천 카드를 찾는 중..."):
        try:
            # JWT 토큰을 쿠키에 담아서 Spring으로 요청
            cookies = {}
            if st.session_state.access_token:
                cookies["accessToken"] = st.session_state.access_token

            res = requests.post(
                f"{SPRING_BASE}/api/cards/recommend",
                json={"query": prompt, "user_report": ""},
                cookies=cookies,
                timeout=120
            )

            if res.status_code == 401 or res.status_code == 403:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": " 인증 실패 (401/403) — 왼쪽 사이드바에서 토큰을 다시 확인해주세요.",
                    "sources": [],
                })
            else:
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