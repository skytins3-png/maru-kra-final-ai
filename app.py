
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import itertools
import re
import requests


API_DEFAULT_URLS = {
    "race_url": "https://apis.data.go.kr/B551015/API186_1/SeoulRace_1",
    "entry_url": "https://apis.data.go.kr/B551015/API23_1/entryRaceHorse_1",
    "horse_url": "https://apis.data.go.kr/B551015/API310/raceHorseInfo",
    "body_url": "https://apis.data.go.kr/B551015/API25_1/raceHorseBody",
    "gear_url": "https://apis.data.go.kr/B551015/API24_1/raceHorseGear",
    "rating_url": "https://apis.data.go.kr/B551015/API77/raceHorseRating",
    "odds_url": "https://apis.data.go.kr/B551015/API28_1/Dividend_rate",
    "today_odds_url": "https://apis.data.go.kr/B551015/API301/Dividend_rate_total",
    "result_detail_url": "https://apis.data.go.kr/B551015/API299_1/raceResultDetail_1",
    "race_record_url": "https://apis.data.go.kr/B551015/API214_1/raceRecord_1",
    "start_exam_url": "https://apis.data.go.kr/B551015/API76_1/startExamResult_1",
    "judge_url": "https://apis.data.go.kr/B551015/API72_1/raceJudge_1",
    "jockey_change_url": "https://apis.data.go.kr/B551015/API71_1/jockeyChange_1",
    "weather_alert_url": "https://apis.data.go.kr/1360000/WthrWrnInfoService/getPwnStatus",
    "corner_pace_url": "https://apis.data.go.kr/B551015/API303/corner_rank",
    "popularity_url": "https://apis.data.go.kr/B551015/API302/popularity",
    "first_odds_url": "https://apis.data.go.kr/B551015/API27_1/winPredictionRateInfo_1",
    "second_odds_url": "https://apis.data.go.kr/B551015/API29_1/doublePredictionRateInfo_1",
    "third_odds_url": "https://apis.data.go.kr/B551015/API30_1/triplePredictionRateInfo_1",
}

API_URL_LABELS = [
    ("race_url", "1. 경주정보"),
    ("entry_url", "2. 출전등록말"),
    ("horse_url", "3. 경주마정보"),
    ("body_url", "4. 출전마 체중"),
    ("gear_url", "5. 장구/폐출혈"),
    ("rating_url", "6. 레이팅"),
    ("odds_url", "7. 배당/매출"),
    ("today_odds_url", "8. 시행당일 배당종합"),
    ("result_detail_url", "9. 경주결과상세"),
    ("race_record_url", "10. 경주기록"),
    ("start_exam_url", "11. 출발심사"),
    ("judge_url", "12. 경주심판"),
    ("jockey_change_url", "13. 기수변경"),
    ("weather_alert_url", "14. 기상특보"),
    ("corner_pace_url", "15. 코너/주로빠르기"),
    ("popularity_url", "16. 인기투표"),
    ("first_odds_url", "17. 1착마 적중승식"),
    ("second_odds_url", "18. 2착마 적중승식"),
    ("third_odds_url", "19. 3착마 적중승식"),
]

def api_secret_value(key, default=""):
    try:
        if "maru" in st.secrets:
            if key in st.secrets["maru"]:
                return st.secrets["maru"][key]
            if key.upper() in st.secrets["maru"]:
                return st.secrets["maru"][key.upper()]
    except Exception:
        pass
    try:
        if key in st.secrets:
            return st.secrets[key]
        if key.upper() in st.secrets:
            return st.secrets[key.upper()]
    except Exception:
        pass
    try:
        if key in API_DEFAULT_URLS:
            return API_DEFAULT_URLS[key]
    except Exception:
        pass
    return default

st.set_page_config(page_title="MARU KRA 안정 부팅 복구", page_icon="🐎", layout="wide", initial_sidebar_state="expanded")

try:
    if "saved_count" not in st.session_state:
        st.session_state["saved_count"] = 0
except Exception:
    pass

st.markdown("""
<style>
.stApp { background:#0b0b0b; color:#eee; }
.block-container { max-width:1320px; padding-top:.7rem; }
section[data-testid="stSidebar"] { background:#f3f4f8; color:#222; }
.title-card { border:1px solid #444; background:#151515; padding:15px; color:#fff; font-size:27px; font-weight:900; border-radius:15px; }
.sub-card { border:1px solid #444; background:#151515; padding:10px; color:#ddd; font-size:15px; font-weight:800; border-radius:12px; margin-bottom:12px; }
.alert-card { border:3px solid #ff3333; background:#2a0e0e; padding:18px; border-radius:18px; margin:12px 0; }
.best-card { border:3px solid #ff7a18; background:#241306; padding:18px; border-radius:18px; margin:12px 0; }
.source-card { border:2px solid #1677ff; background:#0e1726; padding:15px; border-radius:16px; margin:12px 0; }
.big { font-size:34px; font-weight:900; color:#ffb020; line-height:1.3; }
.alert-big { font-size:34px; font-weight:900; color:#ff5555; line-height:1.3; }
a.buy-link { display:block; text-align:center; background:#ffcc00; color:#111; padding:18px; border-radius:15px; font-size:24px; font-weight:900; text-decoration:none; margin:12px 0; }

/* MARU 현장용 프리미엄 블랙/골드 대시보드 */
.maru-gold-card {
  border:2px solid #d7aa38;
  background: radial-gradient(circle at 20% 0%, rgba(255,210,88,.18), transparent 28%), linear-gradient(180deg,#141414,#050505);
  border-radius:22px;
  padding:18px;
  margin:14px 0;
  box-shadow:0 0 22px rgba(215,170,56,.22);
}
.maru-gold-title {font-size:22px;font-weight:1000;color:#ffd15c;text-align:center;letter-spacing:-.3px;}
.maru-gold-main {font-size:42px;font-weight:1000;color:#fff;text-align:center;line-height:1.15;margin:8px 0;}
.maru-gold-combo {font-size:46px;font-weight:1000;color:#ffd15c;text-align:center;line-height:1.1;}
.maru-gold-sub {font-size:16px;color:#e9e1cc;text-align:center;line-height:1.55;}
.maru-metric-grid {display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:14px;}
.maru-metric {border:1px solid rgba(255,209,92,.45);background:#101010;border-radius:13px;padding:10px;text-align:center;}
.maru-metric-label {font-size:13px;color:#ffd15c;font-weight:900;}
.maru-metric-value {font-size:22px;color:#fff;font-weight:1000;}
.maru-info-grid {display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-top:12px;}
.maru-info {border:1px solid rgba(255,209,92,.35);background:#0d0d0d;border-radius:14px;padding:12px;font-size:15px;line-height:1.65;color:#eee;}
.maru-info b {color:#ffd15c;}
.maru-action-gold {display:block;text-align:center;background:linear-gradient(180deg,#ffe08a,#c89120);color:#101010 !important;padding:16px;border-radius:14px;font-size:24px;font-weight:1000;text-decoration:none;margin:12px 0;}
.maru-action-blue {display:block;text-align:center;background:linear-gradient(180deg,#1677ff,#084ec7);color:white !important;padding:16px;border-radius:14px;font-size:22px;font-weight:1000;text-decoration:none;margin:10px 0;}
.maru-red-banner {background:linear-gradient(180deg,#ff2b2b,#a70707);border-radius:14px;padding:13px;text-align:center;color:white;font-size:24px;font-weight:1000;margin:10px 0;}
.maru-manual-card {border:2px solid #d7aa38;background:linear-gradient(180deg,#111,#050505);border-radius:22px;padding:20px;margin:14px 0;box-shadow:0 0 20px rgba(215,170,56,.25);}
.maru-big-number {font-size:64px;font-weight:1000;color:#fff;text-align:center;line-height:1.05;}
.maru-big-won {font-size:44px;font-weight:1000;color:#ffd15c;text-align:center;}
@media (max-width:700px){
  .maru-gold-main{font-size:36px}.maru-gold-combo{font-size:40px}.maru-big-number{font-size:58px}.maru-metric-grid{grid-template-columns:repeat(3,1fr)}.maru-info-grid{grid-template-columns:repeat(2,1fr)}.maru-action-gold,.maru-action-blue{font-size:20px;padding:14px}
}

.good { color:#31d158; font-weight:900; }
.bad { color:#ff5555; font-weight:900; }
.warn { color:#ffd84d; font-weight:900; }
@media (max-width:700px){ .title-card{font-size:24px}.big,.alert-big{font-size:28px}.best-card,.alert-card{padding:14px} }

.super-alert {
  border: 4px solid #ff0000;
  background: linear-gradient(90deg, #290000, #5a0000, #290000);
  padding: 22px;
  border-radius: 20px;
  margin: 16px 0;
  animation: superFlash 0.75s infinite alternate;
  box-shadow: 0 0 24px rgba(255,0,0,.85);
}
.super-alert-title {
  font-size: 40px;
  font-weight: 1000;
  color: #fff200;
  line-height: 1.25;
}
.super-alert-body {
  font-size: 20px;
  color: #ffffff;
  line-height: 1.7;
  font-weight: 800;
}
.sms-alert {
  border: 3px solid #00ff90;
  background: #001f12;
  padding: 18px;
  border-radius: 18px;
  margin: 14px 0;
  box-shadow: 0 0 18px rgba(0,255,144,.55);
  color: #eafff4;
  font-family: monospace;
  white-space: pre-wrap;
  font-size: 17px;
}
@keyframes superFlash {
  from { filter: brightness(1); transform: scale(1); }
  to { filter: brightness(1.55); transform: scale(1.01); }
}


.watch-on {
  border: 3px solid #00ff90;
  background: #001d12;
  color: #eafff4;
  padding: 18px;
  border-radius: 18px;
  margin: 14px 0;
  box-shadow: 0 0 18px rgba(0,255,144,.45);
}
.watch-off {
  border: 3px solid #777;
  background: #181818;
  color: #ddd;
  padding: 18px;
  border-radius: 18px;
  margin: 14px 0;
}
.watch-title {
  font-size: 30px;
  font-weight: 1000;
}


.final-buy-card {
  border: 4px solid #22c55e;
  background: linear-gradient(135deg, #022c22, #064e3b);
  color: #ecfdf5;
  padding: 22px;
  border-radius: 20px;
  margin: 18px 0;
  box-shadow: 0 0 22px rgba(34,197,94,.45);
}
.final-hold-card {
  border: 4px solid #f59e0b;
  background: linear-gradient(135deg, #451a03, #78350f);
  color: #fffbeb;
  padding: 22px;
  border-radius: 20px;
  margin: 18px 0;
  box-shadow: 0 0 22px rgba(245,158,11,.45);
}
.final-stop-card {
  border: 4px solid #ef4444;
  background: linear-gradient(135deg, #450a0a, #7f1d1d);
  color: #fef2f2;
  padding: 22px;
  border-radius: 20px;
  margin: 18px 0;
  box-shadow: 0 0 22px rgba(239,68,68,.45);
}
.final-title {
  font-size: 34px;
  font-weight: 1000;
  margin-bottom: 12px;
}
.final-body {
  font-size: 19px;
  line-height: 1.75;
  font-weight: 750;
}
.report-box {
  border: 2px solid #38bdf8;
  background: #082f49;
  color: #e0f2fe;
  padding: 18px;
  border-radius: 18px;
  margin: 14px 0;
  line-height: 1.7;
}


.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(155px, 1fr));
  gap: 10px;
  margin: 14px 0;
}
.status-ok {
  border: 2px solid #22c55e;
  background: #052e16;
  color: #dcfce7;
  padding: 14px;
  border-radius: 16px;
}
.status-warn {
  border: 2px solid #f59e0b;
  background: #451a03;
  color: #fffbeb;
  padding: 14px;
  border-radius: 16px;
}
.status-bad {
  border: 2px solid #ef4444;
  background: #450a0a;
  color: #fee2e2;
  padding: 14px;
  border-radius: 16px;
}
.status-title {
  font-size: 15px;
  font-weight: 800;
  opacity: .9;
}
.status-value {
  font-size: 25px;
  font-weight: 1000;
}
.ultra-home {
  border: 4px solid #38bdf8;
  background: linear-gradient(135deg, #082f49, #0f172a);
  color: #e0f2fe;
  padding: 22px;
  border-radius: 22px;
  margin: 16px 0;
  box-shadow: 0 0 24px rgba(56,189,248,.40);
}
.ultra-home-title {
  font-size: 36px;
  font-weight: 1000;
  margin-bottom: 10px;
}
.ultra-home-body {
  font-size: 20px;
  line-height: 1.75;
  font-weight: 760;
}

</style>
""", unsafe_allow_html=True)

KRA_URLS = {
    "서울경마공원": "https://race.kra.co.kr/",
    "부산경남경마공원": "https://race.kra.co.kr/busanMain.do",
    "제주경마공원": "https://race.kra.co.kr/jejuMain.do",
}
KRA_MENUS = {
    "오늘의 경주": "https://race.kra.co.kr/todayrace/todayrace.do",
    "출마표": "https://race.kra.co.kr/chulmainfo/chulmaInfoList.do",
    "경주결과": "https://race.kra.co.kr/raceScore/scoretableScoreList.do",
    "경주마 정보": "https://race.kra.co.kr/racehorse/profileHorseList.do",
    "기수 정보": "https://race.kra.co.kr/racehorse/profileJockeyList.do",
}


def make_safe_sample(rows, columns):
    safe = []
    n = len(columns)
    for row in rows:
        row = list(row)
        if len(row) < n:
            row = row + [None] * (n - len(row))
        elif len(row) > n:
            row = row[:n]
        safe.append(row)
    return pd.DataFrame(safe, columns=columns)

COLUMNS = ["경주일","경마장","경주번호","출발시간","경주명","거리","등급","경주마","마번","줄","기수","이전기수","조교사","마주","주행습성","마령","부담중량","초기배당","현재배당","직전순위","지지난순위","순위","착차","초반위치","중반위치","4코너위치","결승위치","혈통점수","스피드점수","지구력점수","거리적성","컨디션점수","현재체중","평균체중","체중증감","출전간격일","최근5전","기수승률","마주승률","조교사승률","조교상태","선행가능성","마체상태","초반스피드","막판탄력","게이트안정","주로상태"]

sample = make_safe_sample([
["2026-06-09","서울경마공원",1,"10:45","2세 신마전",1000,"신마","번개질주",1,"1째줄","김철수","김철수","박조교","박마주","선행",3,55,2.2,1.8,2,1,1,92,93,86,94,90,-1,14,"2-1-1-2-1",22,16,18,"상승","높음","양호",9,8,9,"건조"],
["2026-06-09","서울경마공원",1,"10:45","2세 신마전",1000,"신마","태양왕",2,"2째줄","이영호","박기수","최조교","최마주","선입",4,56,7.5,5.1,1,3,3,78,84,72,79,78,2,21,"1-3-4-2-3",15,10,9,"보통","중간","보통",7,6,5,"양호"],
["2026-06-09","서울경마공원",1,"10:45","2세 신마전",1000,"신마","백호질주",5,"5째줄","이영호","이영호","강조교","강마주","추입",5,55.5,10.8,8.9,1,2,2,88,79,91,89,87,-2,18,"3-2-2-1-1",21,16,15,"상승","중간","양호",8,9,7,"건조"],
["2026-06-09","서울경마공원",1,"10:45","2세 신마전",1000,"신마","흑룡",4,"4째줄","최강준","낮은기수","이조교","이마주","선입",6,56.5,13.2,11.5,2,4,4,82,73,88,85,80,1,18,"5-4-3-2-2",12,11,10,"상승","낮음","보통",6,8,5,"다습"],
["2026-06-09","서울경마공원",1,"10:45","2세 신마전",1000,"신마","한라질주",8,"8째줄","오한라","오한라","오조교","오마주","선행",4,54,14.0,9.6,2,2,5,81,87,77,82,81,1,20,"4-3-2-2-1",16,12,8,"상승","높음","양호",8,6,8,"건조"],
["2026-06-09","서울경마공원",1,"10:45","2세 신마전",1000,"신마","청풍",9,"9째줄","신바람","신바람","문조교","문마주","자유",8,57.5,18.0,16.2,7,6,6,66,71,60,63,58,8,105,"7-8-6-6-5",6,4,5,"하락","낮음","불안",4,4,3,"다습"],
["2026-06-09","서울경마공원",1,"10:45","2세 신마전",1000,"신마","숨은강자",6,"6째줄","한승부","한승부","최조교","최마주","선입",5,54.5,15.5,9.8,3,5,1,84,80,84,88,85,-3,16,"6-5-3-3-1",14,13,16,"상승","중간","양호",7,8,7,"건조"],
["2026-06-09","서울경마공원",1,"10:45","2세 신마전",1000,"신마","막판왕",7,"7째줄","장거리","장거리","김조교","장마주","추입",7,55,12.5,8.2,4,6,2,85,76,94,91,86,-2,21,"7-6-4-2-1",13,12,14,"상승","낮음","양호",5,10,6,"건조"],
["2026-06-09","서울경마공원",2,"11:15","국산 5등급",1300,"5등급","천둥",3,"3째줄","강기수","강기수","강조교","강마주","선행",3,55,3.8,3.1,2,3,1,86,88,80,87,84,-1,17,"4-3-2-2-1",17,13,15,"상승","높음","양호",8,7,8,"건조"],
["2026-06-09","서울경마공원",2,"11:15","국산 5등급",1300,"5등급","불꽃",6,"6째줄","박기수","낮은기수","박조교","박마주","선입",4,56,9.0,7.4,4,5,2,82,80,86,85,82,-2,19,"6-5-4-3-2",13,12,13,"상승","중간","양호",7,8,7,"건조"],
["2026-06-09","서울경마공원",2,"11:15","국산 5등급",1300,"5등급","바람검",10,"10째줄","오기수","오기수","오조교","오마주","추입",8,54,20.0,14.8,6,7,3,80,74,92,88,80,-3,20,"8-7-6-4-3",11,10,11,"상승","낮음","양호",5,10,5,"건조"],
], COLUMNS)
sample["경주일"] = pd.to_datetime(sample["경주일"])

if "df" not in st.session_state:
    st.session_state.df = sample.copy()
if "raw_tables" not in st.session_state:
    st.session_state.raw_tables = []
if "source_status" not in st.session_state:
    st.session_state.source_status = "샘플 데이터 대기"
if "watch_mode_on" not in st.session_state:
    st.session_state.watch_mode_on = False
if "watch_start_time" not in st.session_state:
    st.session_state.watch_start_time = ""
if "watch_stop_reason" not in st.session_state:
    st.session_state.watch_stop_reason = ""

if "auto_loaded" not in st.session_state:
    st.session_state.auto_loaded = False
if "auto_analysis_status" not in st.session_state:
    st.session_state.auto_analysis_status = "자동 분석 대기"
if "auto_load_log" not in st.session_state:
    st.session_state.auto_load_log = ""
if "alarm_on" not in st.session_state:
    st.session_state.alarm_on = False
if "review_records" not in st.session_state:
    st.session_state.review_records = detailed_review_records_default() if 'detailed_review_records_default' in globals() else []

if "race_results" not in st.session_state:
    st.session_state.race_results = pd.DataFrame(columns=[
        "날짜","경마장","경주","경주번호","1착","2착","3착","최종배당_삼복승","최종배당_삼쌍승","기록","주로상태"
    ])
if "result_compare_log" not in st.session_state:
    st.session_state.result_compare_log = pd.DataFrame(columns=[
        "날짜","경마장","경주","방식","조합","예상배당","최종배당","판정","구매여부","예상환급","실제환급","메모"
    ])
if "auto_recommend_text_log" not in st.session_state:
    st.session_state.auto_recommend_text_log = pd.DataFrame(columns=[
        "날짜","경마장","경주번호","출발시간","추천문구","방식","조합","예상배당","조합점수","위험합계","신뢰등급","상태"
    ])
if "parsed_result_text_log" not in st.session_state:
    st.session_state.parsed_result_text_log = pd.DataFrame(columns=[
        "날짜","경마장","경주번호","1착","2착","3착","최종배당_삼복승","최종배당_삼쌍승","원문"
    ])

if "observation_records" not in st.session_state:
    st.session_state.observation_records = pd.DataFrame(columns=[
        "날짜","시간","경마장","경주","방식","조합","예상배당","조합점수","신뢰등급",
        "운영판정","관찰결과","실제결과","구매여부","메모"
    ])
if "learning_memory" not in st.session_state:
    st.session_state.learning_memory = pd.DataFrame(columns=[
        "날짜","유형","요인","방향","가중치","근거","적용여부"
    ])
if "daily_purchase_count" not in st.session_state:
    st.session_state.daily_purchase_count = 0
if "daily_purchase_date" not in st.session_state:
    st.session_state.daily_purchase_date = pd.Timestamp.today().strftime("%Y-%m-%d")

if "records" not in st.session_state:
    st.session_state.records = pd.DataFrame([
        {"날짜":"2026-06-09","시간":"10:45","경마장":"서울","경주":"1R","발견":"30배 발견","결과":"적중","수익":290000,"방식":"삼복승","조합":"5-6-8","예상배당":34.2,"공통요인":"체중 안정|출전간격 안정|최근 순위 상승"},
        {"날짜":"2026-06-09","시간":"11:15","경마장":"서울","경주":"2R","발견":"30배 발견","결과":"실패","수익":-10000,"방식":"삼쌍승","조합":"3-6-10","예상배당":31.8,"공통요인":"외곽게이트|정확순서 실패"},
    ])

def ensure(df):
    d = df.copy()
    for c in COLUMNS:
        if c not in d.columns:
            d[c] = np.nan
    for c in ["경주번호","거리","마번","마령","부담중량","초기배당","현재배당","직전순위","지지난순위","순위","착차","초반위치","중반위치","4코너위치","결승위치","혈통점수","스피드점수","지구력점수","거리적성","컨디션점수","현재체중","평균체중","체중증감","출전간격일","기수승률","마주승률","조교사승률","초반스피드","막판탄력","게이트안정"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["줄"] = d.apply(lambda r: r["줄"] if pd.notna(r["줄"]) and str(r["줄"]).strip() else (f"{int(r['마번'])}째줄" if pd.notna(r["마번"]) else ""), axis=1)
    d["배당변화율"] = ((d["현재배당"] - d["초기배당"]) / d["초기배당"] * 100).round(1)
    return d

@st.cache_data(ttl=120)
def fetch_kra_tables(url):
    try:
        res = requests.get(url, timeout=10, headers={"User-Agent":"Mozilla/5.0"})
        res.raise_for_status()
        return True, pd.read_html(res.text), ""
    except Exception as e:
        return False, [], str(e)

def normalize_kra(t, course):
    df = t.copy()
    df.columns = [str(c).replace("\n"," ").strip() for c in df.columns]
    def pick(keys):
        for k in keys:
            for c in df.columns:
                if k in c:
                    return c
        return None
    horse, num = pick(["마명","경주마","말명"]), pick(["마번","번호"])
    if horse is None or num is None:
        return None
    out = pd.DataFrame()
    out["경주일"] = pd.Timestamp.today().normalize()
    out["경마장"] = course
    out["경주번호"] = 1
    out["출발시간"] = ""
    out["경주명"] = "KRA 원본표"
    out["거리"] = np.nan
    out["등급"] = ""
    out["경주마"] = df[horse].astype(str)
    out["마번"] = pd.to_numeric(df[num].astype(str).str.extract(r"(\d+)")[0], errors="coerce")
    out["줄"] = out["마번"].apply(lambda x: f"{int(x)}째줄" if pd.notna(x) else "")
    out["기수"] = df[pick(["기수"])].astype(str) if pick(["기수"]) else ""
    out["이전기수"] = out["기수"]
    out["조교사"] = df[pick(["조교사"])].astype(str) if pick(["조교사"]) else ""
    out["마주"] = ""
    out["주행습성"] = ""
    out["마령"] = 4
    out["부담중량"] = np.nan
    out["초기배당"] = np.nan
    out["현재배당"] = np.nan
    out["직전순위"] = np.nan
    out["지지난순위"] = np.nan
    out["순위"] = np.nan
    out["착차"] = np.nan
    out["초반위치"] = np.nan
    out["중반위치"] = np.nan
    out["4코너위치"] = np.nan
    out["결승위치"] = np.nan
    out["혈통점수"] = 65
    out["스피드점수"] = 65
    out["지구력점수"] = 65
    out["거리적성"] = 65
    out["컨디션점수"] = 65
    out["현재체중"] = 0
    out["평균체중"] = 0
    out["체중증감"] = 0
    out["출전간격일"] = 18
    out["최근5전"] = ""
    out["기수승률"] = 10
    out["마주승률"] = 10
    out["조교사승률"] = 10
    out["조교상태"] = "보통"
    out["선행가능성"] = "중간"
    out["마체상태"] = "보통"
    out["초반스피드"] = 6
    out["막판탄력"] = 6
    out["게이트안정"] = 6
    out["주로상태"] = "양호"
    return out[COLUMNS]

def vibrate():
    components.html("""
    <script>
    try {
      navigator.vibrate && navigator.vibrate([500,150,500,150,800]);
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator(); const gain = ctx.createGain();
      osc.connect(gain); gain.connect(ctx.destination);
      osc.frequency.value = 880; gain.gain.value = 0.08;
      osc.start(); setTimeout(()=>{osc.stop();ctx.close();}, 800);
    } catch(e) {}
    </script>
    """, height=0)

def recent5_score(text):
    vals = [int(x) for x in re.findall(r"\d+", str(text))][-5:]
    if not vals: return 55
    score = 50
    for v in vals:
        score += 15 if v==1 else 10 if v==2 else 7 if v==3 else 2 if v<=5 else -5
    if len(vals) >= 3 and vals[-1] < vals[-3]: score += 10
    if len(vals) and vals[-1] <= 3: score += 8
    return max(0, min(100, score))

def weight_score(x):
    try: d=abs(float(x))
    except: return 70
    return 90 if d<=3 else 65 if d<=7 else 35

def layoff_score(x):
    try: d=float(x)
    except: return 65
    return 90 if 14<=d<=42 else 65 if 43<=d<=90 else 35 if d>90 else 60

def gate_distance_score(gate, dist):
    try: g, d = int(gate), int(dist)
    except: return 65
    if d <= 1300: return 92 if g<=4 else 75 if g<=7 else 45
    if d >= 1700: return 78 if g<=8 else 60
    return 85 if g<=6 else 68 if g<=9 else 50

def jockey_change_score(row):
    rate = pd.to_numeric(row.get("기수승률",10), errors="coerce")
    if pd.isna(rate): rate=10
    prev, cur = str(row.get("이전기수","")).strip(), str(row.get("기수","")).strip()
    if prev and cur and prev != "nan" and prev != cur:
        return 88 if rate>=15 else 40 if rate<8 else 65
    return min(90, max(45, rate*4))

def confidence_grade(v):
    try: v=float(v)
    except: v=0
    return "🟢 A등급 실전 가능" if v>=82 else "🟡 B등급 소액" if v>=74 else "🔴 C등급 관찰" if v>=66 else "⚫ D등급 보류"

def risk_list(row):
    risks=[]
    if pd.notna(row["마번"]) and row["마번"]>=9: risks.append("외곽게이트")
    if pd.notna(row["거리적성"]) and row["거리적성"]<78: risks.append("거리 적성 부족")
    if pd.notna(row["체중증감"]) and abs(row["체중증감"])>=8: risks.append("체중 ±8kg 이상")
    elif pd.notna(row["체중증감"]) and abs(row["체중증감"])>=4: risks.append("체중 변화 주의")
    if pd.notna(row["출전간격일"]) and row["출전간격일"]>90: risks.append("3개월 이상 공백")
    if pd.notna(row["기수승률"]) and row["기수승률"]<10: risks.append("기수 약함")
    if str(row["마체상태"])!="양호": risks.append("마체 불안")
    if str(row["조교상태"])=="하락": risks.append("조교 하락")
    return risks


def weather_track_score(row, weather_type="보통", sand_status="보통"):
    score = 70
    notes = []

    style = str(row.get("주행습성", ""))
    horse_no = pd.to_numeric(row.get("마번", 0), errors="coerce")
    dist = pd.to_numeric(row.get("거리", 0), errors="coerce")
    weight_delta = pd.to_numeric(row.get("체중증감", 0), errors="coerce")
    stamina = pd.to_numeric(row.get("지구력점수", 60), errors="coerce")
    speed = pd.to_numeric(row.get("스피드점수", 60), errors="coerce")
    condition = pd.to_numeric(row.get("컨디션점수", 60), errors="coerce")
    interval = pd.to_numeric(row.get("출전간격일", 18), errors="coerce")

    if pd.isna(horse_no): horse_no = 0
    if pd.isna(dist): dist = 0
    if pd.isna(weight_delta): weight_delta = 0
    if pd.isna(stamina): stamina = 60
    if pd.isna(speed): speed = 60
    if pd.isna(condition): condition = 60
    if pd.isna(interval): interval = 18

    # Weather
    if weather_type == "비":
        if style in ["선행", "선입"]:
            score += 8
            notes.append("비/젖은주로 선행·선입 가산")
        if style == "추입":
            score -= 7
            notes.append("비/젖은주로 추입 감점")
        if horse_no <= 4 and dist <= 1300:
            score += 5
            notes.append("단거리 안쪽 게이트 가산")
        if stamina >= 85:
            score += 4
            notes.append("지구력형 가산")
    elif weather_type == "무더움":
        if abs(weight_delta) >= 4:
            score -= 8
            notes.append("무더위 체중변화 감점")
        if interval < 14:
            score -= 6
            notes.append("무더위 짧은 출전간격 감점")
        if stamina >= 85 and condition >= 80:
            score += 8
            notes.append("무더위 체력·컨디션 가산")
    elif weather_type == "추움":
        if speed < 75:
            score -= 4
            notes.append("추운날 초반스피드 부족 감점")
        if condition >= 82:
            score += 6
            notes.append("추운날 컨디션 양호 가산")
        if style == "선행" and speed >= 85:
            score += 5
            notes.append("추운날 빠른 선행 가산")

    # Sand / track special status
    if sand_status == "모래 새로교체":
        # Historical track patterns less reliable; power/stamina get boosted.
        score -= 4
        notes.append("모래교체 기존기록 신뢰도 감점")
        if stamina >= 85:
            score += 8
            notes.append("새 모래 파워·지구력형 가산")
        if speed >= 88 and style == "선행":
            score += 4
            notes.append("새 모래 초반 자리잡기 가산")
    elif sand_status == "모래 깊음":
        if stamina >= 85:
            score += 8
            notes.append("깊은 모래 지구력 가산")
        if speed < 75:
            score -= 5
            notes.append("깊은 모래 추진력 부족 감점")
    elif sand_status == "모래 가벼움":
        if speed >= 85:
            score += 8
            notes.append("가벼운 모래 스피드형 가산")
        if style == "추입":
            score += 3
            notes.append("가벼운 모래 막판탄력 가능")
    elif sand_status == "안쪽 무거움":
        if horse_no <= 4:
            score -= 8
            notes.append("안쪽 무거움 안쪽마 감점")
        elif horse_no >= 6:
            score += 4
            notes.append("안쪽 무거움 바깥 전개 가산")
    elif sand_status == "바깥쪽 무거움":
        if horse_no >= 8:
            score -= 8
            notes.append("바깥쪽 무거움 외곽마 감점")
        elif horse_no <= 5:
            score += 4
            notes.append("바깥쪽 무거움 안쪽 전개 가산")

    return max(0, min(100, score)), " / ".join(notes) if notes else "특수보정 없음"


def age_score(age, dist):
    try:
        a = float(age)
        d = float(dist)
    except Exception:
        return 70
    if 3 <= a <= 5:
        return 90
    if 6 <= a <= 7:
        return 75 if d < 1700 else 70
    if a >= 8:
        return 55 if d < 1700 else 42
    return 65

def pace_prediction_for_race(g):
    styles = g["주행습성"].astype(str)
    lead_count = int(styles.isin(["선행"]).sum())
    front_count = int(styles.isin(["선행","선입"]).sum())
    if lead_count >= 5:
        pace = "초반 과열"
        adv = "추입마 유리"
        note = "선행형 5두 이상 → 앞선 경쟁 심함"
    elif lead_count <= 1:
        pace = "느린 페이스"
        adv = "선행마 유리"
        note = "선행형 1~2두 → 앞에서 편하게 갈 가능성"
    else:
        pace = "보통 페이스"
        adv = "선입/능력마 유리"
        note = "선행·선입 균형"
    return pace, adv, note, lead_count, front_count

def odds_surge_score(row):
    try:
        open_o = float(row.get("초기배당", 0))
        cur_o = float(row.get("현재배당", 0))
    except Exception:
        return 65, "배당정보 부족"
    if open_o <= 0 or cur_o <= 0:
        return 65, "배당정보 부족"
    chg = (cur_o - open_o) / open_o * 100
    if chg <= -30:
        return 88, "인기 급상승 - 내부 정보/시장 관심 가능"
    if chg >= 45:
        return 38, "인기 급하락 - 컨디션 이상 가능"
    if chg >= 25:
        return 52, "인기 하락 주의"
    if chg <= -15:
        return 78, "배당 하락 관심 유입"
    return 65, "배당 안정"

def course_key(row):
    try:
        return f"{row.get('경마장','')}-{int(row.get('거리',0))}m"
    except Exception:
        return f"{row.get('경마장','')}-{row.get('거리','')}m"

def failed_blacklist_score(row, records):
    if records is None or len(records) == 0:
        return 70, "블랙리스트 없음"
    recent_fail = records[records["결과"].astype(str) == "실패"].tail(100)
    fail_text = " ".join(recent_fail.astype(str).agg(" ".join, axis=1).tolist())
    penalties = []
    score = 80
    if "외곽" in fail_text and pd.to_numeric(row.get("마번",0), errors="coerce") >= 9:
        score -= 18
        penalties.append("실패패턴: 외곽게이트")
    if "비" in fail_text and str(row.get("주로상태","")) in ["다습","불량"]:
        score -= 10
        penalties.append("실패패턴: 비/젖은주로")
    if "기수" in fail_text and pd.to_numeric(row.get("기수승률",10), errors="coerce") < 10:
        score -= 12
        penalties.append("실패패턴: 기수 약함")
    if "장거리" in fail_text and pd.to_numeric(row.get("거리",0), errors="coerce") >= 1700 and pd.to_numeric(row.get("거리적성",60), errors="coerce") < 78:
        score -= 15
        penalties.append("실패패턴: 장거리 약함")
    if "체중" in fail_text and abs(pd.to_numeric(row.get("체중증감",0), errors="coerce")) >= 4:
        score -= 12
        penalties.append("실패패턴: 체중 변화")
    return max(20, min(100, score)), " / ".join(penalties) if penalties else "실패패턴 감점 없음"

def course_stats(df):
    d = ensure(df)
    if len(d) == 0:
        return pd.DataFrame()
    d["코스"] = d.apply(course_key, axis=1)
    out = d.groupby("코스").agg(
        출전수=("코스","count"),
        평균배당=("현재배당","mean"),
        평균순위=("순위","mean"),
        우승수=("순위", lambda x: int((pd.to_numeric(x, errors="coerce")==1).sum())),
        평균게이트=("마번","mean"),
        평균거리적성=("거리적성","mean")
    ).reset_index()
    out["코스승률"] = (out["우승수"] / out["출전수"] * 100).round(1)
    return out.sort_values("코스", ascending=True)

def self_learning_summary(records):
    if records is None or len(records) == 0:
        return pd.DataFrame(columns=["구분","건수","수익합계"])
    r = records.tail(100).copy()
    r["수익"] = pd.to_numeric(r["수익"], errors="coerce").fillna(0)
    out = r.groupby("결과")["수익"].agg(["count","sum"]).reset_index()
    out.columns = ["구분","건수","수익합계"]
    return out

def horse_engine(df, records):
    h = ensure(df)
    h["인기순위"] = h.groupby(["경마장","경주번호"])["현재배당"].transform(lambda s: pd.to_numeric(s, errors="coerce").rank(method="min", ascending=True).fillna(99)).astype(int)
    h["인기유형"] = h["인기순위"].apply(lambda x: "인기마" if x<=3 else "중배당" if x<=7 else "복병")
    h["최근5경기흐름"] = h["최근5전"].apply(recent5_score)
    h["체중변화점수"] = h["체중증감"].apply(weight_score)
    h["출전간격점수"] = h["출전간격일"].apply(layoff_score)
    h["기수교체점수"] = h.apply(jockey_change_score, axis=1)
    h["거리전환점수"] = h["거리적성"].fillna(60).clip(0,100)
    h["게이트거리점수"] = h.apply(lambda r: gate_distance_score(r["마번"], r["거리"]), axis=1)
    h["주로상태점수"] = h["주로상태"].apply(lambda x: {"건조":82,"양호":78,"다습":65,"불량":45}.get(str(x),65))
    wt = h.apply(lambda r: weather_track_score(r, weather_type, sand_status), axis=1)
    h["날씨주로특수점수"] = [x[0] for x in wt]
    h["날씨주로메모"] = [x[1] for x in wt]
    h["ROI보정점수"] = 70
    h["배당가치"] = h["현재배당"].apply(lambda x: 95 if pd.notna(x) and 6<=x<=15 else 78 if pd.notna(x) and 3<=x<6 else 65 if pd.notna(x) and 15<x<=22 else 35)
    h["마령점수"] = h.apply(lambda r: age_score(r.get("마령",4), r.get("거리",0)), axis=1)
    odds_calc = h.apply(odds_surge_score, axis=1)
    h["배당급변점수"] = [x[0] for x in odds_calc]
    h["배당급변메모"] = [x[1] for x in odds_calc]
    bl_calc = h.apply(lambda r: failed_blacklist_score(r, records), axis=1)
    h["실패블랙점수"] = [x[0] for x in bl_calc]
    h["실패블랙메모"] = [x[1] for x in bl_calc]
    pace_rows = []
    for (cc, rr), gg in h.groupby(["경마장","경주번호"]):
        pace, adv, note, lead_cnt, front_cnt = pace_prediction_for_race(gg)
        for idx in gg.index:
            pace_rows.append((idx, pace, adv, note, lead_cnt, front_cnt))
    pace_df = pd.DataFrame(pace_rows, columns=["idx","페이스예상","페이스유리","페이스메모","선행마수","선행선입수"]).set_index("idx")
    h = h.join(pace_df)
    h["페이스점수"] = h.apply(lambda r:
        88 if (r["페이스유리"] == "선행마 유리" and str(r["주행습성"]) == "선행") else
        86 if (r["페이스유리"] == "추입마 유리" and str(r["주행습성"]) == "추입") else
        78 if (r["페이스유리"] == "선입/능력마 유리" and str(r["주행습성"]) in ["선입","선행"]) else
        62, axis=1)

    h["인기마제거점수"] = h["인기순위"].apply(lambda x: 45 if x<=3 else 85 if x<=8 else 75)
    h["위험요인"] = h.apply(lambda r: " / ".join(risk_list(r)) if risk_list(r) else "큰 위험요인 적음", axis=1)
    h["위험개수"] = h.apply(lambda r: len(risk_list(r)), axis=1)

    h["핵심점수"] = (
        h["혈통점수"].fillna(60)*.08 + h["스피드점수"].fillna(60)*.10 + h["지구력점수"].fillna(60)*.10 +
        h["컨디션점수"].fillna(60)*.10 + h["최근5경기흐름"]*.14 + h["배당가치"]*.08 +
        h["출전간격점수"]*.08 + h["게이트거리점수"]*.06 + h["인기마제거점수"]*.05 +
        h["페이스점수"]*.08 + h["마령점수"]*.05 + h["배당급변점수"]*.04 + h["실패블랙점수"]*.04 - h["위험개수"]*3
    ).round(1).clip(0,100)

    h["최종실전점수"] = (
        h["핵심점수"]*.55 + h["기수교체점수"]*.10 + h["거리전환점수"]*.10 + h["체중변화점수"]*.05 +
        h["주로상태점수"]*.05 + h["날씨주로특수점수"]*.07 + h["ROI보정점수"]*.04 + h["최근5경기흐름"]*.04
    ).round(1).clip(0,100)
    h["최종판정"] = h["최종실전점수"].apply(confidence_grade)

    h["1착점수"] = (h["최종실전점수"]*.55 + h["최근5경기흐름"]*.20 + h["게이트거리점수"]*.15 + h["기수교체점수"]*.10 - h["위험개수"]*3).round(1).clip(0,100)
    h["2착점수"] = (h["최종실전점수"]*.45 + h["지구력점수"].fillna(60)*.20 + h["체중변화점수"]*.15 + h["배당가치"]*.20 - h["위험개수"]*2).round(1).clip(0,100)
    h["3착점수"] = (h["최종실전점수"]*.32 + h["배당가치"]*.30 + h["막판탄력"].fillna(5)*10*.20 + h["거리전환점수"]*.18 - h["위험개수"]*2).round(1).clip(0,100)
    return h.sort_values("최종실전점수", ascending=False)

def estimate_tri(a,b,c):
    raw = a["현재배당"]*.48 + b["현재배당"]*.36 + c["현재배당"]*.28
    premium = 1 + ((a["현재배당"]+b["현재배당"]+c["현재배당"])/36)
    return round(float(raw*premium*3.2),1)

def estimate_trio(a,b,c):
    raw = (a["현재배당"]+b["현재배당"]+c["현재배당"])/3
    premium = 1 + ((a["현재배당"]+b["현재배당"]+c["현재배당"])/42)
    return round(float(raw*premium*2.1),1)

def combo_engine(h, stake, target_return, max_rows):
    rows=[]
    need = target_return/stake
    for (course, race_no), g in h.groupby(["경마장","경주번호"]):
        g = g.dropna(subset=["마번","현재배당"])
        if len(g)<5: continue
        for a,b,c in itertools.permutations(g.index,3):
            h1,h2,h3 = g.loc[a],g.loc[b],g.loc[c]
            if h1["1착점수"]<64 or h2["2착점수"]<58 or h3["3착점수"]<54: continue
            odds=estimate_tri(h1,h2,h3)
            nums=[int(h1["마번"]),int(h2["마번"]),int(h3["마번"])]
            pop_trap = "인기마 과다 - 배당 죽음" if all(n<=3 for n in nums) else "복병 포함 - 실전 배당" if any(n>=6 for n in nums) else "보통"
            judge = "🚀 120배 대박조합" if odds>=120 else "💰 60배 고수익조합" if odds>=60 else "🔥 30배 실전조합" if odds>=need else "👀 관찰" if odds>=20 else "⛔ 보류"
            score = round(h1["1착점수"]*.35+h2["2착점수"]*.24+h3["3착점수"]*.20+min(odds,120)*.13-(h1["위험개수"]+h2["위험개수"]+h3["위험개수"])*2.3,1)
            rows.append({"판정":judge,"경마장":course,"경주번호":race_no,"출발시간":h1["출발시간"],"방식":"삼쌍승","1착":f"{nums[0]}번 {h1['경주마']}","2착":f"{nums[1]}번 {h2['경주마']}","3착":f"{nums[2]}번 {h3['경주마']}","예상배당":odds,"투자금":stake,"예상환급":int(stake*odds),"예상순수익":int(stake*odds-stake),"조합점수":score,"신뢰등급":confidence_grade(score),"인기마제거판정":pop_trap,"위험합계":int(h1["위험개수"]+h2["위험개수"]+h3["위험개수"]),"메모":f"정확순서: {nums[0]}-{nums[1]}-{nums[2]}"})
        for a,b,c in itertools.combinations(g.index,3):
            h1,h2,h3 = g.loc[a],g.loc[b],g.loc[c]
            odds=estimate_trio(h1,h2,h3)
            if odds<15: continue
            nums=sorted([int(h1["마번"]),int(h2["마번"]),int(h3["마번"])])
            pop_trap = "인기마 과다 - 배당 죽음" if all(n<=3 for n in nums) else "복병 포함 - 실전 배당" if any(n>=6 for n in nums) else "보통"
            judge = "🚀 120배 대박조합" if odds>=120 else "💰 60배 고수익조합" if odds>=60 else "🔥 30배 실전조합" if odds>=need else "👀 관찰" if odds>=20 else "⛔ 보류"
            score = round(np.mean([h1["1착점수"],h2["2착점수"],h3["3착점수"]])*.62+min(odds,90)*.18+max([h1["3착점수"],h2["3착점수"],h3["3착점수"]])*.20-(h1["위험개수"]+h2["위험개수"]+h3["위험개수"])*2,1)
            names=" / ".join([f"{int(x['마번'])}번 {x['경주마']}" for _,x in pd.DataFrame([h1,h2,h3]).iterrows()])
            rows.append({"판정":judge,"경마장":course,"경주번호":race_no,"출발시간":h1["출발시간"],"방식":"삼복승","1착":"순서무관","2착":names,"3착":"","예상배당":odds,"투자금":stake,"예상환급":int(stake*odds),"예상순수익":int(stake*odds-stake),"조합점수":score,"신뢰등급":confidence_grade(score),"인기마제거판정":pop_trap,"위험합계":int(h1["위험개수"]+h2["위험개수"]+h3["위험개수"]),"메모":f"순서무관: {'-'.join(map(str,nums))}"})
    out=pd.DataFrame(rows)
    if len(out):
        order={"🔥 30배 실전조합":0,"💰 60배 고수익조합":1,"🚀 120배 대박조합":2,"👀 관찰":3,"⛔ 보류":4}
        out["정렬"]=out["판정"].map(order).fillna(9)
        out=out.sort_values(["정렬","조합점수","예상배당"], ascending=[True,False,False]).drop(columns=["정렬"]).head(max_rows)
    return out

def roi_summary(records):
    r=records.copy()
    bet=r[r["결과"].isin(["적중","실패"])]
    invested=len(bet)*10000
    profit=int(pd.to_numeric(bet["수익"], errors="coerce").fillna(0).sum())
    returned=invested+profit
    roi=round(returned/invested*100,1) if invested else 0
    return invested, returned, profit, roi


def confidence_percent(score, risk_count=0):
    try:
        s = float(score)
    except Exception:
        s = 0
    conf = s + 5
    conf -= int(risk_count) * 4
    return int(max(0, min(98, round(conf))))

def star_rating(conf):
    if conf >= 90:
        return "★★★★★"
    if conf >= 80:
        return "★★★★☆"
    if conf >= 70:
        return "★★★☆☆"
    if conf >= 60:
        return "★★☆☆☆"
    return "★☆☆☆☆"

def red_warning_list(row):
    warnings = []
    try:
        if float(row.get("체중증감", 0)) <= -12:
            warnings.append("⚠️ 체중 -12kg 이상 급감")
        elif abs(float(row.get("체중증감", 0))) >= 8:
            warnings.append("⚠️ 체중 ±8kg 이상")
    except Exception:
        pass

    try:
        if float(row.get("출전간격일", 0)) >= 120:
            warnings.append("⚠️ 4개월 이상 공백")
        elif float(row.get("출전간격일", 0)) >= 90:
            warnings.append("⚠️ 3개월 이상 공백")
    except Exception:
        pass

    try:
        vals = [int(x) for x in re.findall(r"\d+", str(row.get("최근5전", "")))][-5:]
        if len(vals) >= 3 and vals[-1] > vals[0] and vals[-1] >= 6:
            warnings.append("⚠️ 최근 5경기 급하락")
    except Exception:
        pass

    try:
        if int(row.get("마번", 0)) >= 9:
            warnings.append("⚠️ 외곽 게이트")
    except Exception:
        pass

    try:
        if float(row.get("기수승률", 10)) < 8:
            warnings.append("⚠️ 기수 승률 낮음")
    except Exception:
        pass

    if str(row.get("마체상태", "")) == "불안":
        warnings.append("⚠️ 마체상태 불안")
    if str(row.get("조교상태", "")) == "하락":
        warnings.append("⚠️ 조교 하락")
    return warnings

def apply_confidence_and_warnings(horses_df):
    h = horses_df.copy()
    if len(h) == 0:
        return h
    h["빨간경고"] = h.apply(lambda r: " / ".join(red_warning_list(r)) if red_warning_list(r) else "위험요소 없음", axis=1)
    h["빨간경고수"] = h.apply(lambda r: len(red_warning_list(r)), axis=1)
    h["확신도"] = h.apply(lambda r: confidence_percent(r.get("최종실전점수", 0), r.get("빨간경고수", 0)), axis=1)
    h["추천별점"] = h["확신도"].apply(star_rating)
    def final_grade(r):
        if r["빨간경고수"] >= 3:
            return "⚫ D등급 보류"
        if r["확신도"] >= 90:
            return "🟢 A등급 실전 가능"
        if r["확신도"] >= 70:
            return "🟡 B등급 소액"
        if r["확신도"] >= 60:
            return "🔴 C등급 관찰"
        return "⚫ D등급 보류"
    h["확신등급"] = h.apply(final_grade, axis=1)
    return h

def today_rest_decision(combos_df, horses_df, target_odds):
    over30 = int((combos_df["예상배당"] >= target_odds).sum()) if combos_df is not None and len(combos_df) else 0
    hh = apply_confidence_and_warnings(horses_df)
    a_count = int((hh["확신등급"].astype(str).str.contains("A등급")).sum()) if len(hh) else 0
    red3 = int((hh["빨간경고수"] >= 3).sum()) if len(hh) else 0
    if over30 == 0 and a_count == 0:
        return "⛔ 오늘은 관망", "30배 후보가 없고 A등급도 없습니다."
    if red3 >= max(1, len(hh)//3):
        return "⛔ 오늘은 관망", "빨간 경고가 많은 경주입니다."
    if over30 >= 1 and a_count >= 1:
        return "🔥 실전 가능", "30배 후보와 A등급 후보가 있습니다."
    return "👀 소액/관찰", "후보는 있으나 확신도가 높지 않습니다."

def record_window_stats(records, n=100):
    if records is None or len(records) == 0:
        return {"기록수":0, "적중률":0, "ROI":0, "총투자":0, "총회수":0, "순수익":0}
    r = records.tail(n).copy()
    bet = r[r["결과"].isin(["적중","실패"])]
    if len(bet) == 0:
        return {"기록수":len(r), "적중률":0, "ROI":0, "총투자":0, "총회수":0, "순수익":0}
    hit = int((bet["결과"] == "적중").sum())
    invested = len(bet) * 10000
    profit = int(pd.to_numeric(bet["수익"], errors="coerce").fillna(0).sum())
    returned = invested + profit
    hit_rate = round(hit / len(bet) * 100, 1)
    roi = round(returned / invested * 100, 1) if invested else 0
    return {"기록수":len(bet), "적중률":hit_rate, "ROI":roi, "총투자":invested, "총회수":returned, "순수익":profit}

def failure_top10(records):
    if records is None or len(records) == 0:
        return pd.DataFrame(columns=["실패원인","건수"])
    fail = records[records["결과"] == "실패"].tail(500)
    factors = []
    for _, row in fail.iterrows():
        text = str(row.get("공통요인", ""))
        if text and text != "nan":
            factors += [x for x in text.split("|") if x]
    if not factors:
        return pd.DataFrame(columns=["실패원인","건수"])
    out = pd.Series(factors).value_counts().head(10).reset_index()
    out.columns = ["실패원인","건수"]
    return out



def margin_score(row):
    """
    착차 분석:
    순위만 보지 않고 얼마나 근소하게 졌는지/크게 졌는지 봅니다.
    착차가 0.2~0.5면 강한 가산, 3마신 이상이면 감점.
    """
    try:
        margin = float(row.get("착차", 0))
    except Exception:
        margin = 0
    try:
        rank = float(row.get("순위", 9))
    except Exception:
        rank = 9

    if rank == 1:
        return 92, "우승"
    if rank <= 3 and margin <= 0.5:
        return 88, "근소차 입상 - 강한 상승세"
    if rank <= 3 and margin <= 1.5:
        return 76, "입상권 양호"
    if margin >= 3:
        return 38, "착차 큼 - 과대평가 주의"
    return 62, "보통 착차"

def running_style_analysis(row):
    """
    초반/중반/4코너/결승 위치 변화로 전개 유형을 판단합니다.
    """
    vals = []
    for k in ["초반위치", "중반위치", "4코너위치", "결승위치"]:
        try:
            vals.append(float(row.get(k, 0)))
        except Exception:
            vals.append(0)
    if not vals or all(v == 0 for v in vals):
        return 65, "전개자료 부족"

    start, mid, corner, finish = vals
    score = 65
    notes = []

    if start >= 7 and finish <= 3:
        score += 20
        notes.append("막판 추입 강함")
    if start <= 2 and corner <= 2 and finish >= 5:
        score -= 18
        notes.append("초반만 빠르고 끝심 부족")
    if start <= 3 and finish <= 3:
        score += 12
        notes.append("선행 유지형")
    if corner - finish >= 3:
        score += 12
        notes.append("4코너 이후 탄력")
    if finish - corner >= 3:
        score -= 12
        notes.append("직선에서 무너짐")

    return max(0, min(100, score)), " / ".join(notes) if notes else "전개 보통"

def normal_weight_score(row):
    """
    말별 정상체중 범위 분석.
    평균체중이 있으면 평균 대비 이탈을 보고, 없으면 체중증감 기준으로 판단합니다.
    """
    try:
        current = float(row.get("현재체중", 0))
        avg = float(row.get("평균체중", 0))
    except Exception:
        current, avg = 0, 0

    if current > 0 and avg > 0:
        diff = current - avg
    else:
        try:
            diff = float(row.get("체중증감", 0))
        except Exception:
            diff = 0

    ad = abs(diff)
    if ad <= 3:
        return 92, f"정상체중 범위 diff {diff:+.1f}kg"
    if ad <= 7:
        return 66, f"체중 변화 주의 diff {diff:+.1f}kg"
    if diff <= -8:
        return 34, f"체중 급감 위험 diff {diff:+.1f}kg"
    return 45, f"체중 급증 위험 diff {diff:+.1f}kg"

def jockey_trainer_combo_stats(df):
    d = ensure(df)
    if len(d) == 0:
        return pd.DataFrame()
    d["기수조교사"] = d["기수"].astype(str) + " + " + d["조교사"].astype(str)
    out = d.groupby("기수조교사").agg(
        출전수=("기수조교사","count"),
        평균기수승률=("기수승률","mean"),
        평균조교사승률=("조교사승률","mean"),
        평균순위=("순위","mean"),
        우승수=("순위", lambda x: int((pd.to_numeric(x, errors="coerce")==1).sum())),
        평균배당=("현재배당","mean")
    ).reset_index()
    out["조합승률"] = (out["우승수"] / out["출전수"] * 100).round(1)
    out["기수조교사조합점수"] = (
        out["평균기수승률"].fillna(10)*2.2 +
        out["평균조교사승률"].fillna(10)*2.0 +
        out["조합승률"].fillna(0)*1.3 +
        (100 - out["평균순위"].fillna(6)*8)
    ).clip(0,100).round(1)
    return out.sort_values("기수조교사조합점수", ascending=False)

def combo_pair_score(row, combo_df):
    if combo_df is None or len(combo_df) == 0:
        return 70
    key = str(row.get("기수","")) + " + " + str(row.get("조교사",""))
    hit = combo_df[combo_df["기수조교사"] == key]
    if len(hit) == 0:
        return 70
    return float(hit.iloc[0]["기수조교사조합점수"])

def detailed_review_records_default():
    return pd.DataFrame([
        {"날짜":"2026-06-09","경마장":"서울","경주":"1R","예상조합":"5-6-8","실제조합":"5-2-8","결과":"실패","빠진말":"2번","실패원인":"2번 인기마 과소평가|6번 체중 -9kg 무시|외곽 전개 실패","수정규칙":"체중 급감 말 감점 강화"},
        {"날짜":"2026-06-09","경마장":"서울","경주":"2R","예상조합":"3-6-10","실제조합":"3-6-10","결과":"적중","빠진말":"","실패원인":"","수정규칙":"30~40배 삼복승 조합 유지"},
    ])

def review_failure_top(records):
    if records is None or len(records) == 0:
        return pd.DataFrame(columns=["복기원인","건수"])
    fail = records[records["결과"] == "실패"].copy()
    factors = []
    for _, row in fail.iterrows():
        factors += [x for x in str(row.get("실패원인","")).split("|") if x and x != "nan"]
    if not factors:
        return pd.DataFrame(columns=["복기원인","건수"])
    out = pd.Series(factors).value_counts().head(10).reset_index()
    out.columns = ["복기원인","건수"]
    return out

def add_review_plus_scores(horses_df, df, records):
    h = horses_df.copy()
    combo_df = jockey_trainer_combo_stats(df)

    margin_calc = h.apply(margin_score, axis=1)
    h["착차점수"] = [x[0] for x in margin_calc]
    h["착차메모"] = [x[1] for x in margin_calc]

    run_calc = h.apply(running_style_analysis, axis=1)
    h["전개점수"] = [x[0] for x in run_calc]
    h["전개메모"] = [x[1] for x in run_calc]

    weight_calc = h.apply(normal_weight_score, axis=1)
    h["정상체중점수"] = [x[0] for x in weight_calc]
    h["정상체중메모"] = [x[1] for x in weight_calc]

    h["기수조교사조합점수"] = h.apply(lambda r: combo_pair_score(r, combo_df), axis=1)

    # Review score adjustment
    h["복기강화점수"] = (
        h["착차점수"]*0.22 +
        h["전개점수"]*0.25 +
        h["정상체중점수"]*0.22 +
        h["기수조교사조합점수"]*0.21 +
        h.get("최종실전점수", 60)*0.10
    ).round(1).clip(0,100)

    h["최종실전점수"] = (
        h.get("최종실전점수", 60)*0.82 +
        h["복기강화점수"]*0.18
    ).round(1).clip(0,100)

    if "확신도" in h.columns:
        h["확신도"] = (h["확신도"]*0.85 + h["복기강화점수"]*0.15).round(0).astype(int).clip(0,98)

    return h



def reset_daily_purchase_count():
    today = pd.Timestamp.today().strftime("%Y-%m-%d")
    if st.session_state.get("daily_purchase_date", "") != today:
        st.session_state.daily_purchase_date = today
        st.session_state.daily_purchase_count = 0

def combo_identity(row):
    return f"{row.get('경마장','')}_{row.get('경주번호','')}_{row.get('방식','')}_{row.get('1착','')}_{row.get('2착','')}_{row.get('3착','')}_{row.get('예상배당','')}"

def auto_save_observations(combos_df, top_n=10):
    if combos_df is None or len(combos_df) == 0:
        return 0
    today = pd.Timestamp.today().strftime("%Y-%m-%d")
    obs = st.session_state.observation_records.copy()
    if "조합ID" not in obs.columns:
        obs["조합ID"] = ""

    c = combos_df.copy().head(top_n)
    new_rows = []
    existing = set(obs["조합ID"].astype(str).tolist())
    for _, row in c.iterrows():
        cid = combo_identity(row)
        if cid in existing:
            continue
        new_rows.append({
            "조합ID": cid,
            "날짜": today,
            "시간": row.get("출발시간",""),
            "경마장": row.get("경마장",""),
            "경주": f"{int(row.get('경주번호',0))}R" if pd.notna(row.get("경주번호", None)) else "",
            "방식": row.get("방식",""),
            "조합": f"{row.get('1착','')} / {row.get('2착','')} / {row.get('3착','')}",
            "예상배당": row.get("예상배당",0),
            "조합점수": row.get("조합점수",0),
            "신뢰등급": row.get("신뢰등급",""),
            "운영판정": row.get("운영판정", row.get("판정","")),
            "관찰결과": "결과대기",
            "실제결과": "",
            "구매여부": "미구매 관찰",
            "메모": row.get("메모","")
        })
    if new_rows:
        st.session_state.observation_records = pd.concat([obs, pd.DataFrame(new_rows)], ignore_index=True)
    return len(new_rows)

def mark_combo_as_purchased(best_row):
    reset_daily_purchase_count()
    today = pd.Timestamp.today().strftime("%Y-%m-%d")
    if st.session_state.daily_purchase_count >= daily_buy_limit:
        return False, f"오늘 실제 구매 제한 {daily_buy_limit}회에 도달했습니다."
    st.session_state.daily_purchase_count += 1
    new = pd.DataFrame([{
        "날짜": today,
        "시간": best_row.get("출발시간",""),
        "경마장": best_row.get("경마장",""),
        "경주": f"{int(best_row.get('경주번호',0))}R" if pd.notna(best_row.get("경주번호", None)) else "",
        "발견": best_row.get("판정",""),
        "결과": "구매대기",
        "수익": 0,
        "방식": best_row.get("방식",""),
        "조합": best_row.get("메모",""),
        "예상배당": best_row.get("예상배당",0),
        "공통요인": "실제구매"
    }])
    st.session_state.records = pd.concat([st.session_state.records, new], ignore_index=True)
    return True, "실제 구매 후보로 저장했습니다. 결과 나오면 적중/실패로 바꾸면 됩니다."

def update_learning_memory_from_records():
    rows = []
    today = pd.Timestamp.today().strftime("%Y-%m-%d")
    # Observations: missed/failed factors
    if "observation_records" in st.session_state and len(st.session_state.observation_records):
        obs = st.session_state.observation_records.copy()
        failed = obs[obs["관찰결과"].astype(str).isin(["실패","미적중","놓침"])] if "관찰결과" in obs.columns else pd.DataFrame()
        hit = obs[obs["관찰결과"].astype(str).isin(["적중","성공"])] if "관찰결과" in obs.columns else pd.DataFrame()
        if len(failed):
            rows.append({"날짜":today,"유형":"관찰실패","요인":"관찰 후보 실패 증가","방향":"감점","가중치":-3,"근거":f"{len(failed)}건","적용여부":"적용"})
        if len(hit):
            rows.append({"날짜":today,"유형":"관찰적중","요인":"미구매 관찰 후보 적중","방향":"가산","가중치":3,"근거":f"{len(hit)}건","적용여부":"적용"})
    if "records" in st.session_state and len(st.session_state.records):
        r = st.session_state.records.copy()
        fail = r[r["결과"].astype(str) == "실패"]
        win = r[r["결과"].astype(str) == "적중"]
        if len(fail):
            rows.append({"날짜":today,"유형":"구매실패","요인":"실제 구매 실패 패턴","방향":"감점","가중치":-5,"근거":f"{len(fail.tail(20))}건","적용여부":"적용"})
        if len(win):
            rows.append({"날짜":today,"유형":"구매적중","요인":"실제 구매 적중 패턴","방향":"가산","가중치":5,"근거":f"{len(win.tail(20))}건","적용여부":"적용"})
    if rows:
        mem = st.session_state.learning_memory.copy()
        st.session_state.learning_memory = pd.concat([mem, pd.DataFrame(rows)], ignore_index=True).drop_duplicates(subset=["날짜","유형","요인"], keep="last")

def learning_evolution_score():
    score = 50
    mem = st.session_state.learning_memory if "learning_memory" in st.session_state else pd.DataFrame()
    if len(mem):
        score += pd.to_numeric(mem["가중치"], errors="coerce").fillna(0).tail(30).sum()
    obs_count = len(st.session_state.observation_records) if "observation_records" in st.session_state else 0
    buy_count = len(st.session_state.records) if "records" in st.session_state else 0
    score += min(30, obs_count * 0.2 + buy_count * 0.5)
    return int(max(0, min(100, score)))


@st.cache_data(ttl=120, show_spinner=False)
def server_side_heavy_analysis_cached(data_csv, records_csv, review_csv, stake, target_return, max_combos, max_daily_buys, base_stake, operation_mode):
    """
    서버에서 무거운 분석을 먼저 계산하고,
    휴대폰은 계산된 결과만 빠르게 받아보는 캐시 레이어.
    """
    from io import StringIO
    data = pd.read_csv(StringIO(data_csv)) if data_csv else pd.DataFrame()
    records = pd.read_csv(StringIO(records_csv)) if records_csv else pd.DataFrame()
    review_records = pd.read_csv(StringIO(review_csv)) if review_csv else pd.DataFrame()

    h = horse_engine(data, records)
    if "apply_confidence_and_warnings" in globals():
        h = apply_confidence_and_warnings(h)
    if "add_review_plus_scores" in globals():
        h = add_review_plus_scores(h, data, review_records)
        if "apply_confidence_and_warnings" in globals():
            h = apply_confidence_and_warnings(h)

    c = combo_engine(h, stake, target_return, max_combos)
    if "combo_over_limit_guard" in globals():
        op = combo_over_limit_guard(c, max_daily_buys, base_stake, operation_mode)
    else:
        op = c.copy()

    target_odds = round(target_return / stake, 1) if stake else 30
    if "today_summary_card" in globals():
        summary = today_summary_card(h, c, target_odds, max_daily_buys)
    else:
        summary = {"오늘 경주 수":0, "30배 후보":len(c), "A등급 후보":0, "빨간경고 경주":0, "추천 구매 수":0, "하루 제한":max_daily_buys, "오늘 판단":"분석"}

    if "race_one_line_conclusions" in globals():
        one_line = race_one_line_conclusions(h, c, target_odds)
    else:
        one_line = pd.DataFrame()

    if "purchase_vs_observe_stats" in globals():
        pvo = purchase_vs_observe_stats()
    else:
        pvo = pd.DataFrame()

    return h, c, op, summary, one_line, pvo

def df_to_csv_safe(df):
    try:
        return df.to_csv(index=False)
    except Exception:
        return ""

def mobile_card(title, body, kind="source-card"):
    st.markdown(f"""
    <div class="{kind}">
      <div class="big">{title}</div>
      <div style="font-size:18px;line-height:1.8;">{body}</div>
    </div>
    """, unsafe_allow_html=True)




def parse_horse_numbers_from_combo_text(text):
    nums = []
    for x in re.findall(r"(\d+)번", str(text)):
        try:
            nums.append(int(x))
        except Exception:
            pass
    # fallback for combos like 5-6-8
    if not nums:
        for x in re.findall(r"\b\d+\b", str(text)):
            try:
                n = int(x)
                if 1 <= n <= 20:
                    nums.append(n)
            except Exception:
                pass
    # preserve order, unique
    out = []
    for n in nums:
        if n not in out:
            out.append(n)
    return out[:3]

def normalize_result_df(df):
    if df is None or len(df) == 0:
        return pd.DataFrame(columns=["날짜","경마장","경주","경주번호","1착","2착","3착","최종배당_삼복승","최종배당_삼쌍승","기록","주로상태"])
    d = df.copy()
    # Common aliases
    aliases = {
        "일자":"날짜", "경주일":"날짜",
        "경마장명":"경마장",
        "R":"경주", "경주명":"경주",
        "race_no":"경주번호", "경주번호":"경주번호",
        "일착":"1착", "1위":"1착", "1등":"1착",
        "이착":"2착", "2위":"2착", "2등":"2착",
        "삼착":"3착", "3위":"3착", "3등":"3착",
        "삼복승배당":"최종배당_삼복승",
        "삼쌍승배당":"최종배당_삼쌍승",
        "최종배당":"최종배당_삼복승"
    }
    for old, new in aliases.items():
        if old in d.columns and new not in d.columns:
            d[new] = d[old]
    for c in ["날짜","경마장","경주","경주번호","1착","2착","3착","최종배당_삼복승","최종배당_삼쌍승","기록","주로상태"]:
        if c not in d.columns:
            d[c] = ""
    for c in ["경주번호","1착","2착","3착","최종배당_삼복승","최종배당_삼쌍승"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["경주"] = d.apply(lambda r: r["경주"] if str(r["경주"]).strip() else (f"{int(r['경주번호'])}R" if pd.notna(r["경주번호"]) else ""), axis=1)
    return d[["날짜","경마장","경주","경주번호","1착","2착","3착","최종배당_삼복승","최종배당_삼쌍승","기록","주로상태"]]

@st.cache_data(ttl=60, show_spinner=False)
def fetch_result_sheet(url):
    try:
        if not url:
            return False, pd.DataFrame(), "결과표 주소 없음"
        csv_url = normalize_sheet_url(url) if "normalize_sheet_url" in globals() else url
        df = pd.read_csv(csv_url)
        return True, normalize_result_df(df), ""
    except Exception as e:
        return False, pd.DataFrame(), str(e)

def load_result_sheet_if_any():
    if not result_sheet_url:
        return False, "결과표 주소 없음"
    ok, df, err = fetch_result_sheet(result_sheet_url)
    if ok and len(df):
        st.session_state.race_results = df
        return True, f"결과표 {len(df)}행 자동 읽기 성공"
    return False, f"결과표 읽기 실패: {err}"

def judge_combo_against_result(combo_row, result_row):
    try:
        first = int(result_row.get("1착"))
        second = int(result_row.get("2착"))
        third = int(result_row.get("3착"))
    except Exception:
        return "결과부족", 0, "결과표 1/2/3착 부족"

    actual_order = [first, second, third]
    actual_set = set(actual_order)

    way = str(combo_row.get("방식", ""))
    combo_text = " ".join([str(combo_row.get(k, "")) for k in ["1착","2착","3착","조합","메모"]])
    nums = parse_horse_numbers_from_combo_text(combo_text)
    if len(nums) < 3:
        return "조합부족", 0, "조합 마번 3개 인식 실패"

    if "삼쌍" in way:
        hit = nums[:3] == actual_order
        final_odds = pd.to_numeric(result_row.get("최종배당_삼쌍승", 0), errors="coerce")
        memo = f"예상순서 {nums[:3]} / 실제순서 {actual_order}"
    else:
        hit = set(nums[:3]) == actual_set
        final_odds = pd.to_numeric(result_row.get("최종배당_삼복승", 0), errors="coerce")
        memo = f"예상조합 {sorted(nums[:3])} / 실제조합 {sorted(actual_order)}"

    if pd.isna(final_odds) or final_odds == 0:
        final_odds = pd.to_numeric(combo_row.get("예상배당", 0), errors="coerce")
    if pd.isna(final_odds):
        final_odds = 0

    return ("적중" if hit else "실패"), float(final_odds), memo

def find_result_for_combo(combo_row, results_df):
    if results_df is None or len(results_df) == 0:
        return None
    course = str(combo_row.get("경마장", ""))
    try:
        race_no = int(combo_row.get("경주번호", 0))
    except Exception:
        race_no = 0
    r = results_df.copy()
    mask = pd.Series([True] * len(r))
    if "경마장" in r.columns and course:
        mask = mask & r["경마장"].astype(str).str.contains(course[:2], na=False)
    if "경주번호" in r.columns and race_no:
        mask = mask & (pd.to_numeric(r["경주번호"], errors="coerce") == race_no)
    hit = r[mask]
    if len(hit):
        return hit.iloc[0]
    return None

def auto_compare_combos_with_results(combos_df, results_df, purchase_records=None, observation_records=None):
    logs = []
    if combos_df is not None and len(combos_df) and results_df is not None and len(results_df):
        for _, row in combos_df.iterrows():
            res = find_result_for_combo(row, results_df)
            if res is None:
                continue
            판정, final_odds, memo = judge_combo_against_result(row, res)
            stake_val = pd.to_numeric(row.get("자동투자금", row.get("투자금", 10000)), errors="coerce")
            if pd.isna(stake_val) or stake_val <= 0:
                stake_val = 10000
            actual_return = int(stake_val * final_odds) if 판정 == "적중" else 0
            logs.append({
                "날짜": pd.Timestamp.today().strftime("%Y-%m-%d"),
                "경마장": row.get("경마장",""),
                "경주": f"{int(row.get('경주번호',0))}R" if pd.notna(row.get("경주번호", None)) else "",
                "방식": row.get("방식",""),
                "조합": " / ".join([str(row.get("1착","")), str(row.get("2착","")), str(row.get("3착",""))]),
                "예상배당": row.get("예상배당",0),
                "최종배당": final_odds,
                "판정": 판정,
                "구매여부": row.get("구매여부","미구매 관찰"),
                "예상환급": row.get("예상환급",0),
                "실제환급": actual_return,
                "메모": memo
            })
    out = pd.DataFrame(logs)
    if len(out):
        prev = st.session_state.result_compare_log.copy() if "result_compare_log" in st.session_state else pd.DataFrame()
        st.session_state.result_compare_log = pd.concat([prev, out], ignore_index=True).drop_duplicates(
            subset=["날짜","경마장","경주","방식","조합"], keep="last"
        )
    return out

def update_observations_from_results(results_df):
    if "observation_records" not in st.session_state or len(st.session_state.observation_records) == 0:
        return 0
    obs = st.session_state.observation_records.copy()
    updated = 0
    for idx, row in obs.iterrows():
        if str(row.get("관찰결과","")) not in ["결과대기", "대기", "", "nan"]:
            continue
        # Make pseudo combo row from observation
        combo_row = {
            "경마장": row.get("경마장",""),
            "경주번호": int(str(row.get("경주","0")).replace("R","")) if str(row.get("경주","0")).replace("R","").isdigit() else 0,
            "방식": row.get("방식",""),
            "조합": row.get("조합",""),
            "예상배당": row.get("예상배당",0),
            "투자금": 10000
        }
        res = find_result_for_combo(combo_row, results_df)
        if res is None:
            continue
        판정, final_odds, memo = judge_combo_against_result(combo_row, res)
        obs.loc[idx, "관찰결과"] = 판정
        obs.loc[idx, "실제결과"] = memo
        obs.loc[idx, "메모"] = str(obs.loc[idx, "메모"]) + f" | 최종배당 {final_odds}"
        updated += 1
    st.session_state.observation_records = obs
    return updated


def super_alert_candidates(combos_df, min_odds=30, min_score=78, max_risk=3, max_count=3):
    if combos_df is None or len(combos_df) == 0:
        return pd.DataFrame()
    c = combos_df.copy()
    c["예상배당_num"] = pd.to_numeric(c.get("예상배당", 0), errors="coerce").fillna(0)
    c["조합점수_num"] = pd.to_numeric(c.get("조합점수", 0), errors="coerce").fillna(0)
    c["위험합계_num"] = pd.to_numeric(c.get("위험합계", 0), errors="coerce").fillna(0)
    if "운영판정" not in c.columns:
        c["운영판정"] = c.get("판정", "")
    mask = (
        (c["예상배당_num"] >= min_odds) &
        (c["조합점수_num"] >= min_score) &
        (c["위험합계_num"] <= max_risk) &
        (~c.astype(str).agg(" ".join, axis=1).str.contains("보류|배당 죽음", na=False))
    )
    out = c[mask].copy()
    if len(out) == 0:
        return out
    out["놓치면아까운점수"] = (
        out["조합점수_num"] * 0.62 +
        out["예상배당_num"].clip(0, 120) * 0.28 -
        out["위험합계_num"] * 4
    ).round(1)
    return out.sort_values("놓치면아까운점수", ascending=False).head(max_count)


def watch_mode_js(check_sec=30, keep_awake=True, auto_stop_min=0):
    """
    감시모드:
    - 앱이 열린 상태에서 자동 새로고침
    - Wake Lock API로 화면 꺼짐 방지 시도
    - 알림 권한 요청
    - 사용자가 수동으로 OFF 가능
    """
    keep_awake_js = """
    let wakeLock = null;
    async function requestWakeLock() {
      try {
        if ('wakeLock' in navigator) {
          wakeLock = await navigator.wakeLock.request('screen');
          console.log('MARU wake lock on');
        }
      } catch (err) { console.log('wake lock failed', err); }
    }
    requestWakeLock();
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') requestWakeLock();
    });
    """ if keep_awake else ""

    notification_js = """
    try {
      if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
      }
    } catch(e) {}
    """

    auto_stop_js = ""
    if auto_stop_min and auto_stop_min > 0:
        auto_stop_js = f"""
        setTimeout(function(){{
          localStorage.setItem('maru_watch_auto_stop','1');
        }}, {int(auto_stop_min)*60*1000});
        """

    components.html(f"""
    <script>
    {keep_awake_js}
    {notification_js}
    {auto_stop_js}
    setTimeout(function() {{
      window.location.reload();
    }}, {int(check_sec) * 1000});
    </script>
    """, height=0)

def browser_notification(title, body):
    safe_title = str(title).replace("'", "").replace('"', "")
    safe_body = str(body).replace("'", "").replace('"', "")
    components.html(f"""
    <script>
    try {{
      if ('Notification' in window && Notification.permission === 'granted') {{
        new Notification('{safe_title}', {{ body: '{safe_body}' }});
      }}
    }} catch(e) {{}}
    </script>
    """, height=0)


def parse_hhmm_to_minutes(x):
    try:
        h, m = str(x).strip().split(":")[:2]
        return int(h) * 60 + int(m)
    except Exception:
        return None

def minutes_to_hhmm(m):
    if m is None:
        return ""
    m = int(m) % (24*60)
    return f"{m//60:02d}:{m%60:02d}"

def default_watch_window(day_type):
    if day_type == "야간 금요일":
        return "13:30", "21:10"
    if day_type == "야간 토요일":
        return "12:00", "20:10"
    if day_type == "수동 설정":
        return manual_watch_start, manual_watch_end
    return "10:30", "18:10"

def is_now_in_watch_window():
    if not race_schedule_watch:
        return True, "시간대 감시 OFF"
    start, end = default_watch_window(race_day_type)
    now = pd.Timestamp.now()
    now_min = now.hour * 60 + now.minute
    s = parse_hhmm_to_minutes(start)
    e = parse_hhmm_to_minutes(end)
    if s is None or e is None:
        return True, "시간 설정 오류 - 감시 허용"
    active = s <= now_min <= e if s <= e else (now_min >= s or now_min <= e)
    return active, f"{start}~{end}"

def race_time_minutes_from_row(row):
    t = str(row.get("출발시간", "")).strip()
    # HH:MM direct
    m = parse_hhmm_to_minutes(t)
    if m is not None:
        return m
    # fallback: 10시45분 style
    import re
    mt = re.search(r"(\d{1,2})\D+(\d{1,2})", t)
    if mt:
        return int(mt.group(1))*60 + int(mt.group(2))
    return None

def high_odds_time_phase(row):
    rt = race_time_minutes_from_row(row)
    if rt is None:
        return "출발시간 없음", 999
    now = pd.Timestamp.now()
    now_min = now.hour * 60 + now.minute
    diff = rt - now_min
    if diff < -5:
        return "경주 종료/지남", diff
    if diff <= final_watch_min:
        return "🚨 최종확인", diff
    if diff <= 5:
        return "🚨 특급감시", diff
    if diff <= 10:
        return "🔥 강력감시", diff
    if diff <= high_odds_watch_min:
        return "📈 30배 집중감시", diff
    if diff <= 30:
        return "👀 사전관찰", diff
    return "대기", diff

def add_time_phase_to_combos(combos_df):
    if combos_df is None or len(combos_df) == 0:
        return combos_df
    c = combos_df.copy()
    phases = c.apply(high_odds_time_phase, axis=1)
    c["시간대상태"] = [p[0] for p in phases]
    c["출발까지분"] = [p[1] for p in phases]
    return c




def count_df_rows(state_name):
    try:
        df = st.session_state.get(state_name, pd.DataFrame())
        return len(df) if isinstance(df, pd.DataFrame) else 0
    except Exception:
        return 0

def status_card(label, value, level="ok"):
    cls = "status-ok" if level == "ok" else ("status-warn" if level == "warn" else "status-bad")
    return f"""
    <div class="{cls}">
      <div class="status-title">{label}</div>
      <div class="status-value">{value}</div>
    </div>
    """

def connection_status_text():
    source = st.session_state.get("source_status", "상태 없음")
    rows = 0
    try:
        rows = len(data) if "data" in globals() else 0
    except Exception:
        rows = 0
    return source, rows

def render_status_dashboard():
    if not stable_status_enabled:
        return
    source, data_rows = connection_status_text()
    kra_level = "ok" if "성공" in str(source) or data_rows > 0 else "warn"
    result_rows = count_df_rows("race_results")
    compare_rows = count_df_rows("result_compare_log")
    rec_rows = count_df_rows("auto_recommend_text_log")
    obs_rows = count_df_rows("observation_records")
    buy_rows = count_df_rows("purchase_records")
    html = '<div class="status-grid">'
    html += status_card("데이터 행 수", data_rows, "ok" if data_rows else "warn")
    html += status_card("원본 연결", "OK" if kra_level=="ok" else "확인", kra_level)
    html += status_card("결과표", result_rows, "ok" if result_rows else "warn")
    html += status_card("추천저장", rec_rows, "ok" if rec_rows else "warn")
    html += status_card("결과비교", compare_rows, "ok" if compare_rows else "warn")
    html += status_card("미구매관찰", obs_rows, "ok" if obs_rows else "warn")
    html += status_card("구매기록", buy_rows, "ok" if buy_rows else "warn")
    html += status_card("감시모드", "ON" if st.session_state.get("watch_mode_on", False) else "OFF", "ok" if st.session_state.get("watch_mode_on", False) else "warn")
    html += status_card("텔레그램", "준비" if external_alert_ready and telegram_chat_id and telegram_bot_token else "OFF", "ok" if external_alert_ready and telegram_chat_id and telegram_bot_token else "warn")
    html += status_card("백업", "가능", "ok")
    html += "</div>"
    with st.expander("🛠 상태 점검판", expanded=True):
        st.markdown(html, unsafe_allow_html=True)
        st.caption(f"원본 상태: {source}")
        if data_rows == 0:
            st.warning("현재 분석 데이터가 비어 있습니다. KRA/Google Sheet/CSV 연결을 확인하세요.")
        if result_rows == 0:
            st.info("결과표가 없으면 추천은 가능하지만, 놓친 조합 학습은 제한됩니다.")
        if rec_rows == 0:
            st.info("추천기록이 아직 없습니다. 오늘 경주 데이터를 읽은 뒤 자동 저장됩니다.")

def ultra_home_best_text():
    base = operation_combos if "operation_combos" in globals() and len(operation_combos) else (combos if "combos" in globals() else pd.DataFrame())
    row, reason = best_final_candidate(base) if "best_final_candidate" in globals() else (None, "판정불가")
    if row is None:
        return f"""
        <div class="ultra-home">
          <div class="ultra-home-title">🟡 지금은 관망</div>
          <div class="ultra-home-body">
            이유: <b>{reason}</b><br>
            특급 조합이 없으면 무리하지 말고 관찰 기록만 쌓는 쪽이 좋습니다.<br>
            감시모드: <b>{"ON" if st.session_state.get("watch_mode_on", False) else "OFF"}</b>
          </div>
        </div>
        """
    return f"""
    <div class="ultra-home">
      <div class="ultra-home-title">📱 현장용 초간단 홈</div>
      <div class="ultra-home-body">
        오늘 판단: <b>{reason}</b><br>
        경주: <b>{row.get('경마장','')} {row.get('경주번호','')}R {row.get('출발시간','')}</b><br>
        조합: <b>{row.get('방식','')} / {row.get('1착','')} - {row.get('2착','')} - {row.get('3착','')}</b><br>
        예상배당: <b>{row.get('예상배당','')}배</b> /
        점수: <b>{row.get('조합점수','')}</b> /
        위험: <b>{row.get('위험합계','')}</b><br>
        시간대: <b>{row.get('시간대상태','')}</b> /
        출발까지: <b>{row.get('출발까지분','')}분</b><br>
        감시모드: <b>{"ON" if st.session_state.get("watch_mode_on", False) else "OFF"}</b><br>
        ※ 공식 페이지 최종 확인 후 수동구매
      </div>
    </div>
    """

def render_ultra_mobile_home():
    if not ultra_mobile_home_enabled:
        return
    st.markdown(ultra_home_best_text(), unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("📱 감시 ON", key="ultra_watch_on", use_container_width=True):
            st.session_state.watch_mode_on = True
            st.rerun()
    with c2:
        if st.button("🛑 감시 OFF", key="ultra_watch_off", use_container_width=True):
            st.session_state.watch_mode_on = False
            st.rerun()
    with c3:
        if st.button("🔄 새로고침", key="ultra_refresh", use_container_width=True):
            st.rerun()

def enhanced_result_url_candidates():
    urls = []
    base_urls = [
        "https://race.kra.co.kr/raceScore/scoretableScoreList.do",
        "https://race.kra.co.kr/raceScore/scoretableScoreList.do?Act=01",
        "https://race.kra.co.kr/todayrace/todayrace.do",
    ]
    for u in base_urls:
        urls.append(u)
    return urls

@st.cache_data(ttl=120, show_spinner=False)
def fetch_kra_results_enhanced():
    if not kra_result_auto_enhanced:
        return False, pd.DataFrame(), "KRA 결과표 자동수집 강화 OFF"
    errors = []
    for url in enhanced_result_url_candidates():
        try:
            tables = pd.read_html(url)
            good_tables = []
            for t in tables:
                cols = " ".join(map(str, t.columns)) + " " + " ".join(map(str, t.head(3).values.flatten()))
                if any(k in cols for k in ["순위", "착순", "삼복", "삼쌍", "배당", "경주"]):
                    good_tables.append(t)
            if good_tables:
                raw = pd.concat(good_tables, ignore_index=True)
                return True, raw, url
        except Exception as e:
            errors.append(f"{url}: {str(e)[:80]}")
    return False, pd.DataFrame(), " / ".join(errors[-2:]) if errors else "읽기 실패"

def render_kra_result_enhanced_panel():
    if not kra_result_auto_enhanced:
        return
    with st.expander("🏁 KRA 결과표 자동수집 강화", expanded=False):
        ok, raw, msg = fetch_kra_results_enhanced()
        if ok:
            st.success(f"KRA 결과표 후보 읽기 성공: {msg}")
            st.dataframe(raw.head(100), use_container_width=True)
            st.caption("표 구조가 일정하지 않을 수 있어, 최종 반영 전에는 결과문구 자동해석/수동 확인을 함께 사용하세요.")
        else:
            st.warning(f"KRA 결과표 자동수집 실패 또는 표 없음: {msg}")
            st.info("이 경우 결과문구 한 줄 붙여넣기 방식이 가장 안정적인 백업입니다.")


def send_telegram_message_safe(token="", chat_id="", text=""):
    try:
        if not token or not chat_id or not text:
            return False
        import requests
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": text}, timeout=5)
        return True
    except Exception:
        return False

def send_telegram_alert(text):
    if not external_alert_ready or not telegram_bot_token or not telegram_chat_id:
        return False, "텔레그램 설정 없음"
    try:
        import requests
        url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
        r = requests.post(url, data={"chat_id": telegram_chat_id, "text": text}, timeout=8)
        return r.status_code == 200, r.text[:120]
    except Exception as e:
        return False, str(e)

def render_external_alert_panel():
    with st.expander("🔔 텔레그램/외부알림 준비", expanded=False):
        st.markdown("""
휴대폰이 완전히 꺼져 있거나 앱이 닫힌 상태에서 웹앱이 스스로 켜지는 것은 어렵습니다.  
진짜 백그라운드 알림은 텔레그램/문자 API 같은 외부 알림이 필요합니다.
""")
        if external_alert_ready and telegram_bot_token and telegram_chat_id:
            if st.button("텔레그램 테스트 알림 보내기", use_container_width=True):
                ok, msg = send_telegram_alert("MARU KRA 테스트 알림입니다.")
                st.success("전송 성공") if ok else st.error(f"전송 실패: {msg}")
        else:
            st.info("왼쪽에 Bot Token과 Chat ID를 넣고 외부알림 준비를 켜면 테스트할 수 있습니다.")

def render_google_save_ready_panel():
    with st.expander("☁️ Google Sheet 자동저장 준비", expanded=False):
        st.markdown("""
현재는 백업 ZIP/CSV 방식이 가장 안전합니다.  
Google Sheet에 앱이 직접 저장하려면 Google Cloud 서비스계정 키가 필요합니다.

준비물:
1. Google Cloud 서비스 계정 JSON  
2. 해당 구글시트를 서비스계정 이메일과 공유  
3. Streamlit Secrets에 JSON 저장  
4. gspread 연동

토큰 없이 자동쓰기까지 켜면 오류가 날 수 있어, 지금은 준비 화면으로 안전하게 두었습니다.
""")
        st.info("원하면 다음 버전에서 Google 서비스계정 방식까지 붙일 수 있습니다.")



def safe_df(name, columns=None):
    if name in st.session_state and isinstance(st.session_state[name], pd.DataFrame):
        return st.session_state[name]
    return pd.DataFrame(columns=columns or [])

def best_final_candidate(combos_df):
    if combos_df is None or len(combos_df) == 0:
        return None, "후보 없음"
    c = combos_df.copy()
    c["예상배당_num"] = pd.to_numeric(c.get("예상배당", 0), errors="coerce").fillna(0)
    c["조합점수_num"] = pd.to_numeric(c.get("조합점수", 0), errors="coerce").fillna(0)
    c["위험합계_num"] = pd.to_numeric(c.get("위험합계", 0), errors="coerce").fillna(99)
    if "신뢰등급" not in c.columns:
        c["신뢰등급"] = ""
    text_all = c.astype(str).agg(" ".join, axis=1)
    c = c[~text_all.str.contains("보류|배당 죽음|과열|위험", na=False)]
    if len(c) == 0:
        return None, "보류/위험 후보 제외 후 남은 후보 없음"
    # 하루 1~2회 구매 제한 기준
    bought_today = 0
    if "daily_purchase_count" in st.session_state:
        try:
            bought_today = int(st.session_state.daily_purchase_count)
        except Exception:
            bought_today = 0
    max_buys = int(max_daily_buys) if "max_daily_buys" in globals() else 2
    if bought_today >= max_buys:
        return None, f"오늘 구매 제한 {max_buys}회 도달"
    # practical score: high enough score, but not too risky
    c["최종판정점수"] = (
        c["조합점수_num"] * 0.72 +
        c["예상배당_num"].clip(0, 100) * 0.18 -
        c["위험합계_num"] * 4
    ).round(1)
    c = c.sort_values("최종판정점수", ascending=False)
    best = c.iloc[0]
    if best["조합점수_num"] >= 82 and best["위험합계_num"] <= 2:
        reason = "소액 구매 가능"
    elif best["조합점수_num"] >= 76 and best["위험합계_num"] <= 3 and best["예상배당_num"] >= 25:
        reason = "관찰 후 소액 가능"
    else:
        reason = "관망 우선"
    return best, reason

def render_final_decision_card(combos_df):
    if not final_decision_enabled:
        return
    row, reason = best_final_candidate(combos_df)
    if row is None:
        st.markdown(f"""
        <div class="final-hold-card">
          <div class="final-title">🟡 오늘은 관망 우선</div>
          <div class="final-body">
            이유: <b>{reason}</b><br>
            무리하게 사는 날이 아니라, 미구매 관찰로 데이터만 쌓는 쪽이 좋습니다.
          </div>
        </div>
        """, unsafe_allow_html=True)
        return
    odds = pd.to_numeric(row.get("예상배당", 0), errors="coerce")
    risk = pd.to_numeric(row.get("위험합계", 99), errors="coerce")
    score = pd.to_numeric(row.get("조합점수", 0), errors="coerce")
    card_class = "final-buy-card" if "구매" in reason else "final-hold-card"
    title = "🟢 오늘 최종 후보" if "구매" in reason else "🟡 오늘 관심 후보"
    st.markdown(f"""
    <div class="{card_class}">
      <div class="final-title">{title}</div>
      <div class="final-body">
        판정: <b>{reason}</b><br>
        경마장/경주: <b>{row.get('경마장','')} {row.get('경주번호','')}R {row.get('출발시간','')}</b><br>
        방식: <b>{row.get('방식','')}</b><br>
        조합: <b>{row.get('1착','')} / {row.get('2착','')} / {row.get('3착','')}</b><br>
        예상배당: <b>{row.get('예상배당','')}배</b> /
        점수: <b>{row.get('조합점수','')}</b> /
        위험합계: <b>{row.get('위험합계','')}</b> /
        신뢰등급: <b>{row.get('신뢰등급','')}</b><br>
        ※ 공식 페이지에서 최종배당·출주상태 확인 후 수동으로만 구매
      </div>
    </div>
    """, unsafe_allow_html=True)

def make_backup_bundle_csv():
    import io, zipfile as zf
    buf = io.BytesIO()
    frames = {
        "race_results.csv": safe_df("race_results"),
        "result_compare_log.csv": safe_df("result_compare_log"),
        "auto_recommend_text_log.csv": safe_df("auto_recommend_text_log"),
        "parsed_result_text_log.csv": safe_df("parsed_result_text_log"),
        "observation_records.csv": safe_df("observation_records"),
        "purchase_records.csv": safe_df("purchase_records"),
        "review_records.csv": safe_df("review_records"),
    }
    with zf.ZipFile(buf, "w", zf.ZIP_DEFLATED) as zz:
        for filename, df in frames.items():
            zz.writestr(filename, df.to_csv(index=False, encoding="utf-8-sig"))
    return buf.getvalue()

def restore_backup_zip(uploaded):
    import zipfile as zf, io
    if uploaded is None:
        return []
    mapping = {
        "race_results.csv": "race_results",
        "result_compare_log.csv": "result_compare_log",
        "auto_recommend_text_log.csv": "auto_recommend_text_log",
        "parsed_result_text_log.csv": "parsed_result_text_log",
        "observation_records.csv": "observation_records",
        "purchase_records.csv": "purchase_records",
        "review_records.csv": "review_records",
    }
    restored = []
    data = uploaded.read()
    with zf.ZipFile(io.BytesIO(data), "r") as zz:
        for filename, state_name in mapping.items():
            if filename in zz.namelist():
                with zz.open(filename) as f:
                    try:
                        st.session_state[state_name] = pd.read_csv(f)
                        restored.append(state_name)
                    except Exception:
                        pass
    return restored

def render_backup_panel():
    if not backup_panel_enabled:
        return
    with st.expander("💾 기록 백업 / 불러오기", expanded=False):
        st.markdown("""
앱 서버가 재시작되면 내부 기록이 사라질 수 있습니다.  
하루 끝나고 백업 ZIP을 받아두면 다음에 다시 불러와서 이어서 볼 수 있습니다.
""")
        backup_bytes = make_backup_bundle_csv()
        st.download_button(
            "💾 오늘 기록 전체 백업 ZIP 다운로드",
            data=backup_bytes,
            file_name=f"MARU_KRA_BACKUP_{pd.Timestamp.today().strftime('%Y%m%d')}.zip",
            mime="application/zip",
            width="stretch"
        )
        up = st.file_uploader("이전 백업 ZIP 불러오기", type=["zip"], key="restore_backup_zip")
        if st.button("백업 불러오기 적용", use_container_width=True):
            if up:
                restored = restore_backup_zip(up)
                st.success(f"복원 완료: {', '.join(restored) if restored else '복원된 항목 없음'}")
                st.rerun()
            else:
                st.warning("먼저 백업 ZIP 파일을 올려주세요.")

def daily_close_report():
    today = pd.Timestamp.today().strftime("%Y-%m-%d")
    rec = safe_df("auto_recommend_text_log")
    obs = safe_df("observation_records")
    buy = safe_df("purchase_records")
    comp = safe_df("result_compare_log")
    result = safe_df("race_results")

    def today_filter(df):
        if df is None or len(df) == 0 or "날짜" not in df.columns:
            return df.iloc[0:0] if df is not None else pd.DataFrame()
        return df[df["날짜"].astype(str).str[:10] == today]

    rec_t = today_filter(rec)
    obs_t = today_filter(obs)
    buy_t = today_filter(buy)
    comp_t = today_filter(comp)
    result_t = today_filter(result)

    hit_buy = int((buy_t.get("결과", pd.Series(dtype=str)).astype(str) == "적중").sum()) if len(buy_t) else 0
    obs_hit = int((obs_t.get("관찰결과", pd.Series(dtype=str)).astype(str) == "적중").sum()) if len(obs_t) else 0
    comp_hit = int((comp_t.get("판정", pd.Series(dtype=str)).astype(str) == "적중").sum()) if len(comp_t) else 0
    comp_fail = int((comp_t.get("판정", pd.Series(dtype=str)).astype(str) == "실패").sum()) if len(comp_t) else 0

    missed_notes = []
    if len(obs_t) and "관찰결과" in obs_t.columns:
        missed = obs_t[obs_t["관찰결과"].astype(str) == "적중"]
        for _, r in missed.head(5).iterrows():
            missed_notes.append(f"{r.get('경마장','')} {r.get('경주','') or str(r.get('경주번호',''))+'R'} {r.get('조합','')}")
    missed_text = "<br>".join(missed_notes) if missed_notes else "아직 없음"

    report = f"""
    <div class="report-box">
      <b>📘 하루 마감 리포트</b><br>
      오늘 추천 저장: <b>{len(rec_t)}건</b><br>
      결과표 입력/해석: <b>{len(result_t)}경주</b><br>
      실제 구매: <b>{len(buy_t)}건</b> / 구매 적중: <b>{hit_buy}건</b><br>
      미구매 관찰: <b>{len(obs_t)}건</b> / 샀으면 맞았던 조합: <b>{obs_hit}건</b><br>
      결과비교 적중/실패: <b>{comp_hit} / {comp_fail}</b><br><br>
      <b>놓치면 아까웠던 후보</b><br>
      {missed_text}<br><br>
      <b>내일 보정 포인트</b><br>
      - 특급알림 후보는 결과표까지 꼭 비교<br>
      - 미구매 적중 조합이 반복되면 해당 유형 가산<br>
      - 위험합계 4 이상 조합은 계속 관찰 위주
    </div>
    """
    return report

def render_daily_close_report():
    if not daily_report_enabled:
        return
    with st.expander("📘 하루 마감 리포트", expanded=True):
        st.markdown(daily_close_report(), unsafe_allow_html=True)
        st.download_button(
            "📘 마감 리포트 HTML 다운로드",
            data=daily_close_report().encode("utf-8"),
            file_name=f"MARU_KRA_DAILY_REPORT_{pd.Timestamp.today().strftime('%Y%m%d')}.html",
            mime="text/html",
            width="stretch"
        )



def combo_to_recommend_sentence(row):
    return (
        f"[MARU추천] {row.get('경마장','')} {row.get('경주번호','')}R "
        f"{row.get('출발시간','')} / {row.get('방식','')} / "
        f"{row.get('1착','')} - {row.get('2착','')} - {row.get('3착','')} / "
        f"예상 {row.get('예상배당','')}배 / 점수 {row.get('조합점수','')} / "
        f"위험 {row.get('위험합계','')} / 등급 {row.get('신뢰등급','')}"
    )

def auto_save_recommendations(combos_df, max_rows=20):
    if not auto_save_recommend_text:
        return 0
    if combos_df is None or len(combos_df) == 0:
        return 0
    c = combos_df.copy().head(max_rows)
    rows = []
    for _, row in c.iterrows():
        combo = " / ".join([str(row.get("1착","")), str(row.get("2착","")), str(row.get("3착",""))])
        rows.append({
            "날짜": pd.Timestamp.today().strftime("%Y-%m-%d"),
            "경마장": row.get("경마장",""),
            "경주번호": row.get("경주번호",""),
            "출발시간": row.get("출발시간",""),
            "추천문구": combo_to_recommend_sentence(row),
            "방식": row.get("방식",""),
            "조합": combo,
            "예상배당": row.get("예상배당",0),
            "조합점수": row.get("조합점수",0),
            "위험합계": row.get("위험합계",0),
            "신뢰등급": row.get("신뢰등급",""),
            "상태": "자동저장"
        })
    new = pd.DataFrame(rows)
    prev = st.session_state.auto_recommend_text_log.copy()
    out = pd.concat([prev, new], ignore_index=True).drop_duplicates(
        subset=["날짜","경마장","경주번호","방식","조합"], keep="last"
    )
    st.session_state.auto_recommend_text_log = out
    return len(new)

def parse_result_text_block(text, default_course="서울"):
    """
    KRA/문자/메모 형태를 대략 자동해석.
    예:
    1경주 5 2 8 삼복승 38.5 삼쌍승 210.4
    서울 2R 3번 6번 10번 삼복 31.2 삼쌍 145.0
    """
    rows = []
    if not text or not str(text).strip():
        return pd.DataFrame(columns=["날짜","경마장","경주번호","1착","2착","3착","최종배당_삼복승","최종배당_삼쌍승","원문"])
    lines = [x.strip() for x in str(text).splitlines() if x.strip()]
    for line in lines:
        course = default_course
        if "부산" in line or "부경" in line:
            course = "부산경남"
        elif "제주" in line:
            course = "제주"
        elif "서울" in line:
            course = "서울"

        race_no = None
        m = re.search(r"(\d{1,2})\s*(?:경주|R|r)", line)
        if m:
            race_no = int(m.group(1))

        # Find horse numbers.
        # Prefer numbers followed by 번. If not enough, use remaining small numbers after race number.
        nums = [int(x) for x in re.findall(r"(\d{1,2})\s*번", line)]
        if len(nums) < 3:
            allnums = [int(x) for x in re.findall(r"\b(\d{1,2})\b", line)]
            # remove race_no once
            temp = []
            removed = False
            for n in allnums:
                if race_no is not None and n == race_no and not removed:
                    removed = True
                    continue
                if 1 <= n <= 20:
                    temp.append(n)
            nums = temp[:3]

        if race_no is None or len(nums) < 3:
            continue

        삼복 = None
        삼쌍 = None
        m1 = re.search(r"(?:삼복승|삼복)\D*(\d+(?:\.\d+)?)", line)
        m2 = re.search(r"(?:삼쌍승|삼쌍)\D*(\d+(?:\.\d+)?)", line)
        if m1:
            삼복 = float(m1.group(1))
        if m2:
            삼쌍 = float(m2.group(1))

        # Fallback: after first 4 integers, larger decimal odds
        if 삼복 is None or 삼쌍 is None:
            decimals = [float(x) for x in re.findall(r"\b(\d{1,4}(?:\.\d+)?)\b", line)]
            odds_candidates = [x for x in decimals if x > 10 and x not in nums and x != race_no]
            if 삼복 is None and odds_candidates:
                삼복 = odds_candidates[0]
            if 삼쌍 is None and len(odds_candidates) > 1:
                삼쌍 = odds_candidates[1]

        rows.append({
            "날짜": pd.Timestamp.today().strftime("%Y-%m-%d"),
            "경마장": course,
            "경주번호": race_no,
            "1착": nums[0],
            "2착": nums[1],
            "3착": nums[2],
            "최종배당_삼복승": 삼복 if 삼복 is not None else "",
            "최종배당_삼쌍승": 삼쌍 if 삼쌍 is not None else "",
            "원문": line
        })
    return pd.DataFrame(rows)

def apply_parsed_results_to_system(parsed_df):
    if parsed_df is None or len(parsed_df) == 0:
        return 0, 0
    result_df = normalize_result_df(parsed_df.rename(columns={"원문":"메모"})) if "normalize_result_df" in globals() else parsed_df
    prev = st.session_state.race_results.copy() if "race_results" in st.session_state else pd.DataFrame()
    st.session_state.race_results = pd.concat([prev, result_df], ignore_index=True).drop_duplicates(
        subset=["날짜","경마장","경주번호"], keep="last"
    )
    prev_text = st.session_state.parsed_result_text_log.copy()
    st.session_state.parsed_result_text_log = pd.concat([prev_text, parsed_df], ignore_index=True).drop_duplicates(
        subset=["날짜","경마장","경주번호"], keep="last"
    )

    base_combos = operation_combos if "operation_combos" in globals() and len(operation_combos) else combos
    compare_df = auto_compare_combos_with_results(base_combos, st.session_state.race_results) if "auto_compare_combos_with_results" in globals() else pd.DataFrame()
    updated = update_observations_from_results(st.session_state.race_results) if "update_observations_from_results" in globals() else 0
    if "update_learning_memory_from_records" in globals():
        update_learning_memory_from_records()
    return len(compare_df), updated



def schedule_watch_summary(combos_df):
    active, window = is_now_in_watch_window()
    c = add_time_phase_to_combos(combos_df)
    if c is None or len(c) == 0:
        return active, window, pd.DataFrame()
    hot = c[c["시간대상태"].astype(str).str.contains("집중감시|강력감시|특급감시|최종확인", na=False)].copy()
    return active, window, hot.sort_values("출발까지분")

def should_fire_time_based_super_alert(row):
    phase, diff = high_odds_time_phase(row)
    if phase in ["🚨 최종확인", "🚨 특급감시", "🔥 강력감시"]:
        return True
    return False



def render_watch_mode_panel(super_count=0):
    if st.session_state.watch_mode_on:
        st.markdown(f"""
        <div class="watch-on">
          <div class="watch-title">📱 감시모드 ON</div>
          앱을 열어둔 상태에서 자동 확인 중입니다.<br>
          확인 간격: <b>{watch_check_sec}초</b><br>
          특급 후보: <b>{super_count}개</b><br>
          화면 꺼짐 방지: <b>{"시도 중" if watch_keep_awake else "OFF"}</b><br>
          필요하면 아래 버튼으로 바로 끌 수 있습니다.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="watch-off">
          <div class="watch-title">📴 감시모드 OFF</div>
          감시모드가 꺼져 있습니다. 앱이 자동으로 휴대폰을 열 수는 없지만,
          감시모드를 켜두면 앱이 열린 상태에서 자동 확인·진동·경고음이 작동합니다.
        </div>
        """, unsafe_allow_html=True)



def super_alert_js(sound_on=True):
    # Strong vibration + siren-like beep. Browser may block sound until user interaction.
    sound_script = """
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const gain = ctx.createGain(); gain.gain.value = 0.12; gain.connect(ctx.destination);
      let t = ctx.currentTime;
      for (let i=0; i<7; i++) {
        let osc = ctx.createOscillator();
        osc.type = 'square';
        osc.frequency.setValueAtTime(i % 2 === 0 ? 880 : 1320, t + i*0.18);
        osc.connect(gain);
        osc.start(t + i*0.18);
        osc.stop(t + i*0.18 + 0.14);
      }
      setTimeout(()=>ctx.close(), 1800);
    } catch(e) {}
    """ if sound_on else ""
    components.html(f"""
    <script>
    try {{
      if (navigator.vibrate) {{
        navigator.vibrate([900,160,900,160,1300,250,1300]);
      }}
    }} catch(e) {{}}
    {sound_script}
    </script>
    """, height=0)

def sms_style_text(row):
    return f"""[MARU 특급 경고]
놓치면 아까운 조합 발견

경마장: {row.get('경마장','')}
경주: {row.get('경주번호','')}R / {row.get('출발시간','')}
방식: {row.get('방식','')}
1착: {row.get('1착','')}
2착: {row.get('2착','')}
3착: {row.get('3착','')}

예상배당: {row.get('예상배당','')}배
시간대: {row.get('시간대상태','')} / 출발까지 {row.get('출발까지분','')}분
조합점수: {row.get('조합점수','')}
위험합계: {row.get('위험합계','')}
신뢰등급: {row.get('신뢰등급','')}

※ 공식 페이지에서 직접 확인 후 수동구매
"""

def render_super_alert(row):
    st.markdown(f"""
    <div class="super-alert">
      <div class="super-alert-title">🚨 놓치면 아까운 특급 조합</div>
      <div class="super-alert-body">
        경마장: <b>{row.get('경마장','')}</b> /
        경주: <b>{row.get('경주번호','')}R {row.get('출발시간','')}</b><br>
        방식: <b>{row.get('방식','')}</b><br>
        1착: <b>{row.get('1착','')}</b><br>
        2착: <b>{row.get('2착','')}</b><br>
        3착: <b>{row.get('3착','')}</b><br>
        예상배당: <b>{row.get('예상배당','')}배</b> /
        조합점수: <b>{row.get('조합점수','')}</b> /
        위험합계: <b>{row.get('위험합계','')}</b><br>
        신뢰등급: <b>{row.get('신뢰등급','')}</b>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f'<div class="sms-alert">{sms_style_text(row)}</div>', unsafe_allow_html=True)



def result_compare_stats():
    log = st.session_state.result_compare_log if "result_compare_log" in st.session_state else pd.DataFrame()
    if len(log) == 0:
        return pd.DataFrame([{"구분":"결과비교","전체":0,"적중":0,"실패":0,"적중률":"0%","평균최종배당":0}])
    hit = int((log["판정"] == "적중").sum())
    fail = int((log["판정"] == "실패").sum())
    total = hit + fail
    rate = round(hit / total * 100, 1) if total else 0
    avg_odds = round(pd.to_numeric(log["최종배당"], errors="coerce").fillna(0).mean(), 1)
    return pd.DataFrame([{"구분":"결과비교","전체":total,"적중":hit,"실패":fail,"적중률":f"{rate}%","평균최종배당":avg_odds}])



def observation_stats():
    obs = st.session_state.observation_records if "observation_records" in st.session_state else pd.DataFrame()
    if len(obs) == 0:
        return pd.DataFrame([{"구분":"관찰","전체":0,"적중":0,"실패":0,"대기":0,"관찰적중률":"0%"}])
    hit = int(obs["관찰결과"].astype(str).isin(["적중","성공"]).sum())
    fail = int(obs["관찰결과"].astype(str).isin(["실패","미적중","놓침"]).sum())
    pending = int(obs["관찰결과"].astype(str).isin(["결과대기","대기",""]).sum())
    total_done = hit + fail
    rate = round(hit / total_done * 100, 1) if total_done else 0
    return pd.DataFrame([{"구분":"미구매 관찰","전체":len(obs),"적중":hit,"실패":fail,"대기":pending,"관찰적중률":f"{rate}%"}])

def purchase_vs_observe_stats():
    obs = observation_stats()
    purchase = st.session_state.records.copy() if "records" in st.session_state else pd.DataFrame()
    if len(purchase):
        bet = purchase[purchase["결과"].astype(str).isin(["적중","실패"])]
        hit = int((bet["결과"].astype(str) == "적중").sum())
        fail = int((bet["결과"].astype(str) == "실패").sum())
        total = hit + fail
        rate = round(hit / total * 100, 1) if total else 0
    else:
        hit = fail = total = rate = 0
    return pd.DataFrame([
        {"구분":"실제구매","전체":total,"적중":hit,"실패":fail,"대기":0,"적중률":f"{rate}%"},
        {"구분":"미구매관찰","전체":int(obs.iloc[0]["전체"]),"적중":int(obs.iloc[0]["적중"]),"실패":int(obs.iloc[0]["실패"]),"대기":int(obs.iloc[0]["대기"]),"적중률":obs.iloc[0]["관찰적중률"]},
    ])



def factor_table(records, result):
    r=records[records["결과"]==result].tail(20)
    factors=[]
    for _,row in r.iterrows():
        factors += [x for x in str(row.get("공통요인","")).split("|") if x and x!="nan"]
    if not factors: return pd.DataFrame(columns=["요인","건수"])
    s=pd.Series(factors).value_counts().reset_index()
    s.columns=["요인","건수"]
    return s

st.sidebar.title("설정")

st.sidebar.success("안정 롤백판: 텔레그램/Google Sheet/감시모드 메뉴 복구")

st.sidebar.divider()
st.sidebar.subheader("API 자동값")
api_key = st.sidebar.text_input("공공데이터 API Key", value=str(api_secret_value("api_key", api_secret_value("API_KEY", ""))), type="password")

# 19개 API URL은 앱 안에 고정 적용됩니다. 현장에서 매번 URL을 다시 입력하지 않습니다.
race_url = str(api_secret_value("race_url"))
entry_url = str(api_secret_value("entry_url"))
horse_url = str(api_secret_value("horse_url"))
body_url = str(api_secret_value("body_url"))
gear_url = str(api_secret_value("gear_url"))
rating_url = str(api_secret_value("rating_url"))
odds_url = str(api_secret_value("odds_url"))
today_odds_url = str(api_secret_value("today_odds_url"))
result_detail_url = str(api_secret_value("result_detail_url"))
race_record_url = str(api_secret_value("race_record_url"))
start_exam_url = str(api_secret_value("start_exam_url"))
judge_url = str(api_secret_value("judge_url"))
jockey_change_url = str(api_secret_value("jockey_change_url"))
weather_alert_url = str(api_secret_value("weather_alert_url"))
corner_pace_url = str(api_secret_value("corner_pace_url"))
popularity_url = str(api_secret_value("popularity_url"))
first_odds_url = str(api_secret_value("first_odds_url"))
second_odds_url = str(api_secret_value("second_odds_url"))
third_odds_url = str(api_secret_value("third_odds_url"))

st.sidebar.success("19개 API URL 자동 적용 완료 · URL 재입력 필요 없음")
with st.sidebar.expander("적용된 19개 API URL 확인", expanded=False):
    for _api_key_name, _api_label in API_URL_LABELS:
        st.caption(f"{_api_label}: {api_secret_value(_api_key_name)}")

st.sidebar.caption("URL은 앱 기본값으로 자동 적용 / API Key만 입력 또는 Secrets 사용")

st.sidebar.caption("이번 버전은 꼬인 API 강제입력판을 중단하고, 기존 안정 UI로 되돌린 버전입니다.")

mobile_fast_mode = st.sidebar.checkbox("📱 모바일 빠른모드", value=True)
show_deep_tabs = st.sidebar.checkbox("상세 분석 탭 표시", value=False)
server_cache_ttl = st.sidebar.selectbox("서버 분석 캐시 시간", [30, 60, 120, 300, 600], index=2, format_func=lambda x: f"{x}초")

course = st.sidebar.selectbox("경마장", list(KRA_URLS.keys()))
stake = st.sidebar.number_input("1조합 투자금", 100, 50000, 10000, 1000)
target_return = st.sidebar.number_input("목표환급", 10000, 5000000, 300000, 10000)
max_combos = st.sidebar.slider("표시 조합 수", 3, 50, 15)
official = st.sidebar.text_input("공식 페이지", KRA_URLS[course])
auto_run_enabled = st.sidebar.checkbox("앱 켜면 자동 분석", value=True)
auto_refresh_sec = st.sidebar.selectbox("자동 새로고침 간격", [0, 30, 60, 120, 300], index=2, format_func=lambda x: "꺼짐" if x == 0 else f"{x}초")
auto_alarm_enabled = st.sidebar.checkbox("30배 후보 자동 진동", value=True)
st.sidebar.markdown("---")
result_sheet_url = st.sidebar.text_input("결과표 Google Sheet/CSV 주소", "")
auto_result_compare = st.sidebar.checkbox("결과표 자동 비교", value=True)
final_odds_mode = st.sidebar.checkbox("최종배당 통계 반영", value=True)
st.sidebar.markdown("---")
super_alert_enabled = st.sidebar.checkbox("🚨 특급 강력알림 ON", value=True)
super_alert_min_odds = st.sidebar.number_input("특급알림 최소배당", 20.0, 300.0, 30.0, 5.0)
super_alert_min_score = st.sidebar.number_input("특급알림 최소점수", 60.0, 100.0, 78.0, 1.0)
super_alert_max_risk = st.sidebar.slider("특급알림 최대 위험합계", 0, 10, 3)
super_alert_sound = st.sidebar.checkbox("경고음 ON", value=True)
st.sidebar.markdown("---")
watch_check_sec = st.sidebar.selectbox("감시모드 자동확인 간격", [15, 30, 60, 120, 300], index=1, format_func=lambda x: f"{x}초")
watch_keep_awake = st.sidebar.checkbox("감시 중 화면 꺼짐 방지 시도", value=True)
watch_auto_stop_min = st.sidebar.selectbox("감시모드 자동 종료", [0, 30, 60, 120, 180, 240], index=0, format_func=lambda x: "수동으로 끄기" if x == 0 else f"{x}분 후 자동 종료")
st.sidebar.markdown("---")
auto_save_recommend_text = st.sidebar.checkbox("추천문구 자동 저장", value=True)
result_text_parse_on = st.sidebar.checkbox("결과문구 붙여넣기 자동해석", value=True)
st.sidebar.markdown("---")
final_decision_enabled = st.sidebar.checkbox("오늘 최종판정 카드 ON", value=True)
backup_panel_enabled = st.sidebar.checkbox("기록 백업/불러오기 ON", value=True)
daily_report_enabled = st.sidebar.checkbox("하루 마감 리포트 ON", value=True)
st.sidebar.markdown("---")
stable_status_enabled = st.sidebar.checkbox("상태 점검판 ON", value=True)
ultra_mobile_home_enabled = st.sidebar.checkbox("초간단 모바일 홈 ON", value=True)
kra_result_auto_enhanced = st.sidebar.checkbox("KRA 결과표 자동수집 강화", value=True)
external_alert_ready = st.sidebar.checkbox("텔레그램/외부알림 준비", value=False)
telegram_chat_id = st.sidebar.text_input("텔레그램 Chat ID", "", type="password")
telegram_bot_token = st.sidebar.text_input("텔레그램 Bot Token", "", type="password")
google_auto_save_ready = st.sidebar.checkbox("Google Sheet 자동저장 준비", value=False)
race_schedule_watch = st.sidebar.checkbox("경주 시간대 자동 감시", value=True)
race_day_type = st.sidebar.selectbox("경마 시간표 유형", ["일반 주간", "야간 금요일", "야간 토요일", "수동 설정"], index=0)
manual_watch_start = st.sidebar.text_input("수동 감시 시작", "10:30")
manual_watch_end = st.sidebar.text_input("수동 감시 종료", "18:10")
high_odds_watch_min = st.sidebar.slider("30배 집중감시 시작: 출발 전 몇 분", 5, 40, 20)
final_watch_min = st.sidebar.slider("최종확인: 출발 전 몇 분", 1, 10, 3)

google_sheet_url = st.sidebar.text_input("Google Sheet CSV 주소", "")
github_csv_url = st.sidebar.text_input("GitHub CSV 백업 주소", "")
data_priority = st.sidebar.selectbox("데이터 우선순위", ["KRA → Google Sheet → GitHub CSV → 샘플", "Google Sheet → KRA → GitHub CSV → 샘플", "GitHub CSV → Google Sheet → KRA → 샘플"])
st.sidebar.markdown("---")
max_daily_buys = st.sidebar.slider("하루 최대 추천 구매 수", 1, 5, 2)
base_stake = st.sidebar.number_input("기본 투자금", 1000, 100000, int(stake), 1000)
operation_mode = st.sidebar.selectbox("운영 모드", ["안전형", "균형형", "공격형"], index=1)
evolution_mode = st.sidebar.checkbox("AI 진화 학습 ON", value=True)
auto_observe_enabled = st.sidebar.checkbox("구매 안 해도 후보 자동 관찰저장", value=True)
daily_buy_limit = st.sidebar.slider("하루 실제 구매 제한", 1, 2, 1)
observe_top_n = st.sidebar.slider("자동 관찰 저장 후보 수", 3, 20, 10)
weather_type = st.sidebar.selectbox("날씨 조건", ["보통", "비", "무더움", "추움"])
sand_status = st.sidebar.selectbox("모래/주로 특수상태", ["보통", "모래 새로교체", "모래 깊음", "모래 가벼움", "안쪽 무거움", "바깥쪽 무거움"])

st.markdown('<div class="title-card">🐎 MARU KRA 운영안정 최종실전 AI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-card">초간단 모바일 홈 → 상태 점검판 → KRA 결과수집 강화 → 백업/알림 준비까지 운영 안정성을 높였습니다.</div>', unsafe_allow_html=True)

if auto_refresh_sec and auto_refresh_sec > 0:
    components.html(f"""
    <script>
    setTimeout(function() {{
        window.location.reload();
    }}, {auto_refresh_sec * 1000});
    </script>
    """, height=0)



def normalize_sheet_url(url):
    url = str(url).strip()
    if not url:
        return ""
    # Published CSV URL already
    if "output=csv" in url or "format=csv" in url:
        return url
    # Google Sheets edit URL -> CSV export URL
    if "docs.google.com/spreadsheets" in url and "/d/" in url:
        try:
            sheet_id = url.split("/d/")[1].split("/")[0]
            gid = "0"
            if "gid=" in url:
                gid = url.split("gid=")[1].split("&")[0].split("#")[0]
            return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
        except Exception:
            return url
    return url

@st.cache_data(ttl=60)
def fetch_csv_from_url(url):
    try:
        csv_url = normalize_sheet_url(url)
        if not csv_url:
            return False, pd.DataFrame(), "주소 없음"
        df = pd.read_csv(csv_url)
        return True, df, ""
    except Exception as e:
        return False, pd.DataFrame(), str(e)

def load_google_sheet_data():
    if not google_sheet_url:
        return False, "Google Sheet 주소 없음"
    ok, df, err = fetch_csv_from_url(google_sheet_url)
    if ok and len(df):
        st.session_state.df = df
        st.session_state.source_status = "Google Sheet 자동 읽기 성공"
        st.session_state.auto_analysis_status = "자동: Google Sheet → 분석 완료"
        return True, "Google Sheet 성공"
    return False, f"Google Sheet 실패: {err}"

def load_github_csv_data():
    if not github_csv_url:
        return False, "GitHub CSV 주소 없음"
    ok, df, err = fetch_csv_from_url(github_csv_url)
    if ok and len(df):
        st.session_state.df = df
        st.session_state.source_status = "GitHub CSV 백업 자동 읽기 성공"
        st.session_state.auto_analysis_status = "자동: GitHub CSV → 분석 완료"
        return True, "GitHub CSV 성공"
    return False, f"GitHub CSV 실패: {err}"

def load_kra_data():
    ok, tables, err = fetch_kra_tables(KRA_URLS[course])
    st.session_state.raw_tables = tables[:5] if ok else []
    converted = []
    for t in st.session_state.raw_tables:
        c = normalize_kra(t, course)
        if c is not None:
            converted.append(c)
    if converted:
        st.session_state.df = pd.concat(converted, ignore_index=True)
        st.session_state.source_status = "KRA 원본표 자동변환 성공"
        st.session_state.auto_analysis_status = "자동: KRA 원본표 → 분석 완료"
        return True, "KRA 성공"
    return False, "KRA 원본표 자동변환 실패"

def smart_auto_load_data():
    logs = []
    if data_priority.startswith("KRA"):
        steps = [("KRA", load_kra_data), ("Google Sheet", load_google_sheet_data), ("GitHub CSV", load_github_csv_data)]
    elif data_priority.startswith("Google"):
        steps = [("Google Sheet", load_google_sheet_data), ("KRA", load_kra_data), ("GitHub CSV", load_github_csv_data)]
    else:
        steps = [("GitHub CSV", load_github_csv_data), ("Google Sheet", load_google_sheet_data), ("KRA", load_kra_data)]

    for name, fn in steps:
        ok, msg = fn()
        logs.append(f"{name}: {msg}")
        if ok:
            st.session_state.auto_load_log = " | ".join(logs)
            return True

    st.session_state.source_status = "자동 데이터 읽기 실패. 샘플/수동 CSV 기준 분석"
    st.session_state.auto_analysis_status = "자동: 외부데이터 실패 → 샘플/수동 CSV 기준 분석"
    st.session_state.auto_load_log = " | ".join(logs)
    return False


def auto_fetch_kra_once():
    smart_auto_load_data()

if auto_run_enabled and not st.session_state.auto_loaded:
    with st.spinner("KRA 홈페이지 원본표를 자동으로 가져오고 분석 중입니다..."):
        auto_fetch_kra_once()
        st.session_state.auto_loaded = True

st.markdown(f"""
<div class="source-card">
<div class="big">🤖 자동 분석 상태</div>
<div style="font-size:17px;line-height:1.7;">
{st.session_state.auto_analysis_status}<br>
데이터 상태: <b>{st.session_state.source_status}</b><br>
현재 분석 데이터: <b>{len(st.session_state.df)}행</b><br>
자동 읽기 기록: <b>{st.session_state.auto_load_log}</b><br>
KRA 실패 시 Google Sheet, 그다음 GitHub CSV 백업으로 자동 전환합니다.<br>
컴퓨터가 꺼져 있어도 Streamlit Cloud와 Google Sheet 주소가 살아 있으면 휴대폰에서 작동합니다.
</div>
</div>
""", unsafe_allow_html=True)

# 자동 관찰/저장 카운트 기본값 보강
saved_count = globals().get("saved_count", st.session_state.get("saved_count", 0))
today_saved_count = globals().get("today_saved_count", 0)
auto_watch_count = globals().get("auto_watch_count", 0)
updated_obs_count = globals().get("updated_obs_count", 0)
result_msg = globals().get("result_msg", "대기")

evo_score = learning_evolution_score()
st.markdown(f"""
<div class="source-card">
<div class="big">🧬 AI 진화 학습 상태</div>
<div style="font-size:18px;line-height:1.8;">
진화점수: <b>{evo_score}/100</b><br>
오늘 자동 관찰 저장: <b>{saved_count}건</b><br>
실제 구매 제한: <b>하루 {daily_buy_limit}회</b> / 오늘 구매 저장: <b>{st.session_state.daily_purchase_count}회</b><br>
구매하지 않은 후보도 관찰 데이터로 저장되어 나중에 통계자료로 사용됩니다.<br>
결과표 비교: <b>{result_msg}</b> / 관찰 자동판정: <b>{updated_obs_count}건</b>
</div>
</div>
""", unsafe_allow_html=True)

b1,b2,b3=st.columns(3)
with b1:
    if st.button("🔄 지금 다시 자동분석", type="primary", use_container_width=True):
        st.session_state.auto_loaded = False
        auto_fetch_kra_once()
        st.success("다시 자동분석 완료")
        st.rerun()
with b2:
    if st.button("🚨 진동 알람 켜기", use_container_width=True):
        st.session_state.alarm_on=True
        vibrate()
        st.success("진동 알람 ON")
with b3:
    if st.button("🔄 샘플 복구", use_container_width=True):
        st.session_state.df=sample.copy()
        st.session_state.source_status="샘플 데이터 복구"
        st.session_state.auto_analysis_status="샘플 데이터 기준 분석"



# ===== MARU FIX: 운영/구매 보조 함수 선정의 (NameError 방지) =====
def op_auto_stake(row, base_stake=10000, mode="균형형"):
    try:
        odds = float(row.get("예상배당", 0) or 0)
        risk = float(row.get("위험합계", 0) or 0)
        score = float(row.get("조합점수", 0) or 0)
    except Exception:
        odds, risk, score = 0, 0, 0
    mult = 1.0
    if mode == "안전형":
        mult = 0.7
    elif mode == "공격형":
        mult = 1.25
    if risk >= 3:
        mult *= 0.55
    if score >= 80 and 8 <= odds <= 35:
        mult *= 1.15
    amount = int(round(float(base_stake) * mult / 1000) * 1000)
    return max(1000, min(amount, 100000))


def op_guard_combos(combos_df, max_buys=2, base_stake=10000, mode="균형형"):
    if combos_df is None or len(combos_df) == 0:
        return pd.DataFrame()
    c = combos_df.copy()
    if "조합점수" in c.columns:
        c = c.sort_values("조합점수", ascending=False)
    c = c.head(int(max_buys)).copy()
    c["운영판정"] = "✅ 오늘 추천"
    c["자동투자금"] = c.apply(lambda r: op_auto_stake(r, base_stake, mode), axis=1)
    return c


def op_today_summary(horses_df, combos_df, target_odds, max_buys):
    h = horses_df.copy() if horses_df is not None else pd.DataFrame()
    c = combos_df.copy() if combos_df is not None else pd.DataFrame()
    race_count = int(h[["경마장", "경주번호"]].drop_duplicates().shape[0]) if len(h) and {"경마장","경주번호"}.issubset(h.columns) else 0
    over30 = 0
    if len(c) and "예상배당" in c.columns:
        over30 = int((pd.to_numeric(c["예상배당"], errors="coerce").fillna(0) >= float(target_odds)).sum())
    a_grade = int(c["신뢰등급"].astype(str).str.contains("A", na=False).sum()) if len(c) and "신뢰등급" in c.columns else 0
    red_races = int((pd.to_numeric(h.get("빨간경고수", pd.Series(dtype=float)), errors="coerce").fillna(0) > 0).sum()) if len(h) else 0
    recommend_n = min(int(max_buys), len(c))
    if recommend_n <= 0:
        judge = "관망"
    elif a_grade > 0 or over30 > 0:
        judge = "구매 후보 있음"
    else:
        judge = "소액/관찰"
    return {"오늘 경주 수": race_count, "30배 후보": over30, "A등급 후보": a_grade, "빨간경고 경주": red_races, "추천 구매 수": recommend_n, "하루 제한": int(max_buys), "오늘 판단": judge}
# ===== /MARU FIX =====

data=ensure(st.session_state.df)
data_csv_cache = df_to_csv_safe(data)
records_csv_cache = df_to_csv_safe(st.session_state.records)
review_csv_cache = df_to_csv_safe(st.session_state.review_records if "review_records" in st.session_state else pd.DataFrame())
horses, combos, operation_combos, cached_summary, cached_one_line, cached_pvo = server_side_heavy_analysis_cached(
    data_csv_cache, records_csv_cache, review_csv_cache,
    stake, target_return, max_combos, max_daily_buys, base_stake, operation_mode
)
# horses already computed by server cache

horses=apply_confidence_and_warnings(horses)
horses=add_review_plus_scores(horses, data, st.session_state.review_records)
horses=apply_confidence_and_warnings(horses)
combos=combo_engine(horses, stake, target_return, max_combos)
operation_combos = op_guard_combos(combos, max_daily_buys, base_stake, operation_mode)
target_odds=round(target_return/stake,1)
operation_combos = add_time_phase_to_combos(operation_combos) if "operation_combos" in globals() else operation_combos
combos = add_time_phase_to_combos(combos)
auto_recommend_saved_count = auto_save_recommendations(operation_combos if "operation_combos" in globals() and len(operation_combos) else combos, 30)
schedule_active, watch_window_text, hot_time_combos = schedule_watch_summary(operation_combos if "operation_combos" in globals() and len(operation_combos) else combos)

super_candidates = super_alert_candidates(
    operation_combos if "operation_combos" in globals() and len(operation_combos) else combos,
    super_alert_min_odds,
    super_alert_min_score,
    super_alert_max_risk,
    3
)
if super_alert_enabled and len(super_candidates) and (schedule_active or not race_schedule_watch):
    super_best = super_candidates.iloc[0]
    render_super_alert(super_best)
    super_alert_js(super_alert_sound)
    if st.session_state.watch_mode_on:
        browser_notification("MARU 특급 조합", f"{super_best.get('경마장','')} {super_best.get('경주번호','')}R {super_best.get('예상배당','')}배")
else:
    super_best = None

render_watch_mode_panel(len(super_candidates) if "super_candidates" in globals() else 0)
st.markdown(f"""
<div class="source-card">
<div class="big">⏰ 경주 시간대 자동 감시</div>
<div style="font-size:18px;line-height:1.8;">
감시 시간표: <b>{watch_window_text if 'watch_window_text' in globals() else ''}</b><br>
현재 시간대 감시: <b>{"ON" if (schedule_active if 'schedule_active' in globals() else True) else "시간 외 OFF"}</b><br>
30배 집중감시: <b>각 경주 출발 {high_odds_watch_min}분 전부터</b><br>
최종확인: <b>출발 {final_watch_min}분 전</b>
</div>
</div>
""", unsafe_allow_html=True)
if 'hot_time_combos' in globals() and len(hot_time_combos):
    st.subheader("🔥 지금 30배 이상 집중감시 시간대")
    st.dataframe(hot_time_combos.head(10), use_container_width=True)

st.subheader("🔗 추천문구 자동연동 / 결과문구 자동해석")
st.markdown(f"""
<div class="source-card">
<div class="big">추천 자동 저장</div>
오늘 추천문구 자동 저장: <b>{auto_recommend_saved_count if 'auto_recommend_saved_count' in globals() else 0}건</b><br>
결과는 KRA 자동읽기가 실패해도, 결과 문구만 붙여넣으면 자동으로 1착/2착/3착/배당을 해석합니다.
</div>
""", unsafe_allow_html=True)

with st.expander("결과문구 붙여넣기 자동해석", expanded=False):
    default_course_for_text = st.selectbox("기본 경마장", ["서울","부산경남","제주"], index=0, key="default_course_for_text")
    result_text = st.text_area(
        "결과 문구를 그대로 붙여넣기",
        placeholder="예: 서울 1경주 5번 2번 8번 삼복승 38.5 삼쌍승 210.4",
        height=120,
        key="result_text_parser_area"
    )
    if st.button("결과문구 자동해석 → 결과표 반영", use_container_width=True):
        parsed = parse_result_text_block(result_text, default_course_for_text)
        if len(parsed):
            compared, obs_updated = apply_parsed_results_to_system(parsed)
            st.success(f"결과 {len(parsed)}건 해석 완료 / 비교 {compared}건 / 관찰판정 {obs_updated}건")
            st.dataframe(parsed, use_container_width=True)
        else:
            st.warning("해석된 결과가 없습니다. 예: 1경주 5번 2번 8번 삼복승 38.5 삼쌍승 210.4")

with st.expander("자동 저장된 추천문구 보기", expanded=False):
    st.dataframe(st.session_state.auto_recommend_text_log.tail(100), use_container_width=True)

if st.session_state.watch_mode_on:
    watch_mode_js(watch_check_sec, watch_keep_awake, watch_auto_stop_min)
summary = op_today_summary(horses, combos, target_odds, max_daily_buys)
st.markdown(f"""
<div class="source-card"><div class="big">📌 오늘 자동 요약</div>
<div style="font-size:18px;line-height:1.8;">
오늘 경주 수: <b>{summary['오늘 경주 수']}경주</b> / 30배 후보: <b>{summary['30배 후보']}개</b> / A등급 후보: <b>{summary['A등급 후보']}두</b><br>
빨간경고 경주: <b>{summary['빨간경고 경주']}개</b> / 추천 구매 수: <b>{summary['추천 구매 수']}개</b> / 하루 제한: <b>{summary['하루 제한']}개</b><br>
오늘 판단: <b>{summary['오늘 판단']}</b>
</div></div>
""", unsafe_allow_html=True)

best_source = operation_combos[operation_combos["운영판정"] == "✅ 오늘 추천"] if "operation_combos" in globals() and len(operation_combos) else combos
best = best_source.iloc[0] if len(best_source) else (combos.iloc[0] if len(combos) else None)
if best is not None and best["판정"]!="⛔ 보류":
    if st.session_state.alarm_on or auto_alarm_enabled: vibrate()
    maru_race_title = f"{best['경마장']} {int(best['경주번호'])}R"
    maru_combo_txt = f"{best['1착']} - {best['2착']} - {best['3착']}"
    st.markdown(f"""
    <div class="maru-gold-card">
      <div class="maru-gold-title">🏆 지금 놓치면 아까운 추천</div>
      <div class="maru-gold-main">{maru_race_title}</div>
      <div class="maru-gold-combo">{best['방식']} {maru_combo_txt}</div>
      <div class="maru-metric-grid">
        <div class="maru-metric"><div class="maru-metric-label">예상배당</div><div class="maru-metric-value">{best['예상배당']}배</div></div>
        <div class="maru-metric"><div class="maru-metric-label">신뢰등급</div><div class="maru-metric-value">{best['신뢰등급']}</div></div>
        <div class="maru-metric"><div class="maru-metric-label">위험도</div><div class="maru-metric-value">{best['위험합계'] if '위험합계' in best.index else '-'}</div></div>
      </div>
      <div class="maru-info-grid">
        <div class="maru-info"><b>실시간 상태</b><br>출발시간 {best['출발시간']}<br>판정 {best['판정']}</div>
        <div class="maru-info"><b>기수/말 컨디션</b><br>신뢰 {best['신뢰등급']}<br>인기마 제거 {best['인기마제거판정']}</div>
        <div class="maru-info"><b>예상 환급</b><br>{int(best['예상환급']):,}원<br>순수익 {int(best['예상순수익']):,}원</div>
        <div class="maru-info"><b>운영 판단</b><br>{best['판정']}<br>확신도는 확신도·경고 탭 확인</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown('<div class="alert-card"><div class="alert-big">⛔ 실전 조합 부족</div><div>30배 이상 근거가 부족합니다. KRA 원본 또는 CSV를 넣고 다시 분석하세요.</div></div>', unsafe_allow_html=True)

st.markdown(f'<a class="maru-action-blue" href="{official}" target="_blank">↗ 공식 마권구매 페이지 열기</a>', unsafe_allow_html=True)

if best is not None:
    manual_text = f"""[MARU 최종실전]
판정: {best['판정']}
경마장: {best['경마장']} / {int(best['경주번호'])}R / {best['출발시간']}
방식: {best['방식']}
1착: {best['1착']}
2착: {best['2착']}
3착: {best['3착']}
필요배당: {target_odds}배
예상배당: {best['예상배당']}배
예상환급: {int(best['예상환급']):,}원
신뢰등급: {best['신뢰등급']}
인기마제거: {best['인기마제거판정']}
공식 페이지에서 직접 확인 후 수동구매"""
    maru_buy_combo = f"{best['1착']} - {best['2착']} - {best['3착']}"
    st.markdown(f"""
    <div class="maru-manual-card">
      <div class="maru-red-banner">🔔 지금 바로 확인</div>
      <div class="maru-gold-main">{best['경마장']} {int(best['경주번호'])}경주</div>
      <div class="maru-gold-title">{best['방식']}</div>
      <div class="maru-big-number">{maru_buy_combo}</div>
      <div class="maru-big-won">{int(base_stake):,}원</div>
      <div class="maru-gold-sub">추천 조합을 보고 공식 구매페이지에서 직접 입력</div>
    </div>
    """, unsafe_allow_html=True)
    st.text_area("추천 조합 복사용", manual_text, height=190)
    st.markdown(f'<a class="maru-action-blue" href="{official}" target="_blank">↗ 공식 마권구매 열기</a>', unsafe_allow_html=True)

    r1,r2,r3=st.columns(3)
    with r1:
        if st.button("✅ 적중 기록", use_container_width=True):
            st.session_state.records=pd.concat([st.session_state.records,pd.DataFrame([{"날짜":pd.Timestamp.today().strftime("%Y-%m-%d"),"시간":best["출발시간"],"경마장":best["경마장"],"경주":f"{int(best['경주번호'])}R","발견":best["판정"],"결과":"적중","수익":int(best["예상순수익"]),"방식":best["방식"],"조합":best["메모"],"예상배당":best["예상배당"],"공통요인":"체중 안정|출전간격 안정|최근 순위 상승"}])], ignore_index=True)
            st.success("적중 기록 저장")
    with r2:
        if st.button("❌ 실패 기록", use_container_width=True):
            st.session_state.records=pd.concat([st.session_state.records,pd.DataFrame([{"날짜":pd.Timestamp.today().strftime("%Y-%m-%d"),"시간":best["출발시간"],"경마장":best["경마장"],"경주":f"{int(best['경주번호'])}R","발견":best["판정"],"결과":"실패","수익":-int(best["투자금"]),"방식":best["방식"],"조합":best["메모"],"예상배당":best["예상배당"],"공통요인":"외곽게이트|정확순서 실패"}])], ignore_index=True)
            st.warning("실패 기록 저장")
    with r3:
        if st.button("👀 보류 기록", use_container_width=True):
            st.session_state.records=pd.concat([st.session_state.records,pd.DataFrame([{"날짜":pd.Timestamp.today().strftime("%Y-%m-%d"),"시간":best["출발시간"],"경마장":best["경마장"],"경주":f"{int(best['경주번호'])}R","발견":best["판정"],"결과":"보류","수익":0,"방식":best["방식"],"조합":best["메모"],"예상배당":best["예상배당"],"공통요인":"보류"}])], ignore_index=True)
            st.info("보류 기록 저장")

invested, returned, profit, roi = roi_summary(st.session_state.records)
m1,m2,m3,m4=st.columns(4)
m1.metric("필요배당", f"{target_odds}배")
m2.metric("30배 후보", f"{int((combos['예상배당']>=target_odds).sum()) if len(combos) else 0}개")
m3.metric("총 회수", f"{returned:,}원")
m4.metric("ROI", f"{roi}%")


def op_has_text(v, text):
    return text in str(v)

def op_auto_stake(row, base_stake=10000, mode="균형형"):
    score = pd.to_numeric(row.get("조합점수", 0), errors="coerce")
    odds = pd.to_numeric(row.get("예상배당", 0), errors="coerce")
    risk = pd.to_numeric(row.get("위험합계", 0), errors="coerce")
    if pd.isna(score): score = 0
    if pd.isna(odds): odds = 0
    if pd.isna(risk): risk = 0
    grade = str(row.get("신뢰등급", ""))
    mult = 1.0 if ("A등급" in grade or score >= 84) else 0.5 if ("B등급" in grade or score >= 74) else 0
    if risk >= 4: mult *= 0.5
    if odds >= 120: mult *= 0.5
    if mode == "안전형": mult *= 0.7
    if mode == "공격형": mult *= 1.2
    amount = int(round(base_stake * mult / 1000) * 1000)
    return amount if amount >= 1000 else 0

def op_is_hold_combo(row):
    text = " ".join(str(row.get(k, "")) for k in ["신뢰등급","인기마제거판정","메모","판정"])
    risk = pd.to_numeric(row.get("위험합계", 0), errors="coerce")
    if pd.isna(risk): risk = 0
    return risk >= 5 or "보류" in text or "배당 죽음" in text

def op_guard_combos(combos_df, max_buys=2, base_stake=10000, mode="균형형"):
    if combos_df is None or len(combos_df) == 0:
        return pd.DataFrame()
    c = combos_df.copy()
    c["자동투자금"] = c.apply(lambda r: op_auto_stake(r, base_stake, mode), axis=1)
    c["운영판정"] = c.apply(lambda r: "⛔ 제외" if r["자동투자금"] <= 0 or op_is_hold_combo(r) else "✅ 오늘 추천" if str(r.get("판정","")).startswith(("🔥","💰","🚀")) else "👀 관찰", axis=1)
    c["우선순위점수"] = (pd.to_numeric(c.get("조합점수", 0), errors="coerce").fillna(0)*0.65 + pd.to_numeric(c.get("예상배당", 0), errors="coerce").fillna(0).clip(0,80)*0.25 - pd.to_numeric(c.get("위험합계", 0), errors="coerce").fillna(0)*4).round(1)
    valid = c[c["운영판정"] == "✅ 오늘 추천"].sort_values("우선순위점수", ascending=False)
    keep = set(valid.head(max_buys).index)
    c.loc[(c["운영판정"] == "✅ 오늘 추천") & (~c.index.isin(keep)), "운영판정"] = "👀 과다방지 관찰"
    return c.sort_values(["운영판정","우선순위점수"], ascending=[True, False])

def op_today_summary(horses_df, combos_df, target_odds, max_buys):
    races = int(horses_df[["경마장","경주번호"]].drop_duplicates().shape[0]) if horses_df is not None and len(horses_df) else 0
    over30 = int((pd.to_numeric(combos_df.get("예상배당", pd.Series(dtype=float)), errors="coerce") >= target_odds).sum()) if combos_df is not None and len(combos_df) else 0
    grade_col = "확신등급" if horses_df is not None and "확신등급" in horses_df.columns else "최종판정"
    a_horses = int(horses_df[grade_col].astype(str).str.contains("A등급", na=False).sum()) if horses_df is not None and len(horses_df) and grade_col in horses_df.columns else 0
    red_races = 0
    if horses_df is not None and len(horses_df) and "빨간경고수" in horses_df.columns:
        tmp = horses_df.copy(); tmp["빨간경고수"] = pd.to_numeric(tmp["빨간경고수"], errors="coerce").fillna(0)
        red_races = int(tmp.groupby(["경마장","경주번호"])["빨간경고수"].max().ge(3).sum())
    op = op_guard_combos(combos_df, max_buys, base_stake if "base_stake" in globals() else 10000, operation_mode if "operation_mode" in globals() else "균형형")
    recommended = int((op["운영판정"] == "✅ 오늘 추천").sum()) if len(op) else 0
    conclusion = "🔥 실전 가능" if recommended and a_horses else "💰 소액/관찰" if over30 else "⛔ 관망"
    return {"오늘 경주 수":races,"30배 후보":over30,"A등급 후보":a_horses,"빨간경고 경주":red_races,"추천 구매 수":recommended,"하루 제한":max_buys,"오늘 판단":conclusion}

def op_race_lines(horses_df, combos_df, target_odds):
    rows=[]
    if horses_df is None or len(horses_df)==0: return pd.DataFrame(rows)
    for (course, race_no), g in horses_df.groupby(["경마장","경주번호"]):
        rc = combos_df[(combos_df["경마장"]==course)&(combos_df["경주번호"]==race_no)] if combos_df is not None and len(combos_df) else pd.DataFrame()
        over30 = int((pd.to_numeric(rc.get("예상배당", pd.Series(dtype=float)), errors="coerce")>=target_odds).sum()) if len(rc) else 0
        grade_col = "확신등급" if "확신등급" in g.columns else "최종판정"
        a = int(g[grade_col].astype(str).str.contains("A등급", na=False).sum()) if grade_col in g.columns else 0
        risk = int(pd.to_numeric(g.get("빨간경고수", pd.Series([0]*len(g))), errors="coerce").fillna(0).max())
        pace = str(g.get("페이스예상", pd.Series([""])).iloc[0]) if "페이스예상" in g.columns else ""
        adv = str(g.get("페이스유리", pd.Series([""])).iloc[0]) if "페이스유리" in g.columns else ""
        if over30 and a and risk < 3: line=f"{course} {int(race_no)}R: {pace} / {adv} → 30배 후보 있음, 실전 후보"
        elif risk >= 3: line=f"{course} {int(race_no)}R: 빨간경고 많음 → 보류"
        elif over30: line=f"{course} {int(race_no)}R: 30배 후보는 있으나 A등급 부족 → 소액/관찰"
        else: line=f"{course} {int(race_no)}R: 30배 후보 부족 → 관망"
        rows.append({"경주":f"{course} {int(race_no)}R","한줄결론":line,"30배후보":over30,"A등급":a,"위험":risk})
    return pd.DataFrame(rows)

def op_missed_candidates(review_records, horses_df):
    if review_records is None or len(review_records)==0 or "빠진말" not in review_records.columns:
        return pd.DataFrame(columns=["놓친말","건수","최근원인","현재후보"])
    rr=review_records[review_records["빠진말"].astype(str).str.len()>0]
    if len(rr)==0: return pd.DataFrame(columns=["놓친말","건수","최근원인","현재후보"])
    out=rr.groupby("빠진말").agg(건수=("빠진말","count"), 최근원인=("실패원인", lambda x:" / ".join(str(v) for v in x.tail(3)))).reset_index().sort_values("건수", ascending=False)
    current=set()
    if horses_df is not None and len(horses_df) and "마번" in horses_df.columns:
        current=set(f"{int(x)}번" for x in pd.to_numeric(horses_df["마번"], errors="coerce").dropna())
    out["현재후보"]=out["놓친말"].apply(lambda x: "오늘 출전 가능성 있음" if str(x) in current else "현재 표에는 없음")
    return out

def op_absolute_hold(horses_df, combos_df):
    hold_h=pd.DataFrame(); hold_c=pd.DataFrame()
    if horses_df is not None and len(horses_df):
        h=horses_df.copy(); mask=pd.Series(False, index=h.index)
        if "빨간경고수" in h.columns: mask |= pd.to_numeric(h["빨간경고수"], errors="coerce").fillna(0) >= 3
        if "체중증감" in h.columns: mask |= pd.to_numeric(h["체중증감"], errors="coerce").fillna(0) <= -12
        if "출전간격일" in h.columns: mask |= pd.to_numeric(h["출전간격일"], errors="coerce").fillna(0) >= 120
        hold_h=h[mask]
    if combos_df is not None and len(combos_df): hold_c=combos_df[combos_df.apply(op_is_hold_combo, axis=1)]
    return hold_h, hold_c



st.subheader("🚨 특급 알림 후보 전체")
if "super_candidates" in globals() and len(super_candidates):
    st.dataframe(super_candidates, use_container_width=True)
else:
    st.info("현재 특급 알림 기준을 만족하는 조합은 없습니다.")

if mobile_fast_mode:
    st.subheader("📱 모바일 빠른 화면")
    render_final_decision_card(operation_combos if "operation_combos" in globals() and len(operation_combos) else combos)

    st.markdown("""
### 30배 이상 배당 집중 시간대
30배 이상 조합은 특정 시각 하나보다 **각 경주 출발 전 20분~3분**이 핵심입니다.

```text
출발 30분 전: 사전관찰
출발 20분 전: 30배 집중감시
출발 10분 전: 강력감시
출발 5분 전: 특급감시
출발 3분 전: 최종확인
```
""")
    if 'hot_time_combos' in globals() and len(hot_time_combos):
        st.dataframe(hot_time_combos.head(5), use_container_width=True)

    st.markdown("""
### 감시모드 안내
핸드폰이 완전히 꺼진 상태에서 웹앱이 스스로 켜지지는 않습니다.  
대신 감시모드를 켜두면 앱이 열린 상태에서 자동 확인하고, 특급 조합이 뜨면 강력 진동·경고음·화면 번쩍임을 줍니다.
""")
    st.caption("무거운 분석은 서버에서 계산하고, 휴대폰에는 핵심 결과만 먼저 보여줍니다.")

    s = summary if "summary" in globals() else cached_summary
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("오늘 판단", s.get("오늘 판단", ""))
    m2.metric("30배 후보", f"{s.get('30배 후보', 0)}개")
    m3.metric("추천 구매", f"{s.get('추천 구매 수', 0)}개")
    m4.metric("하루 제한", f"{s.get('하루 제한', 0)}개")

    if "operation_combos" in globals() and len(operation_combos):
        st.subheader("오늘 바로 볼 추천 1~2개")
        mobile_cols = ["운영판정","판정","경마장","경주번호","출발시간","방식","1착","2착","3착","예상배당","자동투자금","신뢰등급","메모"]
        mobile_cols = [c for c in mobile_cols if c in operation_combos.columns]
        st.dataframe(operation_combos.head(max_daily_buys if "max_daily_buys" in globals() else 2)[mobile_cols], use_container_width=True)
    else:
        st.info("현재 추천 조합이 없습니다.")

    if "cached_one_line" in globals() and len(cached_one_line):
        st.subheader("경주별 한 줄 결론")
        st.dataframe(cached_one_line, use_container_width=True)

    st.markdown("""
### 모바일 빠른모드 사용법
- 첫 화면에서는 오늘요약, 추천 1~2개, 한줄결론만 봅니다.
- 착차/전개/복기/AI학습 같은 상세 기능은 서버에서 계산되지만 화면에는 숨깁니다.
- 필요할 때 왼쪽에서 `상세 분석 탭 표시`를 켜면 전체 탭을 볼 수 있습니다.
""")

    if not show_deep_tabs:
        st.warning("상세 분석 탭은 숨김 상태입니다. 기능은 유지되고 서버에서 계산됩니다.")

if mobile_fast_mode and not show_deep_tabs:
    st.stop()

tabs=st.tabs(["🎯 종합판단","📌 오늘요약","🧬 AI진화학습","🚨 특급알림","🏁 결과자동비교","💸 최종배당통계","👀 미구매관찰","📊 구매vs관찰","🧾 경주별 한줄결론","👻 놓친말 후보","🧯 과다방지·투자금","🚫 절대보류","✅ 확신도·경고","🛑 오늘 쉬는 날","📚 누적100·500","🏇 착차분석","🧭 전개분석","🤝 기수+조교사","⚖️ 정상체중","📝 실패조합복기","🏁 최종점수","🏃 페이스예상","🎂 마령보정","📉 배당급변","🧭 코스통계","🧱 실패블랙리스트","🌦️ 날씨·주로 특수보정","❗ 인기마제거","🔥 30배조합","🐎 마필누적","🧑‍✈️ 기수통계","📏 거리성적","🌦️ 주로상태","💹 ROI","✅ 왜 적중","❌ 실패원인","⏰ 시간표/출마표","🌐 원본표","📂 CSV","🟩 구글시트","📘 사용법"])

with tabs[0]:
    st.subheader("🎯 종합 실전판단")
    a_grade = int((horses["최종판정"].str.contains("A등급")).sum())
    over30 = int((combos["예상배당"]>=target_odds).sum()) if len(combos) else 0
    conclusion = "🔥 도전 가능" if over30 and a_grade and roi>=80 else "💰 소액 도전" if over30 else "⛔ 보류"
    c1,c2,c3,c4=st.columns(4)
    c1.metric("오늘 결론", conclusion)
    c2.metric("A등급 말", f"{a_grade}두")
    c3.metric("30배 조합", f"{over30}개")
    c4.metric("ROI", f"{roi}%")
    st.dataframe(operation_combos.head(10) if "operation_combos" in globals() and len(operation_combos) else combos.head(10), use_container_width=True)

with tabs[1]:
    st.subheader("📌 오늘 경주 자동 요약 카드")
    st.dataframe(pd.DataFrame([summary]), use_container_width=True)
    st.markdown("""
### 해석
- 추천 구매 수가 0이면 관망입니다.
- A등급 후보와 30배 후보가 같이 있을 때 실전 후보로 봅니다.
- 빨간경고 경주가 많으면 구매 수를 줄입니다.
""")

with tabs[2]:
    st.subheader("🧬 학습으로 진화하는 AI")
    update_learning_memory_from_records()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("AI 진화점수", f"{learning_evolution_score()}/100")
    c2.metric("미구매 관찰", f"{len(st.session_state.observation_records)}건")
    c3.metric("실제 구매기록", f"{len(st.session_state.records)}건")
    c4.metric("오늘 구매 제한", f"{st.session_state.daily_purchase_count}/{daily_buy_limit}")
    st.markdown("""
### 구조
구매한 조합만 배우는 것이 아니라, **구매하지 않은 후보도 관찰 데이터로 저장**합니다.
결과표가 들어오면 산 조합과 안 산 조합을 모두 자동 비교합니다.

```text
후보 발견 → 미구매 관찰 저장 → 결과 확인 → 적중/실패 표시 → 통계 반영 → 다음 분석 보정
```
""")
    st.subheader("학습 메모리")
    st.dataframe(st.session_state.learning_memory.tail(100), use_container_width=True)

with tabs[3]:
    st.subheader("🏁 실제 결과표 자동 비교")
    st.markdown("""
결과표 Google Sheet/CSV가 연결되면 AI 추천 조합과 실제 1·2·3착을 자동 비교합니다.

```text
구매 조합 → 실제 결과와 비교 → 적중/실패 자동 판정
미구매 관찰 조합 → 실제 결과와 비교 → 샀으면 맞았는지 자동 판정
```
""")
    if result_sheet_url:
        st.success(f"결과표 연결 상태: {result_msg}")
    else:
        st.info("왼쪽 설정에 결과표 Google Sheet/CSV 주소를 넣으면 자동 비교됩니다.")

    st.subheader("결과표")
    st.dataframe(st.session_state.race_results.tail(100), use_container_width=True)

    st.subheader("자동 비교 로그")
    st.dataframe(st.session_state.result_compare_log.tail(200), use_container_width=True)

    st.subheader("결과표 수동 업로드")
    result_file = st.file_uploader("결과표 CSV 업로드", type=["csv"], key="result_csv_upload")
    if result_file:
        st.session_state.race_results = normalize_result_df(pd.read_csv(result_file))
        compare_now = auto_compare_combos_with_results(operation_combos if "operation_combos" in globals() else combos, st.session_state.race_results)
        updated_obs_count = update_observations_from_results(st.session_state.race_results)
        update_learning_memory_from_records()
        st.success(f"결과표 업로드 및 자동 비교 완료 / 관찰 {updated_obs_count}건 판정")

with tabs[4]:
    st.subheader("💸 최종배당 기록 / 통계")
    st.markdown("""
예상배당과 최종배당을 비교해서 수익성이 실제로 유지됐는지 봅니다.

예:
- 예상 35배 → 최종 18배: 수익성 하락
- 예상 25배 → 최종 42배: 복병 가치 상승
""")
    st.dataframe(result_compare_stats(), use_container_width=True)
    if len(st.session_state.result_compare_log):
        log = st.session_state.result_compare_log.copy()
        log["배당차이"] = pd.to_numeric(log["최종배당"], errors="coerce").fillna(0) - pd.to_numeric(log["예상배당"], errors="coerce").fillna(0)
        st.dataframe(log.sort_values("배당차이", ascending=False).tail(200), use_container_width=True)
    else:
        st.info("아직 결과 비교 로그가 없습니다.")


with tabs[5]:
    st.subheader("👀 구매 안 한 후보 자동 관찰 데이터")
    st.markdown(f"""
자동 관찰 저장은 상위 **{observe_top_n}개 후보**까지 저장합니다.  
실제로 구매하지 않아도 나중에 결과를 입력하면 통계자료로 쓸 수 있습니다.
""")
    st.dataframe(st.session_state.observation_records.tail(200), use_container_width=True)

    st.markdown("### 관찰 결과 수동 업데이트")
    if len(st.session_state.observation_records):
        obs_idx = st.number_input("수정할 관찰행 번호", 0, max(0, len(st.session_state.observation_records)-1), max(0, len(st.session_state.observation_records)-1))
        obs_result = st.selectbox("관찰 결과", ["결과대기","적중","실패","놓침","보류"])
        actual_result = st.text_input("실제 결과/들어온 말", "")
        if st.button("👀 관찰 결과 저장", use_container_width=True):
            st.session_state.observation_records.loc[int(obs_idx), "관찰결과"] = obs_result
            st.session_state.observation_records.loc[int(obs_idx), "실제결과"] = actual_result
            update_learning_memory_from_records()
            st.success("관찰 결과 저장 완료")

with tabs[6]:
    st.subheader("📊 실제 구매 vs 미구매 관찰 통계")
    st.dataframe(purchase_vs_observe_stats(), use_container_width=True)
    st.subheader("관찰 통계")
    st.dataframe(observation_stats(), use_container_width=True)
    st.markdown("""
### 해석
- 실제 구매는 하루 1~2회만 해도 됩니다.
- 나머지 후보는 관찰 기록으로 쌓습니다.
- 관찰 적중률이 높은 조건이 반복되면 다음 실전 구매 후보로 승격합니다.
""")


with tabs[7]:
    st.subheader("🧾 경주별 한 줄 결론")
    one_line = op_race_lines(horses, combos, target_odds)
    st.dataframe(one_line, use_container_width=True)
    for _, row in one_line.iterrows():
        st.markdown(f"- **{row['한줄결론']}**")

with tabs[8]:
    st.subheader("👻 놓친 말 자동 후보")
    missed = op_missed_candidates(st.session_state.review_records if "review_records" in st.session_state else pd.DataFrame(), horses)
    st.dataframe(missed, use_container_width=True)

with tabs[9]:
    st.subheader("🧯 조합 과다 방지 / 투자금 자동 조절")
    st.markdown(f"""
### 현재 운영 설정
- 운영 모드: **{operation_mode}**
- 하루 최대 추천 구매 수: **{max_daily_buys}개**
- 기본 투자금: **{int(base_stake):,}원**

A등급은 기본 투자금, B등급은 절반, C/D등급은 제외합니다. 위험합계가 높거나 120배 이상 초고배당이면 자동으로 소액화합니다.
""")
    st.dataframe(operation_combos if "operation_combos" in globals() and len(operation_combos) else combos, use_container_width=True)

with tabs[10]:
    st.subheader("🚫 절대 보류 규칙")
    hold_horses, hold_combos = op_absolute_hold(horses, combos)
    st.markdown("""
아무리 배당이 좋아도 아래 조건이면 보류 쪽으로 봅니다.

- 빨간경고 3개 이상
- 체중 -12kg 이상
- 4개월 이상 공백
- 인기마 과다로 배당 죽음
- 위험합계 과다
""")
    st.subheader("보류 대상 말")
    st.dataframe(hold_horses, use_container_width=True)
    st.subheader("보류 대상 조합")
    st.dataframe(hold_combos, use_container_width=True)

with tabs[11]:
    st.subheader("✅ 확신도(%) / 빨간 경고 시스템")
    st.markdown("""
### 기준
- A등급: 확신도 90% 이상
- B등급: 70~89%
- C등급: 60~69%
- D등급: 보류

빨간 경고가 3개 이상이면 자동 D등급으로 내립니다.
""")
    st.dataframe(horses[[
        "경주마","마번","현재배당","최종실전점수","확신도","추천별점","확신등급",
        "빨간경고수","빨간경고","최종판정"
    ]].sort_values("확신도", ascending=False), use_container_width=True)

with tabs[12]:
    st.subheader("🛑 오늘 쉬는 날 판단")
    rest_result, rest_reason = today_rest_decision(combos, horses, target_odds)
    over30 = int((combos["예상배당"] >= target_odds).sum()) if len(combos) else 0
    a_count = int((horses["확신등급"].astype(str).str.contains("A등급")).sum()) if len(horses) else 0
    r1, r2, r3 = st.columns(3)
    r1.metric("오늘 결론", rest_result)
    r2.metric("30배 후보", f"{over30}개")
    r3.metric("A등급", f"{a_count}개")
    st.markdown(f"""
### 이유
**{rest_reason}**

돈 버는 사람은 사는 날보다 **안 사는 날**을 잘 고릅니다.
""")

with tabs[13]:
    st.subheader("📚 최근 100회 / 500회 누적 자기학습")
    s100 = record_window_stats(st.session_state.records, 100)
    s500 = record_window_stats(st.session_state.records, 500)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("최근100 적중률", f"{s100['적중률']}%")
    c2.metric("최근100 ROI", f"{s100['ROI']}%")
    c3.metric("최근500 적중률", f"{s500['적중률']}%")
    c4.metric("최근500 ROI", f"{s500['ROI']}%")
    st.subheader("최근 100회")
    st.dataframe(pd.DataFrame([s100]), use_container_width=True)
    st.subheader("최근 500회")
    st.dataframe(pd.DataFrame([s500]), use_container_width=True)
    st.subheader("실패 원인 TOP10")
    st.dataframe(failure_top10(st.session_state.records), use_container_width=True)


with tabs[14]:
    st.subheader("🏇 착차 분석")
    st.markdown("순위만 보지 않고, 얼마나 근소하게 졌는지/크게 졌는지 반영합니다.")
    st.dataframe(horses[[
        "경주마","마번","순위","착차","착차점수","착차메모","최종실전점수","확신도","확신등급"
    ]].sort_values("착차점수", ascending=False), use_container_width=True)

with tabs[15]:
    st.subheader("🧭 초반/중반/4코너/결승 전개 분석")
    st.markdown("초반만 빠른 말, 막판 추입형, 선행 유지형, 직선에서 무너지는 말을 구분합니다.")
    st.dataframe(horses[[
        "경주마","마번","초반위치","중반위치","4코너위치","결승위치",
        "전개점수","전개메모","주행습성","최종실전점수","확신등급"
    ]].sort_values("전개점수", ascending=False), use_container_width=True)

with tabs[16]:
    st.subheader("🤝 기수+조교사 조합 승률")
    st.markdown("기수 단독보다, 기수+조교사 조합이 실제로 맞는지 봅니다.")
    jt = jockey_trainer_combo_stats(data)
    st.dataframe(jt, use_container_width=True)
    st.subheader("말별 조합점수 반영")
    st.dataframe(horses[[
        "경주마","마번","기수","조교사","기수승률","조교사승률",
        "기수조교사조합점수","최종실전점수","확신등급"
    ]].sort_values("기수조교사조합점수", ascending=False), use_container_width=True)

with tabs[17]:
    st.subheader("⚖️ 말별 정상체중 범위")
    st.markdown("현재체중/평균체중이 있으면 정상 범위 이탈을 보고, 없으면 체중증감으로 판단합니다.")
    st.dataframe(horses[[
        "경주마","마번","현재체중","평균체중","체중증감",
        "정상체중점수","정상체중메모","빨간경고","최종실전점수","확신등급"
    ]].sort_values("정상체중점수", ascending=False), use_container_width=True)

with tabs[18]:
    st.subheader("📝 실패 조합 상세 복기")
    st.markdown("예상 조합과 실제 조합, 빠진 말, 실패 원인을 저장해서 다음 분석에 감점 규칙으로 반영합니다.")
    st.dataframe(st.session_state.review_records.tail(100), use_container_width=True)
    st.subheader("실패 복기 원인 TOP10")
    st.dataframe(review_failure_top(st.session_state.review_records), use_container_width=True)

    st.markdown("### 새 복기 기록 추가")
    c1, c2 = st.columns(2)
    with c1:
        expected_combo = st.text_input("예상 조합", "5-6-8")
        actual_combo = st.text_input("실제 조합", "5-2-8")
        missing_horse = st.text_input("빠진 말 / 놓친 말", "2번")
    with c2:
        fail_reason = st.text_input("실패 원인", "외곽 게이트|체중 급감|거리 약함")
        fix_rule = st.text_input("다음 수정 규칙", "외곽+장거리 조합 감점")
        review_result = st.selectbox("결과", ["실패","적중","보류"])
    if st.button("📝 복기 기록 저장", use_container_width=True):
        new_row = pd.DataFrame([{
            "날짜": pd.Timestamp.today().strftime("%Y-%m-%d"),
            "경마장": course,
            "경주": "",
            "예상조합": expected_combo,
            "실제조합": actual_combo,
            "결과": review_result,
            "빠진말": missing_horse,
            "실패원인": fail_reason,
            "수정규칙": fix_rule
        }])
        st.session_state.review_records = pd.concat([st.session_state.review_records, new_row], ignore_index=True)
        st.success("실패 조합 복기 기록 저장 완료")


with tabs[19]:
    st.dataframe(horses[["경주마","마번","현재배당","최종실전점수","복기강화점수","착차점수","전개점수","정상체중점수","기수조교사조합점수","최종판정","최근5경기흐름","체중변화점수","기수교체점수","출전간격점수","거리전환점수","게이트거리점수","페이스점수","마령점수","배당급변점수","실패블랙점수","날씨주로특수점수","날씨주로메모","확신도","추천별점","확신등급","빨간경고","인기유형","위험요인"]], use_container_width=True)

with tabs[20]:
    st.subheader("🏃 경주 페이스 예상")
    st.markdown("""
선행마가 많으면 초반 과열 → 추입마 유리, 선행마가 적으면 선행마가 편하게 갈 가능성을 반영합니다.
""")
    st.dataframe(horses[[
        "경마장","경주번호","경주마","마번","주행습성","선행마수","선행선입수",
        "페이스예상","페이스유리","페이스점수","페이스메모","최종실전점수","최종판정"
    ]].sort_values(["경주번호","페이스점수"], ascending=[True,False]), use_container_width=True)

with tabs[21]:
    st.subheader("🎂 마령/나이 보정")
    st.markdown("""
보통 3~5세는 전성기, 8세 이상은 감점합니다. 장거리에서는 체력 영향이 더 큽니다.
""")
    st.dataframe(horses[["경주마","마번","마령","거리","마령점수","지구력점수","최종실전점수","최종판정"]].sort_values("마령점수", ascending=False), use_container_width=True)

with tabs[22]:
    st.subheader("📉 당일 배당 급변")
    st.markdown("""
출발 직전 인기 급상승은 시장 관심/내부 정보 가능성, 인기 급하락은 컨디션 이상 가능성으로 봅니다.
""")
    st.dataframe(horses[["경주마","마번","초기배당","현재배당","배당변화율","배당급변점수","배당급변메모","최종실전점수","최종판정"]].sort_values("배당급변점수", ascending=False), use_container_width=True)

with tabs[23]:
    st.subheader("🧭 코스별 통계")
    st.markdown("서울 1200m / 1400m / 1700m / 1800m처럼 코스별로 유리한 게이트와 성적을 따로 봅니다.")
    st.dataframe(course_stats(data), use_container_width=True)

with tabs[24]:
    st.subheader("🧱 실패 패턴 블랙리스트 / 자기학습")
    st.markdown("""
최근 100개 적중/실패 기록을 보고 반복 실패 요인을 다음 점수에 감점합니다.
""")
    st.dataframe(self_learning_summary(st.session_state.records), use_container_width=True)
    st.subheader("마필별 실패블랙 감점")
    st.dataframe(horses[["경주마","마번","거리","체중증감","기수승률","실패블랙점수","실패블랙메모","최종실전점수","최종판정"]].sort_values("실패블랙점수"), use_container_width=True)


with tabs[25]:
    st.subheader("🌦️ 날씨·주로 특수보정")
    st.markdown(f"""
### 현재 설정
- 날씨 조건: **{weather_type}**
- 모래/주로 특수상태: **{sand_status}**

### 반영 방식
- 비 오는 날: 선행·선입, 안쪽 게이트, 지구력형 보정
- 무더운 날: 체중 변화, 짧은 출전간격 감점 / 체력형 가산
- 추운 날: 초반스피드, 컨디션 보정
- 모래 새로교체: 기존 기록 신뢰도 일부 감점 / 파워·지구력형 가산
- 안쪽/바깥쪽 무거움: 게이트 위치별 감점·가산
""")
    st.dataframe(horses[[
        "경주마","마번","거리","주행습성","주로상태","현재배당",
        "날씨주로특수점수","날씨주로메모","최종실전점수","최종판정"
    ]].sort_values("날씨주로특수점수", ascending=False), use_container_width=True)


with tabs[26]:
    st.write("인기마 3마리 조합은 배당이 죽기 쉬워서 제거/주의합니다.")
    st.dataframe(horses[["경주마","마번","현재배당","인기순위","인기유형","인기마제거점수","최종실전점수","최종판정"]], use_container_width=True)
    if len(combos): st.dataframe(combos[["방식","1착","2착","3착","예상배당","인기마제거판정","조합점수","신뢰등급"]], use_container_width=True)

with tabs[27]:
    st.dataframe(combos, use_container_width=True)

with tabs[28]:
    hs=horses.groupby("경주마").agg(출전수=("경주마","count"),평균배당=("현재배당","mean"),평균점수=("최종실전점수","mean"),우승수=("순위", lambda x:int((pd.to_numeric(x, errors="coerce")==1).sum()))).reset_index()
    hs["우승률"]=(hs["우승수"]/hs["출전수"]*100).round(1)
    st.dataframe(hs.sort_values("평균점수", ascending=False), use_container_width=True)

with tabs[29]:
    js=horses.groupby("기수").agg(출전수=("기수","count"),평균승률=("기수승률","mean"),평균점수=("최종실전점수","mean"),우승수=("순위", lambda x:int((pd.to_numeric(x, errors="coerce")==1).sum()))).reset_index()
    st.dataframe(js.sort_values("평균점수", ascending=False), use_container_width=True)

with tabs[30]:
    ds=horses.groupby("거리").agg(출전수=("거리","count"),평균거리적성=("거리적성","mean"),평균점수=("최종실전점수","mean"),평균배당=("현재배당","mean")).reset_index()
    st.dataframe(ds, use_container_width=True)

with tabs[31]:
    ts=horses.groupby("주로상태").agg(출전수=("주로상태","count"),평균점수=("최종실전점수","mean"),평균배당=("현재배당","mean")).reset_index()
    st.dataframe(ts, use_container_width=True)

with tabs[32]:
    st.dataframe(pd.DataFrame([{"총투자":invested,"총회수":returned,"순수익":profit,"ROI":f"{roi}%"}]), use_container_width=True)

with tabs[33]:
    st.dataframe(factor_table(st.session_state.records, "적중"), use_container_width=True)

with tabs[34]:
    st.dataframe(factor_table(st.session_state.records, "실패"), use_container_width=True)

with tabs[35]:
    st.dataframe(data[["경마장","경주번호","출발시간","경주명","거리","경주마","마번","기수","현재배당"]].sort_values(["경주번호","마번"]), use_container_width=True)

with tabs[36]:
    if st.session_state.raw_tables:
        for i,t in enumerate(st.session_state.raw_tables,1):
            st.write(f"원본표 {i}")
            st.dataframe(t, use_container_width=True)
    else:
        st.info("KRA 원본 먼저 가져오기를 누르면 표시됩니다.")

with tabs[37]:
    st.write("CSV 업로드 시 권장 컬럼:")
    st.info("수동 CSV 업로드는 최후 백업입니다. 평소에는 Google Sheet 주소를 왼쪽에 넣어두면 자동으로 읽습니다.")
    st.code(", ".join(COLUMNS))
    up=st.file_uploader("CSV 업로드", type=["csv"])
    if up:
        st.session_state.df=pd.read_csv(up)
        st.success("CSV 업로드 완료")
        st.rerun()

with tabs[38]:
    st.subheader("🟩 Google Sheet 자동 백업")
    st.markdown("""
### 컴퓨터 꺼져 있어도 가능한 이유
- Streamlit 앱은 클라우드에서 실행됩니다.
- Google Sheet는 인터넷 주소로 읽습니다.
- 형님 컴퓨터가 꺼져 있어도 휴대폰에서 앱을 열면 데이터 읽기가 가능합니다.

### 구글시트 연결 방법
1. Google Sheet 만들기
2. 첫 줄에 컬럼명 입력
3. `파일 → 공유 → 웹에 게시` 또는 `링크가 있는 사용자 보기 가능`
4. CSV 주소 또는 일반 시트 주소를 앱 왼쪽 `Google Sheet CSV 주소`에 입력
5. 앱을 새로고침하면 자동 분석

### 권장 컬럼
""")
    st.code(", ".join(COLUMNS))
    st.markdown("""
### 자동 순서
기본값은 아래 순서입니다.

```text
KRA 홈페이지
→ 실패하면 Google Sheet
→ 실패하면 GitHub CSV
→ 실패하면 샘플/수동 CSV
```

Google Sheet를 1순위로 쓰고 싶으면 왼쪽 `데이터 우선순위`에서 바꾸면 됩니다.
""")
    if google_sheet_url:
        st.success("Google Sheet 주소가 입력되어 있습니다.")
        st.code(normalize_sheet_url(google_sheet_url))
    else:
        st.info("왼쪽 설정에 Google Sheet 주소를 넣으면 자동 백업 데이터로 읽습니다.")


with tabs[39]:
    st.markdown("""
### 자동 분석 구조
앱 실행 → KRA 원본표 자동 가져오기 → 자동 분석 → 30배 후보 자동 계산

### 최종 분석 구조
KRA 원본표 → 시간표/출마표 → 최근5경기 흐름 → 체중 변화 → 기수 교체 → 출전 간격 → 거리 적성 → 게이트/마번 → 인기마 제거 → 30배 조합 → A/B/C/D 판정

### 점수 구조
핵심점수 60% + 기수 10% + 거리 10% + 체중 5% + 주로 5% + ROI 5% + 최근 상승세 5%

### 인기마 제거 엔진
1위 인기마 + 2위 인기마 + 3위 인기마 조합은 배당이 낮아질 수 있어 주의합니다.  
강한 인기마 1마리 + 중간 인기마 1마리 + 복병 1마리 구조를 우선 확인합니다.

자동구매는 없고, 공식 페이지에서 직접 확인 후 수동구매합니다.
""")

st.warning("예상배당은 공식 확정배당이 아니라 내부 계산입니다. 적중이나 수익을 보장하지 않습니다. 자동구매 기능은 없습니다.")
