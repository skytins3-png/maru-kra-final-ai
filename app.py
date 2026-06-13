
import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from collections import Counter
import random, json

try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except Exception:
    HAS_AUTOREFRESH = False

st.set_page_config(page_title="MARU KRA 3SHOT PROFIT GUARD", page_icon="🐎", layout="centered")

DATA_DIR = Path("maru_kra_data")
DATA_DIR.mkdir(exist_ok=True)
RESULT_FILE = DATA_DIR / "race_result_records.csv"
RECO_FILE = DATA_DIR / "recommendation_bigdata_log.csv"
COMPARE_FILE = DATA_DIR / "prediction_result_compare_log.csv"
WEIGHT_FILE = DATA_DIR / "learning_weights.json"

DEFAULT_WEIGHTS = {
    "recent": 2.2, "win_rate": 0.45, "place_rate": 0.30, "rating": 0.55,
    "rating_delta": 1.8, "odds_value": 1.0, "environment": 1.0,
    "weight_penalty": 1.4, "risk_penalty": 1.0
}

def load_weights():
    if WEIGHT_FILE.exists():
        try:
            return json.loads(WEIGHT_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    WEIGHT_FILE.write_text(json.dumps(DEFAULT_WEIGHTS, ensure_ascii=False, indent=2), encoding="utf-8")
    return DEFAULT_WEIGHTS.copy()

def save_weights(w):
    WEIGHT_FILE.write_text(json.dumps(w, ensure_ascii=False, indent=2), encoding="utf-8")

def read_table(path):
    if path.exists():
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def today():
    return datetime.now().strftime("%Y-%m-%d")

st.sidebar.title("3SHOT PROFIT GUARD")
api_key = st.sidebar.text_input("공공데이터 API Key", type="password")
st.sidebar.caption("{serviceKey}, {today} 자리 자동 치환")

race_url = st.sidebar.text_area("경주정보 API URL", height=55)
horse_url = st.sidebar.text_area("경주마정보 API URL", height=55)
rating_url = st.sidebar.text_area("레이팅정보 API URL", height=55)
odds_url = st.sidebar.text_area("배당/매출 API URL", height=55)
risk_url = st.sidebar.text_area("심판/위험 API URL", height=55)

st.sidebar.markdown("---")
track_place = st.sidebar.selectbox("경마장", ["서울", "부산경남", "제주"])
auto_weather = st.sidebar.checkbox("날씨/바람 자동수집", True)
auto_track = st.sidebar.checkbox("주로/모래 자동추정", True)
manual_weather = st.sidebar.selectbox("날씨 보정", ["자동", "맑음", "흐림", "비", "눈"])
manual_track = st.sidebar.selectbox("주로 보정", ["자동", "건조", "양호", "다습", "포화", "불량"])
manual_sand = st.sidebar.selectbox("모래 보정", ["자동", "가벼움", "보통", "무거움"])
manual_wind = st.sidebar.selectbox("바람 보정", ["자동", "없음", "뒷바람", "맞바람", "측풍"])
distance_type = st.sidebar.selectbox("거리 성향", ["단거리", "중거리", "장거리"], index=1)

st.sidebar.markdown("---")
sim_count = st.sidebar.selectbox("시뮬레이션", [50, 100, 300, 500, 1000], index=2)
risk_mode = st.sidebar.selectbox("위험 성향", ["안전형", "균형형", "공격형"])
bankroll = st.sidebar.number_input("운영잔고", min_value=0, max_value=10000000, value=100000, step=10000)
unit_bet = st.sidebar.number_input("20만원 전 1회 기준금액", min_value=100, max_value=10000, value=1000, step=100)
daily_loss_limit = st.sidebar.number_input("하루 손실 투자금지", min_value=10000, max_value=300000, value=30000, step=1000)
profit_unlock = st.sidebar.number_input("3만원 운영 허용 기준", min_value=50000, max_value=1000000, value=200000, step=10000)
daily_budget = st.sidebar.number_input("허용 후 하루 투자한도", min_value=10000, max_value=100000, value=30000, step=1000)
daily_entries_limit = st.sidebar.number_input("하루 최대 진입", min_value=1, max_value=10, value=3)
auto_save_reco = st.sidebar.checkbox("추천 자동저장", True)
use_sample = st.sidebar.checkbox("데이터 없으면 샘플 사용", True)
kra_url = st.sidebar.text_input("KRA 공식 바로가기", "https://m.kra.co.kr/main.do")

st.sidebar.markdown("---")
race_csv = st.sidebar.file_uploader("경주정보 CSV", type=["csv"])
horse_csv = st.sidebar.file_uploader("경주마정보 CSV", type=["csv"])
rating_csv = st.sidebar.file_uploader("레이팅 CSV", type=["csv"])
odds_csv = st.sidebar.file_uploader("배당 CSV", type=["csv"])
risk_csv = st.sidebar.file_uploader("위험 CSV", type=["csv"])

st.markdown("""
<style>
.block-container{max-width:760px;padding-top:1rem}
.logo{font-size:36px;font-weight:1000;color:#0f172a}.ai{font-size:16px;background:#2563eb;color:white;border-radius:8px;padding:4px 8px}.sub{font-size:17px;color:#0f766e;font-weight:900}
.status{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:12px 0}.stat{background:#f8fafc;border:1px solid #e2e8f0;border-radius:14px;padding:10px;text-align:center}.stat b{color:#0f766e}
.main{background:radial-gradient(circle at 78% 8%,#0f766e,#064e3b 40%,#022c22);color:white;border-radius:28px;padding:26px;margin:18px 0;box-shadow:0 12px 30px rgba(2,44,34,.22)}
.badge{display:inline-block;background:#16a34a;color:white;padding:9px 16px;border-radius:12px;font-size:20px;font-weight:1000}.wait{background:#64748b}.stop{background:#dc2626}.time{float:right;font-size:18px;font-weight:900}.race{font-size:22px;margin-top:25px;color:#ecfdf5}.combo{font-size:43px;font-weight:1000;margin-top:14px}.odds{font-size:34px;color:#facc15;font-weight:1000;text-align:right}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.mini{background:white;border:1px solid #e5e7eb;border-radius:18px;padding:14px 7px;text-align:center;box-shadow:0 4px 14px rgba(15,23,42,.08)}.mini .label{font-size:14px;font-weight:900}.mini .value{font-size:22px;color:#047857;font-weight:1000}
.box{background:white;border:1px solid #e5e7eb;border-radius:20px;padding:17px;margin:13px 0;box-shadow:0 4px 14px rgba(15,23,42,.06)}
.env{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.env div{background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:9px;text-align:center}
.stButton>button{background:#0b5cff;color:white;font-size:19px;font-weight:1000;border-radius:18px;height:58px}.note{text-align:center;color:#64748b;font-size:14px}
@media(max-width:700px){.combo{font-size:33px}.odds{font-size:28px}.mini .value{font-size:19px}.env{font-size:12px}}
</style>
""", unsafe_allow_html=True)

def sample_race():
    return pd.DataFrame([{"경마장":track_place,"경주번호":"6","출발시간":"16:05","거리":1400}])

def sample_horse():
    return pd.DataFrame([
        {"마번":5,"마명":"마루스피드","최근순위":2,"승률":18,"복승률":42,"부담중량":55,"예상배당":9.2,"선행력":82,"추입력":70,"파워":78,"순발력":84,"습주로":72,"모래적응":80},
        {"마번":11,"마명":"그린파워","최근순위":3,"승률":15,"복승률":38,"부담중량":54.5,"예상배당":7.8,"선행력":75,"추입력":78,"파워":82,"순발력":77,"습주로":80,"모래적응":83},
        {"마번":2,"마명":"블루런","최근순위":4,"승률":12,"복승률":35,"부담중량":53,"예상배당":12.5,"선행력":70,"추입력":83,"파워":76,"순발력":79,"습주로":84,"모래적응":75},
        {"마번":7,"마명":"라스트킹","최근순위":5,"승률":10,"복승률":30,"부담중량":55.5,"예상배당":15.4,"선행력":68,"추입력":72,"파워":85,"순발력":69,"습주로":86,"모래적응":88},
        {"마번":3,"마명":"해피로드","최근순위":6,"승률":8,"복승률":25,"부담중량":56,"예상배당":22,"선행력":65,"추입력":74,"파워":70,"순발력":73,"습주로":68,"모래적응":71}
    ])

def sample_rating():
    return pd.DataFrame([{"마번":5,"레이팅":78,"레이팅변화":4},{"마번":11,"레이팅":75,"레이팅변화":2},{"마번":2,"레이팅":72,"레이팅변화":3},{"마번":7,"레이팅":70,"레이팅변화":-1},{"마번":3,"레이팅":66,"레이팅변화":1}])

def sample_odds():
    return pd.DataFrame([{"마번":5,"단승배당":9.2,"매출쏠림":18},{"마번":11,"단승배당":7.8,"매출쏠림":22},{"마번":2,"단승배당":12.5,"매출쏠림":10},{"마번":7,"단승배당":15.4,"매출쏠림":8},{"마번":3,"단승배당":22,"매출쏠림":4}])

def sample_risk():
    return pd.DataFrame([{"마번":5,"출발위험":0,"주행위험":1},{"마번":11,"출발위험":1,"주행위험":0},{"마번":2,"출발위험":0,"주행위험":0},{"마번":7,"출발위험":1,"주행위험":1},{"마번":3,"출발위험":2,"주행위험":1}])

COORDS = {"서울":(37.4438,127.0165), "부산경남":(35.1545,128.8782), "제주":(33.4097,126.3934)}

def fetch_env():
    env = {"weather":"맑음","wind":"없음","track":"양호","sand":"보통","source":"기본","precip":0,"wind_speed":0}
    if auto_weather:
        lat, lon = COORDS.get(track_place, COORDS["서울"])
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation,weather_code,wind_speed_10m&timezone=Asia%2FSeoul"
        try:
            cur = requests.get(url, timeout=10).json().get("current", {})
            precip = float(cur.get("precipitation", 0) or 0)
            wind_speed = float(cur.get("wind_speed_10m", 0) or 0)
            code = int(cur.get("weather_code", 0) or 0)
            weather = "비" if precip >= 0.3 or code in [51,53,55,61,63,65,80,81,82,95,96,99] else ("흐림" if code in [1,2,3,45,48] else "맑음")
            if code in [71,73,75,77,85,86]:
                weather = "눈"
            wind = "없음" if wind_speed < 2 else ("측풍" if wind_speed < 5 else "맞바람")
            if weather in ["비","눈"] and precip >= 3:
                track, sand = "포화", "무거움"
            elif weather in ["비","눈"] and precip >= 1:
                track, sand = "다습", "무거움"
            elif weather in ["비","눈"]:
                track, sand = "다습", "보통"
            else:
                track, sand = "양호", "보통"
            env = {"weather":weather,"wind":wind,"track":track if auto_track else "양호","sand":sand if auto_track else "보통","source":"자동수집","precip":precip,"wind_speed":wind_speed}
        except Exception as e:
            env["source"] = "자동실패"
            env["error"] = str(e)
    if manual_weather != "자동": env["weather"] = manual_weather
    if manual_track != "자동": env["track"] = manual_track
    if manual_sand != "자동": env["sand"] = manual_sand
    if manual_wind != "자동": env["wind"] = manual_wind
    return env

def replace_url(url):
    return url.replace("{serviceKey}", api_key.strip()).replace("{today}", datetime.now().strftime("%Y%m%d"))

def json_to_df(obj):
    if isinstance(obj, dict):
        for path in [["response","body","items","item"],["response","body","item"],["items","item"],["data"],["result"]]:
            cur = obj; ok = True
            for p in path:
                if isinstance(cur, dict) and p in cur:
                    cur = cur[p]
                else:
                    ok = False; break
            if ok:
                obj = cur; break
    if isinstance(obj, dict):
        obj = [obj]
    return pd.json_normalize(obj)

def xml_to_df(text):
    root = ET.fromstring(text)
    rows = []
    for item in root.findall(".//item"):
        rows.append({c.tag:c.text for c in item})
    return pd.DataFrame(rows)

def fetch_url(url):
    if not url.strip():
        return pd.DataFrame(), "URL 미입력"
    if "{serviceKey}" in url and not api_key.strip():
        return pd.DataFrame(), "API Key 미입력"
    try:
        r = requests.get(replace_url(url), timeout=15)
        if r.status_code != 200:
            return pd.DataFrame(), f"HTTP {r.status_code}"
        txt = r.text.strip()
        if txt.startswith("{") or txt.startswith("[") or "json" in r.headers.get("content-type",""):
            return json_to_df(r.json()), ""
        return xml_to_df(txt), ""
    except Exception as e:
        return pd.DataFrame(), str(e)

def read_csv(file):
    if file is None:
        return pd.DataFrame()
    return pd.read_csv(file)

def load_one(file, url, sample_func):
    df = read_csv(file)
    err = ""
    if df.empty and url.strip():
        df, err = fetch_url(url)
    if df.empty and use_sample:
        df = sample_func()
    return df, err

def load_all():
    env = fetch_env()
    st.session_state.env = env
    errors = []
    for key, name, file, url, sample in [
        ("race_df","경주정보",race_csv,race_url,sample_race),
        ("horse_df","경주마",horse_csv,horse_url,sample_horse),
        ("rating_df","레이팅",rating_csv,rating_url,sample_rating),
        ("odds_df","배당",odds_csv,odds_url,sample_odds),
        ("risk_df","위험",risk_csv,risk_url,sample_risk)
    ]:
        df, err = load_one(file, url, sample)
        st.session_state[key] = df
        if err and err != "URL 미입력":
            errors.append(f"{name}:{err}")
    rows = sum(len(st.session_state[k]) for k in ["race_df","horse_df","rating_df","odds_df","risk_df"])
    st.session_state.status = "분석가능" if rows > 0 and not errors else ("일부연결" if rows > 0 else "데이터 없음")
    st.session_state.error = " / ".join(errors)

def col_pick(df, names):
    for n in names:
        if n in df.columns:
            return n
    return None

def num_series(df, names, default):
    c = col_pick(df, names)
    if c:
        return pd.to_numeric(df[c], errors="coerce").fillna(default)
    return pd.Series([default] * len(df), index=df.index)

def merge_h(left, right):
    if right.empty:
        return left
    r = right.copy()
    c = col_pick(r, ["마번","horseNo","hrNo","번호"])
    if not c:
        return left
    r["마번"] = pd.to_numeric(r[c], errors="coerce").fillna(0).astype(int)
    return left.merge(r, on="마번", how="left", suffixes=("","_추가"))

def env_bonus(row):
    env = st.session_state.env or {}
    weather, track, sand, wind = env.get("weather","맑음"), env.get("track","양호"), env.get("sand","보통"), env.get("wind","없음")
    front, late, power, speed, wet, sandfit = [float(row.get(c,70)) for c in ["선행력","추입력","파워","순발력","습주로","모래적응"]]
    b = 0
    if weather in ["비","눈"] or track in ["다습","포화","불량"]:
        b += (wet-70)*.13 + (power-70)*.08
    else:
        b += (speed-70)*.10 + (front-70)*.06
    if sand == "무거움":
        b += (sandfit-70)*.12 + (power-70)*.08
    elif sand == "가벼움":
        b += (speed-70)*.12
    else:
        b += (sandfit-70)*.05
    if wind == "맞바람":
        b += (late-70)*.07 - (front-75)*.04
    elif wind == "뒷바람":
        b += (front-70)*.07 + (speed-70)*.05
    elif wind == "측풍":
        b -= 1
    if distance_type == "단거리":
        b += (speed-70)*.09 + (front-70)*.08
    elif distance_type == "장거리":
        b += (power-70)*.08 + (late-70)*.07
    else:
        b += ((speed+power)/2-70)*.05
    return round(b, 1)

def budget_status():
    df = read_table(RESULT_FILE)
    if df.empty:
        return {"today_bet":0,"today_return":0,"today_profit":0,"total_profit":0,"entries":0,"locked":False,"reason":"정상"}
    if "저장시각" in df.columns:
        df["날짜"] = pd.to_datetime(df["저장시각"], errors="coerce").dt.strftime("%Y-%m-%d")
    else:
        df["날짜"] = ""
    for c in ["투입금","환급금"]:
        if c not in df.columns:
            df[c] = 0
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    tdf = df[df["날짜"] == today()]
    today_bet = float(tdf["투입금"].sum())
    today_return = float(tdf["환급금"].sum())
    today_profit = today_return - today_bet
    total_profit = float(df["환급금"].sum() - df["투입금"].sum())
    entries = int((tdf["투입금"] > 0).sum())
    locked = False
    reason = "정상"
    if today_profit <= -float(daily_loss_limit):
        locked = True
        reason = f"하루 손실 {int(daily_loss_limit):,}원 도달"
    elif entries >= int(daily_entries_limit):
        locked = True
        reason = f"하루 {int(daily_entries_limit)}회 완료"
    elif today_bet >= float(daily_budget):
        locked = True
        reason = f"하루 {int(daily_budget):,}원 한도 도달"
    return {"today_bet":today_bet,"today_return":today_return,"today_profit":today_profit,"total_profit":total_profit,"entries":entries,"locked":locked,"reason":reason}

def build_analysis():
    h = st.session_state.horse_df.copy()
    if h.empty:
        return pd.DataFrame(), {}, []
    c = col_pick(h, ["마번","horseNo","hrNo","번호"])
    h["마번"] = pd.to_numeric(h[c], errors="coerce").fillna(0).astype(int) if c else range(1, len(h)+1)
    h = merge_h(h, st.session_state.rating_df)
    h = merge_h(h, st.session_state.odds_df)
    h = merge_h(h, st.session_state.risk_df)
    for col in ["선행력","추입력","파워","순발력","습주로","모래적응"]:
        if col not in h.columns:
            h[col] = 70
    w = load_weights()
    recent = num_series(h, ["최근순위","최근성적","rank","ord"], 5)
    win = num_series(h, ["승률","winRate"], 10)
    place = num_series(h, ["복승률","placeRate"], 25)
    rating = num_series(h, ["레이팅","rating"], 65)
    delta = num_series(h, ["레이팅변화","ratingDelta"], 0)
    weight = num_series(h, ["부담중량","weight"], 55)
    odds = num_series(h, ["예상배당","배당","odds","winOdds","단승배당"], 12)
    crowd = num_series(h, ["매출쏠림","쏠림","인기쏠림"], 10)
    srisk = num_series(h, ["출발위험","startRisk"], 0)
    rrisk = num_series(h, ["주행위험","runRisk"], 0)
    h["환경보정"] = h.apply(env_bonus, axis=1)
    h["최근점수"] = (10-recent.clip(1,10))*w["recent"]
    h["승률점수"] = win.clip(0,50)*w["win_rate"]
    h["복승점수"] = place.clip(0,80)*w["place_rate"]
    h["레이팅점수"] = (rating.clip(40,100)-40)*w["rating"]
    h["상승점수"] = delta.clip(-10,10)*w["rating_delta"]
    h["배당가치"] = odds.clip(1,100).apply(lambda x:12 if 6<=x<=25 else (7 if 25<x<=45 else (3 if 3<=x<6 else 1)))*w["odds_value"]
    h["중량감점"] = (weight-54).clip(lower=0)*w["weight_penalty"]
    h["위험감점"] = (srisk*2 + rrisk*1.5)*w["risk_penalty"]
    h["인기과열감점"] = crowd.clip(0,100).apply(lambda x:5 if x>=35 else (2 if x>=25 else 0))
    h["최종점수"] = (h["최근점수"]+h["승률점수"]+h["복승점수"]+h["레이팅점수"]+h["상승점수"]+h["배당가치"]+h["환경보정"]*w["environment"]-h["중량감점"]-h["위험감점"]-h["인기과열감점"]).round(1)

    env = st.session_state.env or {}
    vol = 5.5
    if env.get("weather") in ["비","눈"] or env.get("track") in ["포화","불량"]:
        vol = 7.2
    if env.get("wind") in ["맞바람","측풍"]:
        vol += .8
    if env.get("sand") == "무거움":
        vol += .7
    vol *= .9 if risk_mode == "안전형" else (1.15 if risk_mode == "공격형" else 1)

    counter = Counter()
    random.seed(42)
    nums = h["마번"].tolist()
    scores = h["최종점수"].tolist()
    for _ in range(sim_count):
        noisy = [(no, sc + random.gauss(0, vol)) for no, sc in zip(nums, scores)]
        top3 = tuple(str(x[0]) for x in sorted(noisy, key=lambda x:x[1], reverse=True)[:3])
        if len(top3) == 3:
            counter[top3] += 1
    combos = counter.most_common(10)
    top = combos[0][0] if combos else tuple(str(x) for x in nums[:3])
    conf = min(95, max(35, round((combos[0][1] if combos else 0)/max(sim_count,1)*100 + 48)))
    top_rows = h[h["마번"].astype(str).isin(list(top))]
    avg_risk = float(top_rows["위험감점"].mean()) if not top_rows.empty else 0
    avg_over = float(top_rows["인기과열감점"].mean()) if not top_rows.empty else 0
    min_attack, min_entry = (78,66) if risk_mode=="안전형" else ((70,58) if risk_mode=="공격형" else (75,62))
    if conf >= min_attack and avg_risk <= 3.5 and avg_over <= 3:
        decision = "소액 공격"
    elif conf >= min_entry and avg_risk <= 5:
        decision = "소액 가능"
    else:
        decision = "관망"

    b = budget_status()
    unlocked = b["total_profit"] >= float(profit_unlock) or bankroll >= float(profit_unlock)
    remaining_budget = max(0, float(daily_budget) - b["today_bet"])
    remaining_entries = max(0, int(daily_entries_limit) - b["entries"])
    if b["locked"] or remaining_budget <= 0 or remaining_entries <= 0:
        decision = "투자금지"
        amount = 0
    elif decision == "관망":
        amount = 0
    else:
        if unlocked:
            amount = min(10000, remaining_budget)
        else:
            amount = min(unit_bet, remaining_budget)
        amount = int(amount)

    race = st.session_state.race_df.iloc[0].to_dict() if not st.session_state.race_df.empty else {}
    result = {
        "경마장": race.get("경마장", track_place),
        "경주번호": race.get("경주번호", "-"),
        "출발시간": race.get("출발시간", "-"),
        "판정": decision,
        "공격삼쌍승": " - ".join(top),
        "방어삼복승": " / ".join(top),
        "보조삼쌍승": " - ".join(combos[1][0]) if len(combos)>1 else " - ".join(top),
        "놓치기아까운1": " - ".join(combos[2][0]) if len(combos)>2 else "",
        "놓치기아까운2": " - ".join(combos[3][0]) if len(combos)>3 else "",
        "예상배당": round(float(odds.head(3).sum()*0.9), 1) if len(odds)>=3 else 46.8,
        "신뢰도": conf,
        "추천금액": amount,
        "평균위험": round(avg_risk, 1),
        "오늘투입": int(b["today_bet"]),
        "오늘손익": int(b["today_profit"]),
        "누적손익": int(b["total_profit"]),
        "오늘진입": int(b["entries"]),
        "자금상태": b["reason"]
    }
    combo_rows = [{"조합":" - ".join(k),"반복횟수":v,"비율":round(v/max(sim_count,1)*100,1)} for k,v in combos]
    return h.sort_values("최종점수", ascending=False), result, combo_rows

def append_recommendation(result, env):
    df = read_table(RECO_FILE)
    rec = {
        "저장시각":datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "날짜":today(),
        "경마장":result["경마장"], "경주번호":result["경주번호"], "출발시간":result["출발시간"],
        "판정":result["판정"], "공격삼쌍승":result["공격삼쌍승"], "방어삼복승":result["방어삼복승"],
        "보조삼쌍승":result["보조삼쌍승"], "놓치기아까운1":result["놓치기아까운1"], "놓치기아까운2":result["놓치기아까운2"],
        "예상배당":result["예상배당"], "신뢰도":result["신뢰도"], "추천금액":result["추천금액"],
        "오늘투입":result["오늘투입"], "오늘손익":result["오늘손익"], "누적손익":result["누적손익"],
        "날씨":env.get("weather",""), "주로":env.get("track",""), "모래":env.get("sand",""), "바람":env.get("wind","")
    }
    rec["추천키"] = f'{rec["날짜"]}_{rec["경마장"]}_{rec["경주번호"]}_{rec["공격삼쌍승"]}_{rec["판정"]}'
    if "추천키" in df.columns and rec["추천키"] in set(df["추천키"].astype(str)):
        return df
    df = pd.concat([df, pd.DataFrame([rec])], ignore_index=True)
    df.to_csv(RECO_FILE, index=False, encoding="utf-8-sig")
    return df

def append_result(rec):
    df = read_table(RESULT_FILE)
    df = pd.concat([df, pd.DataFrame([rec])], ignore_index=True)
    df.to_csv(RESULT_FILE, index=False, encoding="utf-8-sig")
    return df

def update_learning(records):
    w = load_weights()
    if len(records) < 3:
        return w, "기록 3개 이상부터 자가학습 보정 시작"
    r = records.tail(20)
    roi = pd.to_numeric(r.get("수익률", 0), errors="coerce").fillna(0).mean()
    hit = pd.to_numeric(r.get("적중", 0), errors="coerce").fillna(0).mean()
    if roi > 0 and hit >= .25:
        w["environment"] = min(1.8, w["environment"] + .03)
        w["rating_delta"] = min(2.6, w["rating_delta"] + .02)
        msg = "수익 구간: 환경/상승세 가중치 강화"
    elif roi < -.2:
        w["risk_penalty"] = min(2.5, w["risk_penalty"] + .05)
        w["odds_value"] = max(.6, w["odds_value"] - .03)
        msg = "손실 구간: 위험감점 강화, 배당 과신 감소"
    else:
        w["place_rate"] = min(.5, w["place_rate"] + .01)
        msg = "보통 구간: 삼복승 방어 성향 강화"
    save_weights(w)
    return w, msg


def normalize_combo_text(x):
    return str(x).replace(" ", "").replace("/", "-").replace(",", "-")

def analyze_prediction_error(pred, actual_combo, actual_trio, bet_amount, return_amount):
    pred_main = normalize_combo_text(pred.get("공격삼쌍승", ""))
    pred_assist = normalize_combo_text(pred.get("보조삼쌍승", ""))
    pred_miss1 = normalize_combo_text(pred.get("놓치기아까운1", ""))
    pred_miss2 = normalize_combo_text(pred.get("놓치기아까운2", ""))
    pred_trio_set = set(normalize_combo_text(pred.get("방어삼복승", "")).split("-"))
    actual_combo_norm = normalize_combo_text(actual_combo)
    actual_trio_set = set(normalize_combo_text(actual_trio if actual_trio else actual_combo).split("-"))

    trifecta_hit = actual_combo_norm in [pred_main, pred_assist, pred_miss1, pred_miss2]
    trio_hit = len(pred_trio_set) == 3 and pred_trio_set == actual_trio_set
    paid = return_amount > 0

    if trifecta_hit:
        result_type = "삼쌍승 적중"
        cause = "순서 예측 성공"
        learn = "현재 조합 순서 가중치 유지 또는 강화"
    elif trio_hit:
        result_type = "삼복승 방어 적중"
        cause = "말 3마리는 맞았지만 순서가 다름"
        learn = "삼복승 방어는 유지, 순서 뒤집힘 패턴 학습 강화"
    elif paid:
        result_type = "부분 환급"
        cause = "추천 외 보조/방어 또는 기타 환급 발생"
        learn = "환급 조합을 별도 기록해 유사조건에서 보조 후보 강화"
    else:
        result_type = "미적중"
        cause_parts = []
        if pred.get("판정") in ["소액 공격", "소액 가능"] and pred.get("신뢰도", 0) < 70:
            cause_parts.append("신뢰도 기준 부족")
        if pred.get("평균위험", 0) >= 4:
            cause_parts.append("출발/주행 위험 과소평가")
        if pred.get("오늘손익", 0) < 0:
            cause_parts.append("손실 구간에서 진입")
        if not cause_parts:
            cause_parts.append("순서 변동 또는 복병 미포착")
        cause = ", ".join(cause_parts)
        learn = "위험감점/복병/순서변동 가중치 보정"

    roi = ((return_amount - bet_amount) / bet_amount) if bet_amount > 0 else 0
    return {
        "분석결과": result_type,
        "틀린이유_또는_맞은이유": cause,
        "학습방향": learn,
        "삼쌍적중": 1 if trifecta_hit else 0,
        "삼복방어": 1 if trio_hit else 0,
        "수익률": roi
    }

def append_compare_log(pred, actual_combo, actual_trio, bet_amount, return_amount, memo, env):
    analysis = analyze_prediction_error(pred, actual_combo, actual_trio, bet_amount, return_amount)
    df = read_table(COMPARE_FILE)
    rec = {
        "저장시각": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "날짜": today(),
        "경마장": pred.get("경마장",""),
        "경주번호": pred.get("경주번호",""),
        "출발시간": pred.get("출발시간",""),
        "판정": pred.get("판정",""),
        "신뢰도": pred.get("신뢰도",0),
        "예상배당": pred.get("예상배당",0),
        "예상_공격삼쌍": pred.get("공격삼쌍승",""),
        "예상_방어삼복": pred.get("방어삼복승",""),
        "예상_보조삼쌍": pred.get("보조삼쌍승",""),
        "예상_놓치기1": pred.get("놓치기아까운1",""),
        "예상_놓치기2": pred.get("놓치기아까운2",""),
        "실제삼쌍": actual_combo,
        "실제삼복": actual_trio,
        "투입금": bet_amount,
        "환급금": return_amount,
        "날씨": env.get("weather",""),
        "주로": env.get("track",""),
        "모래": env.get("sand",""),
        "바람": env.get("wind",""),
        "메모": memo,
        **analysis
    }
    df = pd.concat([df, pd.DataFrame([rec])], ignore_index=True)
    df.to_csv(COMPARE_FILE, index=False, encoding="utf-8-sig")
    return df, analysis

def race_by_race_summary():
    reco = read_table(RECO_FILE)
    comp = read_table(COMPARE_FILE)
    if reco.empty:
        return {"오늘예상": 0, "오늘비교": 0, "미비교": 0, "삼쌍적중": 0, "삼복방어": 0}
    if "날짜" in reco.columns:
        today_reco = reco[reco["날짜"].astype(str) == today()]
    else:
        today_reco = reco
    if comp.empty or "날짜" not in comp.columns:
        today_comp = pd.DataFrame()
    else:
        today_comp = comp[comp["날짜"].astype(str) == today()]
    return {
        "오늘예상": len(today_reco),
        "오늘비교": len(today_comp),
        "미비교": max(0, len(today_reco) - len(today_comp)),
        "삼쌍적중": int(pd.to_numeric(today_comp.get("삼쌍적중", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()) if not today_comp.empty else 0,
        "삼복방어": int(pd.to_numeric(today_comp.get("삼복방어", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()) if not today_comp.empty else 0
    }

def update_learning_from_compare(compare_df):
    w = load_weights()
    if compare_df.empty or len(compare_df) < 3:
        return w, "비교 기록 3개 이상부터 오답학습이 강화됩니다."
    recent = compare_df.tail(20)
    miss_rate = 1 - pd.to_numeric(recent.get("삼쌍적중", 0), errors="coerce").fillna(0).mean()
    trio_rate = pd.to_numeric(recent.get("삼복방어", 0), errors="coerce").fillna(0).mean()
    roi = pd.to_numeric(recent.get("수익률", 0), errors="coerce").fillna(0).mean()

    if roi < -0.2 and miss_rate > 0.7:
        w["risk_penalty"] = min(3.0, w["risk_penalty"] + 0.08)
        w["odds_value"] = max(0.55, w["odds_value"] - 0.04)
        msg = "오답학습: 손실/미적중 많음 → 위험감점 강화, 배당 과신 축소"
    elif trio_rate >= 0.35 and miss_rate > 0.5:
        w["place_rate"] = min(0.65, w["place_rate"] + 0.03)
        w["environment"] = min(1.9, w["environment"] + 0.02)
        msg = "오답학습: 말 3마리는 맞고 순서가 틀림 → 삼복 방어/순서변동 학습 강화"
    elif roi > 0:
        w["rating_delta"] = min(2.8, w["rating_delta"] + 0.03)
        w["environment"] = min(1.9, w["environment"] + 0.03)
        msg = "오답학습: 수익 구간 → 상승세/환경 가중치 강화"
    else:
        w["place_rate"] = min(0.6, w["place_rate"] + 0.01)
        msg = "오답학습: 보통 → 방어 성향 소폭 강화"
    save_weights(w)
    return w, msg


st.markdown('<div class="logo">MARU KRA <span class="ai">AI</span></div><div class="sub">RACE-BY-RACE 3SHOT LEARNING ENGINE</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)
if c1.button("데이터/환경 새로고침", use_container_width=True):
    load_all(); st.rerun()
if c2.button("시뮬레이션 실행", use_container_width=True):
    load_all(); st.rerun()

if use_sample and "horse_df" not in st.session_state or st.session_state.horse_df.empty:
    load_all()

rows = sum(len(st.session_state[k]) for k in ["race_df","horse_df","rating_df","odds_df","risk_df"])
reco_df = read_table(RECO_FILE)
result_df = read_table(RESULT_FILE)
rbs = race_by_race_summary()
st.markdown(f'<div class="status"><div class="stat">오늘 예상<br><b>{rbs["오늘예상"]}</b></div><div class="stat">비교/미비교<br><b>{rbs["오늘비교"]} / {rbs["미비교"]}</b></div><div class="stat">삼쌍/삼복<br><b>{rbs["삼쌍적중"]} / {rbs["삼복방어"]}</b></div></div>', unsafe_allow_html=True)
if st.session_state.error:
    st.warning(st.session_state.error)

score_df, result, combos = build_analysis()
env = st.session_state.env or {}
if auto_save_reco:
    append_recommendation(result, env)

badge = "badge stop" if result["판정"] == "투자금지" else ("badge wait" if result["판정"] == "관망" else "badge")
st.markdown(f"""
<div class="main">
  <div style="font-size:22px;font-weight:1000;margin-bottom:23px;">하루 3만원 · 3번 진입 · 빅데이터 자가학습</div>
  <span class="{badge}">{result['판정']}</span><span class="time">{sim_count}회</span>
  <div class="race">{result['경마장']} {result['경주번호']}R · 출발 {result['출발시간']}</div>
  <div style="margin-top:18px;color:#d1fae5;font-size:18px;">공격 삼쌍승</div>
  <div class="combo">{result['공격삼쌍승']}</div>
  <div class="odds">{result['예상배당']}배</div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="grid">
  <div class="mini"><div class="label">신뢰도</div><div class="value">{result['신뢰도']}%</div></div>
  <div class="mini"><div class="label">추천금액</div><div class="value">{result['추천금액']:,}원</div></div>
  <div class="mini"><div class="label">오늘진입</div><div class="value">{result['오늘진입']} / {int(daily_entries_limit)}</div></div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="box"><b style="font-size:21px;">자금 잠금 규칙</b><br><br>
오늘 투입: <b>{result['오늘투입']:,}원 / {int(daily_budget):,}원</b><br>
오늘 손익: <b>{result['오늘손익']:,}원</b><br>
누적 손익: <b>{result['누적손익']:,}원</b><br>
상태: <b>{result['자금상태']}</b><br>
<span class="note">하루 손실 -{int(daily_loss_limit):,}원 도달 시 투자금지 · 20만원 이상이면 하루 3만원 운영</span>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="box"><b style="font-size:21px;">매경주 예측·결과비교·오답학습</b><br><br>
오늘 예상 저장: <b>{rbs['오늘예상']}경주</b><br>
결과 비교 완료: <b>{rbs['오늘비교']}경주</b><br>
아직 결과 미입력: <b>{rbs['미비교']}경주</b><br>
<span class="note">매 경주 예상 → 실제결과 → 왜 틀렸는지/맞았는지 저장 → 다음 분석에 반영</span>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="box"><b style="font-size:21px;">조합 배분</b><br><br>
방어 삼복승: <b>{result['방어삼복승']}</b><br>
주력 삼쌍승: <b>{result['공격삼쌍승']}</b><br>
보조 삼쌍승: <b>{result['보조삼쌍승']}</b><br>
놓치기 아까운 삼쌍승: <b>{result['놓치기아까운1']}</b> / <b>{result['놓치기아까운2']}</b>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="box"><b style="font-size:21px;">자동 환경 반영</b><br><br>
<div class="env">
<div>날씨<br><b>{env.get('weather','-')}</b></div>
<div>주로<br><b>{env.get('track','-')}</b></div>
<div>모래<br><b>{env.get('sand','-')}</b></div>
<div>바람<br><b>{env.get('wind','-')}</b></div>
<div>강수<br><b>{env.get('precip','-')}mm</b></div>
<div>출처<br><b>{env.get('source','-')}</b></div>
</div></div>
""", unsafe_allow_html=True)

st.link_button("KRA 공식 바로가기", kra_url, use_container_width=True)
st.markdown("<div class='note'>※ 자동구매 아님 · 공식 화면으로 이동 · 수익 보장 아님 · 손실 제한/기록학습 엔진</div>", unsafe_allow_html=True)

with st.expander("결과 입력 / 자가학습", expanded=False):
    actual_combo = st.text_input("실제 삼쌍 1-2-3", placeholder="예: 5-11-2")
    actual_trio = st.text_input("실제 삼복 1~3착", placeholder="예: 5/11/2")
    bet_amount = st.number_input("투입금", min_value=0, value=int(result["추천금액"]), step=100)
    return_amount = st.number_input("환급금", min_value=0, value=0, step=100)
    memo = st.text_input("메모")
    if st.button("결과 저장하고 AI 학습", use_container_width=True):
        hit = 1 if return_amount > 0 else 0
        roi = ((return_amount - bet_amount) / bet_amount) if bet_amount > 0 else 0
        rec = {
            "저장시각":datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "경마장":result["경마장"], "경주번호":result["경주번호"],
            "판정":result["판정"], "공격삼쌍승":result["공격삼쌍승"], "방어삼복승":result["방어삼복승"],
            "추천금액":result["추천금액"], "투입금":bet_amount, "환급금":return_amount, "수익률":roi, "적중":hit,
            "실제삼쌍":actual_combo, "실제삼복":actual_trio, "날씨":env.get("weather",""), "주로":env.get("track",""),
            "모래":env.get("sand",""), "바람":env.get("wind",""), "메모":memo
        }
        records = append_result(rec)
        compare_df, reason = append_compare_log(result, actual_combo, actual_trio, bet_amount, return_amount, memo, env)
        w, msg1 = update_learning(records)
        w, msg2 = update_learning_from_compare(compare_df)
        st.success("결과 저장 + 예상비교 완료")
        st.info(reason["분석결과"] + " / " + reason["틀린이유_또는_맞은이유"])
        st.info(msg1 + " / " + msg2)
        st.json(w)

with st.expander("숨겨진 분석 / 빅데이터", expanded=False):
    st.subheader("추천 빅데이터 로그")
    rlog = read_table(RECO_FILE)
    if rlog.empty:
        st.info("아직 추천 로그가 없습니다.")
    else:
        st.dataframe(rlog.tail(100), use_container_width=True)
    st.subheader("예상 vs 실제 비교 / 오답학습 로그")
    clog = read_table(COMPARE_FILE)
    if clog.empty:
        st.info("아직 비교 로그가 없습니다.")
    else:
        st.dataframe(clog.tail(100), use_container_width=True)

    st.subheader("결과 기록")
    reslog = read_table(RESULT_FILE)
    if reslog.empty:
        st.info("아직 결과 기록이 없습니다.")
    else:
        st.dataframe(reslog.tail(100), use_container_width=True)
    st.subheader("말별 점수표")
    st.dataframe(score_df, use_container_width=True)
    st.subheader("삼쌍승 시뮬레이션")
    st.dataframe(pd.DataFrame(combos), use_container_width=True)
    st.subheader("자가학습 가중치")
    st.json(load_weights())
