import streamlit as st
import requests
import base64
from pathlib import Path

SPRING_BASE = "http://163.180.160.37:8080"

st.set_page_config(
    page_title="카드 혜택 추천 챗봇",
    page_icon="💳",
    layout="centered",
)

# 챗봇 아이콘 base64 변환
def get_icon_base64():
    icon_path = Path(__file__).parent / "utils" / "chatbot_icon.png"
    with open(icon_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

icon_b64 = get_icon_base64()

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
    .stApp {
        background: linear-gradient(135deg, #f8fafc, #eef4ff, #f6f7ff);
        min-height: 100vh;
    }
    .main-header h1 {
        font-size: 2rem; font-weight: 700;
        background: linear-gradient(135deg, #2563eb, #7c3aed);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .main-header p { color: #64748b; font-size: 0.9rem; }
    .user-bubble {
        background: linear-gradient(135deg, #2563eb, #4f46e5);
        color: white; padding: 12px 18px;
        border-radius: 18px 18px 4px 18px;
        margin: 8px 0 8px auto;
        max-width: 72%; width: fit-content;
        word-break: break-word;
        box-shadow: 0 6px 18px rgba(37, 99, 235, 0.25);
        font-size: 0.95rem; line-height: 1.6;
    }
    .bot-bubble {
        background: #ffffff; border: 1px solid #dbe3f0;
        color: #1e293b; padding: 14px 18px;
        border-radius: 18px 18px 18px 4px;
        max-width: 78%; width: fit-content;
        word-break: break-word;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
        font-size: 0.95rem; line-height: 1.75;
    }
    .source-tag {
        display: inline-block; background: #eef2ff;
        border: 1px solid #c7d2fe; color: #4338ca;
        padding: 3px 10px; border-radius: 20px;
        font-size: 0.75rem; margin: 3px 2px 0;
    }
    .stChatInput > div {
        background: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.08);
    }
    .stChatInput textarea { color: #111827 !important; }
    hr { border-color: #dbe3f0; }
    ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# 세션 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "access_token" not in st.session_state:
    st.session_state.access_token = ""
if "use_report" not in st.session_state:
    st.session_state.use_report = True  # 기본값: 소비패턴 반영

# ── 사이드바 ──
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
        st.session_state.use_report = True
        st.rerun()

    if st.session_state.access_token:
        st.markdown("🟢 토큰 입력됨")
    else:
        st.markdown("🔴 토큰 없음 — 요청이 거부될 수 있어요")

    st.markdown("---")
    # 현재 모드 표시
    if st.session_state.use_report:
        st.markdown(" **소비패턴 반영 모드**")
    else:
        st.markdown(" **일반 추천 모드**")

# ── 헤더 ──
st.markdown("""
<div class="main-header">
    <h1>카드 혜택 추천 AI</h1>
    <p>내 소비 패턴을 분석해 가장 유리한 카드 혜택을 추천해드려요</p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# ── 대화 렌더링 ──
# 초기 화면: 메시지 없을 때
if not st.session_state.messages:
    st.markdown(f"""
    <div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:16px;">
        <img src="data:image/png;base64,{icon_b64}"
             style="width:80px;height:80px;object-fit:contain;flex-shrink:0;margin-top:4px;">
        <div class="bot-bubble">
            안녕하세요! 카드 혜택 추천 AI입니다.<br>
            소비 패턴을 기반으로 최적의 카드와 혜택을 추천해드려요.<br><br>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button(" 소비패턴 반영 모드", use_container_width=True):
            st.session_state.use_report = True
            st.rerun()
    with col2:
        if st.button(" 카드 혜택 질문 모드", use_container_width=True):
            st.session_state.use_report = False
            st.rerun()
    if st.session_state.use_report:
        st.markdown(" **소비패턴 반영 모드** — 내 소비 데이터를 바탕으로 추천해드려요")
    else:
        st.markdown(" **일반 응답 모드** — 궁금하신 카드에 대해 답해드려요")
# 메시지 렌더링
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(
            f'<div style="display:flex;justify-content:flex-end;margin:8px 0;">'
            f'<div class="user-bubble"> {msg["content"]}</div></div>',
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

        # 챗봇 아이콘 + 말풍선
        st.markdown(
            f'<div style="display:flex;align-items:flex-start;gap:10px;margin:8px 0;">'
            f'<img src="data:image/png;base64,{icon_b64}" '
            f'style="width:80px;height:80px;object-fit:contain;flex-shrink:0;margin-top:4px;">'
            f'<div class="bot-bubble">{msg["content"]}{source_html}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

# ── 채팅 입력 ──
if prompt := st.chat_input("카드 혜택에 대해 물어보세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("추천 카드를 찾는 중..."):
        try:
            cookies = {}
            if st.session_state.access_token:
                cookies["accessToken"] = st.session_state.access_token

            # 소비패턴 반영 여부에 따라 user_report 다르게
            user_report = ""
            if st.session_state.use_report:
                # Spring이 JWT로 리포트 자동 주입하니까 빈 문자열로 보내도 됨
                user_report = "최근 소비 데이터를 반영해주세요"

            res = requests.post(
                f"{SPRING_BASE}/api/cards/recommend",
                json={"query": prompt, "user_report": user_report},
                cookies=cookies,
                timeout=120
            )

            if res.status_code in [401, 403]:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "인증 실패 (401/403) — 왼쪽 사이드바에서 토큰을 다시 확인해주세요.",
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
                "content": "FastAPI 서버에 연결할 수 없어요. uvicorn이 실행 중인지 확인해주세요.",
                "sources": [],
            })
        except Exception as e:
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"오류: {str(e)}",
                "sources": [],
            })

    st.rerun()