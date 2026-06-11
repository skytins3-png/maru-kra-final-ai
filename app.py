
import streamlit as st
import pandas as pd

st.set_page_config(page_title="MARU KRA AI", page_icon="🐎", layout="centered")

if "page" not in st.session_state:
    st.session_state.page = "home"

st.sidebar.title("설정")
kra_url = st.sidebar.text_input("KRA 공식 수동구매 URL", "https://m.kra.co.kr/main.do")

data = {
    "race": "서울 6R",
    "start": "16:05",
    "remain": "18분",
    "decision": "소액 공격",
    "main_combo": "5 - 11 - 2",
    "odds": "46.8",
    "confidence": "84",
    "profit": "높음",
    "hit": "보통+",
    "defense1": "5 - 11 - 7",
    "defense1_odds": "28.4",
    "defense2": "5 - 2 - 11",
    "defense2_odds": "34.6",
}

with st.sidebar.expander("표시값 수정", expanded=False):
    for k in list(data.keys()):
        data[k] = st.text_input(k, data[k])

st.markdown("""
<style>
.block-container {
  max-width: 760px;
  padding-top: 1.0rem;
  padding-bottom: 2rem;
}
.header {
  display:flex;
  justify-content:space-between;
  align-items:flex-start;
  margin-bottom:18px;
}
.logo {
  font-size:42px;
  font-weight:1000;
  color:#0f172a;
  letter-spacing:.3px;
  line-height:1.0;
}
.ai {
  font-size:18px;
  background:#2563eb;
  color:#fff;
  border-radius:8px;
  padding:4px 8px;
  vertical-align:middle;
}
.sub {
  font-size:20px;
  color:#0f766e;
  font-weight:800;
  margin-top:12px;
  letter-spacing:1px;
}
.header-icons {
  font-size:30px;
  color:#0f172a;
  padding-top:3px;
}
.main-card {
  background: radial-gradient(circle at 78% 8%, #0f766e 0%, #064e3b 38%, #022c22 100%);
  color:white;
  border-radius:28px;
  padding:28px;
  margin: 8px 0 24px 0;
  box-shadow:0 12px 30px rgba(2,44,34,.22);
}
.main-title {
  font-size:24px;
  font-weight:1000;
  margin-bottom:28px;
}
.badge {
  display:inline-block;
  background:#16a34a;
  color:white;
  padding:9px 16px;
  border-radius:12px;
  font-size:20px;
  font-weight:1000;
}
.time {
  float:right;
  color:#ecfdf5;
  font-size:19px;
  font-weight:900;
  margin-top:8px;
}
.race-line {
  font-size:24px;
  color:#ecfdf5;
  margin-top:28px;
}
.combo-row {
  display:flex;
  justify-content:space-between;
  align-items:flex-end;
  margin-top:22px;
}
.combo {
  font-size:62px;
  font-weight:1000;
  letter-spacing:2px;
  line-height:1;
}
.odds {
  font-size:56px;
  font-weight:1000;
  color:#facc15;
  line-height:1;
}
.mini-grid {
  display:grid;
  grid-template-columns:repeat(3, 1fr);
  gap:14px;
  margin-bottom:20px;
}
.mini-card {
  background:white;
  border:1px solid #e5e7eb;
  border-radius:20px;
  padding:20px 10px;
  text-align:center;
  box-shadow:0 4px 14px rgba(15,23,42,.08);
}
.mini-label {
  font-size:19px;
  color:#111827;
  font-weight:800;
}
.mini-value {
  font-size:34px;
  color:#047857;
  font-weight:1000;
  margin-top:6px;
}
.box {
  background:white;
  border:1px solid #e5e7eb;
  border-radius:22px;
  padding:20px;
  margin:16px 0;
  color:#111827;
  box-shadow:0 4px 14px rgba(15,23,42,.06);
}
.box-title {
  font-size:24px;
  font-weight:1000;
  margin-bottom:16px;
}
.def-line {
  font-size:23px;
  line-height:1.8;
  display:flex;
  gap:50px;
}
.hidden-grid {
  display:grid;
  grid-template-columns:repeat(4,1fr);
  gap:16px;
  text-align:center;
  color:#475569;
  font-size:18px;
  margin-top:16px;
}
.buy-note {
  text-align:center;
  color:#64748b;
  font-size:15px;
  margin-top:10px;
  margin-bottom:22px;
}
.hub-card {
  background:white;
  border:1px solid #e5e7eb;
  border-radius:20px;
  padding:18px 22px;
  margin-top:16px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  box-shadow:0 4px 12px rgba(15,23,42,.05);
}
.hub-title {
  font-size:24px;
  font-weight:1000;
  color:#0f172a;
}
.hub-sub {
  color:#64748b;
  font-size:16px;
  margin-top:4px;
}
.safe {
  border:1px solid #bfdbfe;
  background:#eff6ff;
  color:#1e3a8a;
  border-radius:18px;
  padding:16px;
  margin:12px 0;
  font-weight:900;
}
.step {
  background:white;
  border:1px solid #e5e7eb;
  border-radius:18px;
  padding:14px;
  margin:10px 0;
}
.num {
  display:inline-block;
  background:#047857;
  color:white;
  width:30px;
  height:30px;
  line-height:30px;
  text-align:center;
  border-radius:50%;
  font-weight:1000;
  margin-right:8px;
}
.stButton > button {
  background:#0b5cff;
  color:white;
  font-size:22px;
  font-weight:1000;
  border-radius:18px;
  height:64px;
}
@media(max-width: 700px) {
  .combo {font-size:48px;}
  .odds {font-size:42px;}
  .mini-grid {gap:8px;}
  .mini-label {font-size:16px;}
  .mini-value {font-size:28px;}
  .hidden-grid {font-size:15px; gap:10px;}
}
</style>
""", unsafe_allow_html=True)

def render_home():
    st.markdown("""
<div class="header">
  <div>
    <div class="logo">MARU KRA <span class="ai">AI</span></div>
    <div class="sub">SIMPLE FINAL ONLY</div>
  </div>
  <div class="header-icons">🔔 ☰</div>
</div>
""", unsafe_allow_html=True)

    st.markdown(f"""
<div class="main-card">
  <div class="main-title">🎯 분석은 숨김 · 최종 결과만</div>
  <span class="badge">🎯 {data['decision']}</span>
  <span class="time">🕘 출발까지 {data['remain']}</span>
  <div class="race-line">{data['race']} · 출발 {data['start']}</div>
  <div class="combo-row">
    <div class="combo">{data['main_combo']}</div>
    <div class="odds">{data['odds']}배</div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown(f"""
<div class="mini-grid">
  <div class="mini-card">
    <div class="mini-label">🛡 신뢰도</div>
    <div class="mini-value">{data['confidence']}%</div>
  </div>
  <div class="mini-card">
    <div class="mini-label">📈 수익기대</div>
    <div class="mini-value">{data['profit']}</div>
  </div>
  <div class="mini-card">
    <div class="mini-label">🎯 적중기대</div>
    <div class="mini-value">{data['hit']}</div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown(f"""
<div class="box">
  <div class="box-title">🛡 방어 조합</div>
  <div class="def-line"><span>1) {data['defense1']}</span><span>{data['defense1_odds']}배</span></div>
  <div class="def-line"><span>2) {data['defense2']}</span><span>{data['defense2_odds']}배</span></div>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="box">
  <div class="box-title">🔒 숨겨진 분석 <span style="float:right;font-size:17px;">접기 ^</span></div>
  <div class="hidden-grid">
    <div>🐴<br>말</div>
    <div>🏇<br>기수</div>
    <div>🧬<br>혈통</div>
    <div>🌤<br>날씨</div>
    <div>📊<br>배당</div>
    <div>🛒<br>구매쏠림</div>
    <div>🚫<br>블랙리스트</div>
    <div>🧪<br>시뮬레이션</div>
  </div>
</div>
""", unsafe_allow_html=True)

    if st.button("↗ KRA 공식 수동구매 화면 열기", use_container_width=True):
        st.session_state.page = "buy"
        st.rerun()

    st.markdown('<div class="buy-note">※ 자동구매 아님 · 직접 확인 후 수동구매</div>', unsafe_allow_html=True)

    with st.expander("허브 보기", expanded=False):
        st.caption("상세 분석은 접어서 필요할 때만 확인")
        df = pd.DataFrame([
            ["말", "최근5전 / 체중 / 게이트 분석"],
            ["기수", "승률 / 흐름 / 기수교체 / 말궁합"],
            ["혈통", "지역 / 날씨 / 거리 적성"],
            ["배당", "구매쏠림 / 배당가치 / 배당흐름"],
            ["블랙리스트", "반복 실패패턴 감점"],
            ["시뮬레이션", "경주별 30~100회 반복 검증"],
        ], columns=["분석", "내용"])
        st.dataframe(df, use_container_width=True)

def render_buy():
    st.markdown("## ← KRA 공식 수동구매")
    st.markdown("""
<div class="safe">
🔒 자동구매 아님 · 직접 확인 후 수동구매<br>
본 화면은 자동구매를 실행하지 않습니다. KRA 공식 페이지에서 직접 구매합니다.
</div>
""", unsafe_allow_html=True)

    st.markdown(f"""
<div class="main-card">
  <div style="font-size:34px;font-weight:1000;">{data['race']}</div>
  <div style="font-size:19px;margin-top:8px;">출발 {data['start']} · 추천 조합</div>
  <div style="font-size:54px;font-weight:1000;margin-top:20px;">{data['main_combo']}</div>
  <div style="font-size:44px;font-weight:1000;color:#facc15;text-align:right;">{data['odds']}배</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("### 구매 진행 안내")
    steps = [
        ("공식 구매창 열기", "아래 버튼을 눌러 KRA 공식 구매 페이지로 이동합니다."),
        ("조합 확인", "선택한 조합이 정확한지 공식 구매창에서 다시 확인하세요."),
        ("직접 금액 입력", "구매 금액을 직접 입력합니다."),
        ("최종 확인 후 구매", "최종 내용을 확인한 뒤 구매를 완료합니다."),
    ]
    for i, (title, body) in enumerate(steps, 1):
        st.markdown(f"""
<div class="step">
  <span class="num">{i}</span><b>{title}</b><br>
  <span style="margin-left:40px;color:#475569;">{body}</span>
</div>
""", unsafe_allow_html=True)

    st.link_button("↗ KRA 공식 구매 페이지로 이동", kra_url, use_container_width=True)

    if st.button("대시보드로 돌아가기", use_container_width=True):
        st.session_state.page = "home"
        st.rerun()

if st.session_state.page == "buy":
    render_buy()
else:
    render_home()
