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

query_params = st.query_params
if "accessToken" in query_params:
    st.session_state.access_token = query_params["accessToken"]
    st.query_params.clear()
    st.rerun()

# 챗봇 아이콘 base64 변환
def get_icon_base64():
    try:
        icon_path = Path(__file__).parent / "utils" / "chatbot_icon.png"
        with open(icon_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""

icon_b64 = get_icon_base64()


st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght=400;500;700&display=swap');
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
    .sync-box {
        background: #ffffff; padding: 20px; border-radius: 12px;
        border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    /* 카카오 로그인 버튼 스타일 */
    .kakao-btn {
        display: block; width: 100%; background-color: #FEE500; color: #191919;
        text-align: center; padding: 10px 0; font-weight: 700; border-radius: 8px;
        text-decoration: none; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .kakao-btn:hover { background-color: #FADA0A; color: #191919; text-decoration: none; }
</style>
""", unsafe_allow_html=True)

# 세션 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "access_token" not in st.session_state:
    st.session_state.access_token = ""
if "use_report" not in st.session_state:
    st.session_state.use_report = True


def get_auth_cookies():
    cookies = {}
    if st.session_state.access_token:
        cookies["accessToken"] = st.session_state.access_token
    return cookies


with st.sidebar:
    st.markdown("## 🔑 사용자 인증")
    
    # 로그인 상태에 따른 UI 분기
    if not st.session_state.access_token:
        st.markdown("서비스를 이용하려면 로그인이 필요합니다.")
        
        kakao_oauth_url = f"{SPRING_BASE}/oauth2/authorization/kakao"
        st.markdown(f'<a href="{kakao_oauth_url}" target="_self" class="kakao-btn">🟡 카카오 계정으로 로그인</a>', unsafe_allow_html=True)
        
        with st.expander("또는 수동으로 토큰 입력"):
            token_input = st.text_area("Access Token", height=80, placeholder="eyJhbGciOiJIUzI1NiJ9...")
            if st.button("토큰 직접 저장"):
                st.session_state.access_token = token_input.strip()
                st.rerun()
    else:
        st.markdown("인증 성공")
        st.code(f"Token: {st.session_state.access_token[:15]}...", language="text")
        
        if st.button("로그아웃", use_container_width=True):
            st.session_state.access_token = ""
            st.session_state.messages = []
            st.success("로그아웃 되었습니다.")
            st.rerun()

    st.markdown("---")
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.session_state.use_report = True
        st.rerun()

# ── 탭 구성 (챗봇 vs CODEF 관리) ──
tab1, tab2 = st.tabs(["💬 AI 혜택 추천 챗봇", "💳 마이데이터 연동 관리"])

# 챗봇 UI
with tab1:
    if not st.session_state.messages:
        st.markdown(f"""
        <div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:16px;">
            <div class="bot-bubble">
                안녕하세요, 카드 혜택 추천 AI입니다.<br>
                마이데이터로 연동된 소비 패턴을 기반으로 최적의 카드와 혜택을 추천해드려요.<br>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button(" 소비패턴 반영 모드", use_container_width=True):
                st.session_state.use_report = True
                st.rerun()
        with col2:
            if st.button(" 질문 모드", use_container_width=True):
                st.session_state.use_report = False
                st.rerun()

    # 메시지 렌더링
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div style="display:flex;justify-content:flex-end;margin:8px 0;"><div class="user-bubble">{msg["content"]}</div></div>', unsafe_allow_html=True)
        else:
            sources = msg.get("sources", [])
            source_html = ""
            if sources:
                tags = "".join([f'<span class="source-tag">💳 {s["card_name"]} ({s["score"]})</span>' for s in sources])
                source_html = f"<div style='margin-top:10px;'>{tags}</div>"
            st.markdown(f'<div style="display:flex;align-items:flex-start;gap:10px;margin:8px 0;"><div class="bot-bubble">{msg["content"]}{source_html}</div></div>', unsafe_allow_html=True)

    # 채팅 입력
    if prompt := st.chat_input("카드 혜택에 대해 물어보세요..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.spinner("카드 분석 중..."):
            try:
                user_report = "최근 소비 데이터를 반영해주세요" if st.session_state.use_report else ""
                res = requests.post(
                    f"{SPRING_BASE}/api/cards/recommend",
                    json={"query": prompt, "user_report": user_report},
                    cookies=get_auth_cookies(),
                    timeout=120
                )
                if res.status_code in [401, 403]:
                    st.session_state.messages.append({"role": "assistant", "content": "인증 실패 — 사이드바 토큰을 확인하세요.", "sources": []})
                else:
                    res.raise_for_status()
                    data = res.json()
                    st.session_state.messages.append({"role": "assistant", "content": data.get("answer", "응답 실패"), "sources": data.get("source_nodes", [])})
            except Exception as e:
                st.session_state.messages.append({"role": "assistant", "content": f"오류: {str(e)}", "sources": []})
        st.rerun()


# 마이데이터 연동 관리 UI
with tab2:
    st.markdown("### 자산 연동 ")
    st.markdown("연동할 카드사를 선택하세요.")

    card_company_options = {
      "국민카드": "0301",
        "농협카드": "0304", #찐
        "우리카드": "0309", #찐
        "하나카드": "0315"  
    }
    card_image_names = {
        "국민카드": "국민.png",
        "농협카드": "농협.png",
        "우리카드": "우리.png",
        "하나카드": "하나.png"
    }

    if "selected_card_company" not in st.session_state:
        st.session_state.selected_card_company = "우리카드"

    cols = st.columns(4)
    for idx, (company_name, company_code) in enumerate(card_company_options.items()):
        with cols[idx]:
            current_dir = Path(__file__).parent
            img_path = current_dir / "utils" / card_image_names[company_name]
            
            if img_path.exists():
                st.image(str(img_path), use_container_width=True)
            else:
                st.warning(f" {company_name} 로고 누락")
            
            # 이미지 바로 밑에 선택 버튼 배치
            is_selected = st.session_state.selected_card_company == company_name
            btn_label = f" {company_name} 선택" if is_selected else f"⚪ {company_name} 선택"
            
            if st.button(btn_label, key=f"btn_{company_code}", use_container_width=True):
                st.session_state.selected_card_company = company_name
                st.rerun()

    selected_company = st.session_state.selected_card_company
    card_code = card_company_options[selected_company]
    
    
    # 2. 계정 연동 섹션 (POST /api/codef/connect)
    st.markdown(" 카드사 계정 연동 ")
    with st.container():
        st.markdown('<div class="sync-box">', unsafe_allow_html=True)
        col_id, col_pw = st.columns(2)
        with col_id:
            login_id = st.text_input("카드사 ID", placeholder="userid123")
        with col_pw:
            login_pw = st.text_input("카드사 PW", type="password", placeholder="******")
            
        if st.button(" 계정 연동 요청", use_container_width=True):
            if not login_id or not login_pw:
                st.warning("ID와 비밀번호를 입력해주세요.")
            else:
                with st.spinner("CODEF API를 통한 RSA 암호화 및 계정 동기화 중..."):
                    try:
                        payload = {"loginId": login_id, "loginPW": login_pw}
                        res = requests.post(
                            f"{SPRING_BASE}/api/codef/connect",
                            params={"cardCompanyCode": card_code},
                            json=payload,
                            cookies=get_auth_cookies()
                        )
                        if res.status_code == 200:
                            ret_data = res.json()
                            st.success(f" 연동 성공! 발급된 Connected ID: {ret_data.get('data')}")
                        else:
                            st.error(f"연동 실패 (오류 코드: {res.status_code})")
                    except Exception as e:
                        st.error(f"서버 통신 실패: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("#### 2단계: 유저 보유 카드 목록 가져오기")
    with st.container():
        st.markdown('<div class="sync-box">', unsafe_allow_html=True)
        st.write("해당 계정에 등록된 정상 카드(분실/도난 제외) 리스트를 스크래핑하여 DB 마스터 데이터와 연동합니다.")
        if st.button(" 내 보유 카드 DB 동기화", use_container_width=True):
            with st.spinner("보유 카드 스크래핑 및 메인 카드 지정 프로세스 가동..."):
                try:
                    res = requests.post(
                        f"{SPRING_BASE}/api/codef/cards/sync",
                        params={"cardCompanyCode": card_code},
                        cookies=get_auth_cookies()
                    )
                    if res.status_code == 200:
                        st.success("💳 보유 카드 리스트 동기화 완료")
                    else:
                        st.error("카드 동기화 실패. Connected ID 등록 상태를 확인하세요.")
                except Exception as e:
                    st.error(f"서버 통신 실패: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)


    st.markdown("#### 3단계: 1개년 승인 내역 수집 ")
    with st.container():
        st.markdown('<div class="sync-box">', unsafe_allow_html=True)
  
        if st.button(" 승인 내역 동기화 ", use_container_width=True):
            with st.spinner("작동 중..."):
                try:
                    res = requests.post(
                        f"{SPRING_BASE}/api/codef/transactions/sync",
                        cookies=get_auth_cookies()
                    )
                    if res.status_code == 200:
                        st.success("완료")
                    else:
                        st.error("내역 조회 실패. 토큰 및 연동 상태를 확인하세요.")
                except Exception as e:
                    st.error(f"서버 통신 실패: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)