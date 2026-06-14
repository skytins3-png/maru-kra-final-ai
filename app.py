
import os
import json
import time
import random
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="MARU KRA 실시간 19API HUB",
    page_icon="🏇",
    layout="wide",
    initial_sidebar_state="collapsed",
)

KST = ZoneInfo("Asia/Seoul")
DATA_DIR = Path("maru_kra_data")
DATA_DIR.mkdir(exist_ok=True)
LOCAL_HUB_FILE = DATA_DIR / "maru_kra_hub_records.csv"
API_STATUS_FILE = DATA_DIR / "maru_kra_api_status.csv"
LOCAL_SETTINGS_FILE = DATA_DIR / "maru_kra_local_settings.json"

# 사용자가 올린 NO_REINPUT 원본 ZIP에서 추출한 실제 API 기본 URL
FORCE_DEFAULT_URLS = {'race_url': 'https://apis.data.go.kr/B551015/API186_1/SeoulRace_1', 'entry_url': 'https://apis.data.go.kr/B551015/API23_1/entryRaceHorse_1', 'horse_url': 'https://apis.data.go.kr/B551015/API310/raceHorseInfo', 'body_url': 'https://apis.data.go.kr/B551015/API25_1/raceHorseBody', 'gear_url': 'https://apis.data.go.kr/B551015/API24_1/raceHorseGear', 'rating_url': 'https://apis.data.go.kr/B551015/API77/raceHorseRating', 'odds_url': 'https://apis.data.go.kr/B551015/API28_1/Dividend_rate', 'today_odds_url': 'https://apis.data.go.kr/B551015/API301/Dividend_rate_total', 'result_detail_url': 'https://apis.data.go.kr/B551015/API299_1/raceResultDetail_1', 'race_record_url': 'https://apis.data.go.kr/B551015/API214_1/raceRecord_1', 'start_exam_url': 'https://apis.data.go.kr/B551015/API76_1/startExamResult_1', 'judge_url': 'https://apis.data.go.kr/B551015/API72_1/raceJudge_1', 'jockey_change_url': 'https://apis.data.go.kr/B551015/API71_1/jockeyChange_1', 'weather_alert_url': 'https://apis.data.go.kr/1360000/WthrWrnInfoService/getPwnStatus', 'corner_pace_url': 'https://apis.data.go.kr/B551015/API303/corner_rank', 'popularity_url': 'https://apis.data.go.kr/B551015/API302/popularity', 'first_odds_url': 'https://apis.data.go.kr/B551015/API27_1/winPredictionRateInfo_1', 'second_odds_url': 'https://apis.data.go.kr/B551015/API29_1/doublePredictionRateInfo_1', 'third_odds_url': 'https://apis.data.go.kr/B551015/API30_1/triplePredictionRateInfo_1'}

API_LABELS = [
    ("race_url", "경주정보"),
    ("entry_url", "출전등록말"),
    ("horse_url", "경주마정보"),
    ("body_url", "출전마 체중"),
    ("gear_url", "장구/폐출혈"),
    ("rating_url", "레이팅"),
    ("odds_url", "배당/매출"),
    ("today_odds_url", "시행당일 배당종합"),
    ("result_detail_url", "AI 경주결과상세"),
    ("race_record_url", "경주기록"),
    ("start_exam_url", "출발심사"),
    ("judge_url", "경주심판"),
    ("jockey_change_url", "기수변경"),
    ("weather_alert_url", "기상특보"),
    ("corner_pace_url", "코너/주로빠르기"),
    ("popularity_url", "인기투표"),
    ("first_odds_url", "1착마 적중승식"),
    ("second_odds_url", "2착마 적중승식"),
    ("third_odds_url", "3착마 적중승식"),
]

def now_kst():
    return datetime.now(KST)

def today_kst():
    return now_kst().strftime("%Y%m%d")

def now_str():
    return now_kst().strftime("%Y-%m-%d %H:%M:%S")

def secret_get(names, default=""):
    try:
        if "maru" in st.secrets:
            for n in names:
                if n in st.secrets["maru"]:
                    return str(st.secrets["maru"][n])
    except Exception:
        pass
    try:
        for n in names:
            if n in st.secrets:
                return str(st.secrets[n])
    except Exception:
        pass
    for n in names:
        val = os.environ.get(n)
        if val:
            return str(val)
    return default

def load_local_settings():
    try:
        if LOCAL_SETTINGS_FILE.exists():
            return json.loads(LOCAL_SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}

def save_local_settings(payload):
    try:
        current = load_local_settings()
        current.update(payload)
        LOCAL_SETTINGS_FILE.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False

def get_api_key():
    # 우선순위: 화면에서 저장한 값 → Streamlit Secrets → 환경변수
    try:
        if st.session_state.get("api_key_saved"):
            return str(st.session_state.get("api_key_saved", "")).strip()
    except Exception:
        pass

    local = load_local_settings()
    if local.get("api_key"):
        return str(local.get("api_key", "")).strip()

    return secret_get(["API_KEY", "api_key", "PUBLIC_DATA_API_KEY", "SERVICE_KEY", "serviceKey"], "")

API_KEY = get_api_key()

def get_url(key):
    # URL도 화면에 다시 입력하지 않음. Secrets에 있으면 우선, 없으면 원본 ZIP 기본값 사용.
    val = secret_get([key, key.upper()], "")
    if val:
        return val
    return FORCE_DEFAULT_URLS.get(key, "")

def mask_key(s):
    s = str(s or "")
    key = str(API_KEY or "")
    if key and key in s:
        s = s.replace(key, key[:5] + "****" + key[-4:])
    return s

def css():
    st.markdown("""
<style>
.main .block-container {padding-top: 1rem; max-width: 1200px;}
.hero {
  background: linear-gradient(135deg,#f3fff1,#ffffff,#eef7ff);
  border:1px solid rgba(0,0,0,.08); border-radius:20px;
  padding:18px 20px; box-shadow:0 6px 22px rgba(0,0,0,.06);
}
.green {
  background:#efffed; border:1px solid rgba(35,130,55,.18); border-radius:20px;
  padding:18px 20px; box-shadow:0 5px 18px rgba(0,0,0,.05);
}
.combo {font-size:46px; font-weight:900; color:#13662d; letter-spacing:1px;}
.muted {color:#666; font-size:13px;}
.stButton > button {width:100%; border-radius:12px; min-height:44px; font-weight:800;}
</style>
""", unsafe_allow_html=True)

def add_or_replace_params(url, params):
    parsed = urlparse(url)
    q = dict(parse_qsl(parsed.query, keep_blank_values=True))
    for k, v in params.items():
        if v is not None and str(v) != "":
            q[k] = str(v)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, urlencode(q, doseq=True), parsed.fragment))

def endpoint_with_placeholders(url, rc_date, meet, race_no):
    key = API_KEY or ""
    repl = {
        "{serviceKey}": key, "{SERVICE_KEY}": key, "{api_key}": key, "{API_KEY}": key,
        "{today}": rc_date, "{ymd}": rc_date, "{rcDate}": rc_date, "{raceDate}": rc_date,
        "{raceNo}": str(race_no), "{rcNo}": str(race_no),
        "{meet}": meet, "{track_place}": meet,
    }
    out = str(url or "")
    for a, b in repl.items():
        out = out.replace(a, b)
    return out

def request_variants(base_url, rc_date, meet, race_no):
    url = endpoint_with_placeholders(base_url, rc_date, meet, race_no)
    key = API_KEY or ""
    base_params = {"serviceKey": key, "pageNo": 1, "numOfRows": 100}
    variants = []

    p1 = dict(base_params); p1["resultType"] = "json"
    variants.append(add_or_replace_params(url, p1))

    p2 = dict(base_params); p2["_type"] = "json"
    variants.append(add_or_replace_params(url, p2))

    for date_name in ["rcDate", "raceDate", "meetDate"]:
        for race_name in ["rcNo", "raceNo"]:
            p = dict(base_params)
            p.update({date_name: rc_date, race_name: race_no, "resultType": "json"})
            variants.append(add_or_replace_params(url, p))

    meet_map = {"서울":"1", "제주":"2", "부산경남":"3", "부경":"3"}
    for meet_name in ["meet", "meetCd", "rcourse"]:
        p = dict(base_params)
        p.update({"rcDate": rc_date, "rcNo": race_no, meet_name: meet_map.get(meet, meet), "resultType": "json"})
        variants.append(add_or_replace_params(url, p))

    if "serviceKey=" in url:
        variants.append(url)

    seen, out = set(), []
    for v in variants:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out

def json_to_df(obj):
    if obj is None:
        return pd.DataFrame()
    candidates = []
    if isinstance(obj, dict):
        paths = [
            ["response","body","items","item"],
            ["response","body","item"],
            ["body","items","item"],
            ["items","item"],
            ["data"],
            ["result"],
        ]
        for path in paths:
            cur = obj
            ok = True
            for p in path:
                if isinstance(cur, dict) and p in cur:
                    cur = cur[p]
                else:
                    ok = False
                    break
            if ok:
                candidates = cur
                break
        if candidates == []:
            def walk(x):
                if isinstance(x, list) and (not x or isinstance(x[0], dict)):
                    return x
                if isinstance(x, dict):
                    for v in x.values():
                        got = walk(v)
                        if got is not None:
                            return got
                return None
            got = walk(obj)
            candidates = got if got is not None else obj
    else:
        candidates = obj

    if isinstance(candidates, dict):
        candidates = [candidates]
    if not isinstance(candidates, list):
        return pd.DataFrame()
    try:
        return pd.json_normalize(candidates)
    except Exception:
        return pd.DataFrame(candidates)

def xml_to_df(txt):
    try:
        root = ET.fromstring(txt)
        rows = []
        for item in root.findall(".//item"):
            rows.append({c.tag: c.text for c in item})
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()

def fetch_one_api(key, rc_date, meet, race_no):
    url = get_url(key)
    if not url:
        return pd.DataFrame(), "URL 없음", ""
    if not API_KEY and "serviceKey=" not in url:
        return pd.DataFrame(), "API_KEY 없음: Secrets 필요", ""

    last_msg = ""
    last_url = ""
    for req_url in request_variants(url, rc_date, meet, race_no):
        last_url = req_url
        try:
            r = requests.get(req_url, timeout=15)
            if r.status_code != 200:
                last_msg = f"HTTP {r.status_code}"
                continue
            txt = r.text.strip()
            if "SERVICE_KEY_IS_NOT_REGISTERED" in txt or "INVALID_REQUEST_PARAMETER" in txt or "SERVICE_ACCESS_DENIED" in txt:
                last_msg = txt[:160]
                continue
            ctype = r.headers.get("content-type","").lower()
            if txt.startswith("{") or txt.startswith("[") or "json" in ctype:
                try:
                    df = json_to_df(r.json())
                except Exception:
                    df = pd.DataFrame()
            else:
                df = xml_to_df(txt)
            if not df.empty:
                return df, "OK", req_url
            last_msg = "응답 200 / 데이터 0건"
        except Exception as e:
            last_msg = str(e)[:180]
    return pd.DataFrame(), last_msg, last_url

def normalize_meet(x):
    s = str(x or "").strip()
    if s in ["1","서울","SEOUL","Seoul","seoul"]:
        return "서울"
    if s in ["2","제주","JEJU","Jeju","jeju"]:
        return "제주"
    if s in ["3","부산경남","부경","부산","BUSAN","Busan","busan"]:
        return "부산경남"
    return s

def find_col(df, names):
    if df is None or df.empty:
        return None
    lower = {str(c).lower(): c for c in df.columns}
    for n in names:
        if str(n).lower() in lower:
            return lower[str(n).lower()]
    for c in df.columns:
        cl = str(c).lower()
        for n in names:
            if str(n).lower() in cl:
                return c
    return None

def horse_no_col(df):
    return find_col(df, ["chulNo", "출전번호", "출전마번", "마번", "horseNo", "hrNo"])

def horse_name_col(df):
    return find_col(df, ["hrName", "horseName", "마명", "경주마명"])

def num_series(s, default=0):
    return pd.to_numeric(s, errors="coerce").fillna(default)

def current_filter(df, rc_date, meet, race_no):
    if df is None or df.empty:
        return df
    d = df.copy()
    original = d.copy()

    date_col = find_col(d, ["rcDate","raceDate","meetDate","날짜","경주일자"])
    meet_col = find_col(d, ["meet","meetCd","rcourse","경마장"])
    rc_col = find_col(d, ["rcNo","raceNo","경주번호"])

    try:
        if date_col:
            ds = d[date_col].astype(str).str.replace("-","",regex=False).str.strip()
            tmp = d[ds == rc_date]
            if not tmp.empty:
                d = tmp
    except Exception:
        pass
    try:
        if meet_col:
            tmp = d[d[meet_col].apply(normalize_meet) == normalize_meet(meet)]
            if not tmp.empty:
                d = tmp
    except Exception:
        pass
    try:
        if rc_col:
            rs = pd.to_numeric(d[rc_col], errors="coerce")
            tmp = d[rs == int(race_no)]
            if not tmp.empty:
                d = tmp
    except Exception:
        pass
    return d if not d.empty else original

def sample_data():
    return pd.DataFrame([
        {"마번":5,"마명":"마루스피드","레이팅":78,"최근순위":2,"승률":18,"복승률":42,"예상배당":9.2,"체중변화":-2,"기수점수":75,"인기":4},
        {"마번":11,"마명":"그린파워","레이팅":75,"최근순위":3,"승률":15,"복승률":38,"예상배당":7.8,"체중변화":-1,"기수점수":72,"인기":5},
        {"마번":2,"마명":"블루런","레이팅":72,"최근순위":4,"승률":12,"복승률":35,"예상배당":12.5,"체중변화":0,"기수점수":69,"인기":7},
        {"마번":7,"마명":"라스트킹","레이팅":70,"최근순위":5,"승률":10,"복승률":30,"예상배당":15.4,"체중변화":2,"기수점수":67,"인기":8},
        {"마번":3,"마명":"해피로드","레이팅":66,"최근순위":6,"승률":8,"복승률":25,"예상배당":22.0,"체중변화":-4,"기수점수":65,"인기":9},
    ])

def build_base_horses(data, rc_date, meet, race_no):
    priority = ["entry_url", "body_url", "gear_url", "today_odds_url", "odds_url", "rating_url", "horse_url"]
    rows = {}
    for key in priority:
        df = current_filter(data.get(key, pd.DataFrame()), rc_date, meet, race_no)
        if df is None or df.empty:
            continue
        no_col = horse_no_col(df)
        if not no_col:
            continue
        name_col = horse_name_col(df)
        for _, r in df.iterrows():
            try:
                n = int(float(r.get(no_col)))
            except Exception:
                continue
            if not 1 <= n <= 20:
                continue
            if n not in rows:
                rows[n] = {"마번": n, "마명": f"{n}번", "근거API": []}
            if name_col and str(r.get(name_col, "")).strip():
                rows[n]["마명"] = str(r.get(name_col)).strip()
            rows[n]["근거API"].append(key.replace("_url",""))
    if not rows:
        return sample_data()
    return pd.DataFrame(list(rows.values())).sort_values("마번")

def merge_score_features(base, data, rc_date, meet, race_no):
    h = base.copy()
    h["레이팅"] = 60
    h["최근순위"] = 5
    h["승률"] = 8
    h["복승률"] = 25
    h["예상배당"] = 12.0
    h["체중변화"] = 0
    h["기수점수"] = 65
    h["인기"] = 7

    def map_by_no(key, target_col, candidate_cols):
        df = current_filter(data.get(key, pd.DataFrame()), rc_date, meet, race_no)
        if df is None or df.empty:
            return
        no_col = horse_no_col(df)
        val_col = find_col(df, candidate_cols)
        if not no_col or not val_col:
            return
        tmp = df[[no_col, val_col]].copy()
        tmp[no_col] = pd.to_numeric(tmp[no_col], errors="coerce")
        tmp = tmp.dropna(subset=[no_col])
        mp = dict(zip(tmp[no_col].astype(int), tmp[val_col]))
        h[target_col] = h["마번"].map(mp).fillna(h[target_col])

    map_by_no("rating_url", "레이팅", ["rating","레이팅","rt","ratingValue"])
    map_by_no("race_record_url", "최근순위", ["ord","rank","chaksun","최근순위","순위"])
    map_by_no("odds_url", "예상배당", ["odds","배당","winOdds","dividend","배당률"])
    map_by_no("today_odds_url", "예상배당", ["odds","배당","winOdds","dividend","배당률"])
    map_by_no("body_url", "체중변화", ["wgBudam","weightDiff","체중변화","증감","diff"])
    map_by_no("popularity_url", "인기", ["popRank","popularity","인기","인기순위"])
    map_by_no("jockey_change_url", "기수점수", ["jockeyScore","기수점수"])

    med = sample_data()
    for c in ["레이팅","최근순위","승률","복승률","예상배당","체중변화","기수점수","인기"]:
        fallback = med[c].median() if c in med else 0
        h[c] = pd.to_numeric(h[c], errors="coerce").fillna(fallback)
    return h

def fetch_weather(meet):
    coords = {"서울":(37.4438,127.0165), "부산경남":(35.1545,128.8782), "제주":(33.4097,126.3934)}
    lat, lon = coords.get(meet, coords["서울"])
    env = {"날씨":"기본", "강수":0.0, "바람":0.0, "주로":"양호", "모래":"보통"}
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation,weather_code,wind_speed_10m&timezone=Asia%2FSeoul"
        cur = requests.get(url, timeout=8).json().get("current", {})
        precip = float(cur.get("precipitation", 0) or 0)
        wind = float(cur.get("wind_speed_10m", 0) or 0)
        code = int(cur.get("weather_code", 0) or 0)
        weather = "비" if precip >= 0.3 or code in [51,53,55,61,63,65,80,81,82,95,96,99] else ("흐림" if code in [1,2,3,45,48] else "맑음")
        track = "포화" if precip >= 3 else ("다습" if precip >= 0.3 else "양호")
        sand = "무거움" if precip >= 1 else "보통"
        env = {"날씨":weather, "강수":precip, "바람":wind, "주로":track, "모래":sand}
    except Exception:
        pass
    return env

def score_and_recommend(h, env, sim_count=1000, risk_mode="균형형"):
    x = h.copy()
    recent_score = (10 - num_series(x["최근순위"], 5).clip(1,10)) * 4.0
    rating_score = (num_series(x["레이팅"], 60).clip(40,100) - 40) * 0.85
    win_score = num_series(x["승률"], 8).clip(0,50) * 0.9
    place_score = num_series(x["복승률"], 25).clip(0,80) * 0.45
    odds = num_series(x["예상배당"], 12).clip(1,100)
    value_score = odds.apply(lambda v: 18 if 6 <= v <= 25 else (11 if 25 < v <= 45 else 4))
    weight_delta = num_series(x["체중변화"], 0)
    weight_score = weight_delta.apply(lambda v: 7 if -3 <= v <= -1 else (2 if v == 0 else (-8 if abs(v) >= 5 else -2)))
    jockey_score = num_series(x["기수점수"], 65) * 0.25
    pop_score = (10 - num_series(x["인기"], 7).clip(1,10)) * 1.2
    env_bonus = 2 if env.get("주로") == "양호" else -1

    x["점수"] = recent_score + rating_score + win_score + place_score + value_score + weight_score + jockey_score + pop_score + env_bonus
    x = x.sort_values("점수", ascending=False).reset_index(drop=True)

    nums = x["마번"].astype(int).tolist()
    scores = x["점수"].astype(float).tolist()
    volatility = 5.5 + (1.5 if env.get("주로") in ["다습","포화"] else 0)
    if risk_mode == "안전형":
        volatility *= 0.88
    elif risk_mode == "공격형":
        volatility *= 1.15

    random.seed(42)
    counts = {}
    for _ in range(int(sim_count)):
        noisy = [(n, s + random.gauss(0, volatility)) for n, s in zip(nums, scores)]
        top3 = tuple(str(n) for n, _ in sorted(noisy, key=lambda a:a[1], reverse=True)[:3])
        counts[top3] = counts.get(top3, 0) + 1
    combos = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:10]
    if combos:
        top_combo = combos[0][0]
        combo_txt = " - ".join(top_combo)
        confidence = min(94, max(35, int(combos[0][1] / int(sim_count) * 100 + 50)))
    else:
        combo_txt = "-"
        confidence = 0

    defense = "-"
    if len(x) >= 4:
        defense = f"{int(x.iloc[0]['마번'])} - {int(x.iloc[1]['마번'])} - {int(x.iloc[3]['마번'])}"

    avg_odds = float(num_series(x.head(3)["예상배당"], 10).mean()) if len(x) else 0
    decision = "소액 공격" if confidence >= 75 else ("소액 가능" if confidence >= 62 else "관망")
    amount = 1000 if decision != "관망" else 0

    result = {
        "판정": decision,
        "공격삼쌍승": combo_txt,
        "방어삼복승": defense,
        "예상배당": round(avg_odds, 1),
        "신뢰도": confidence,
        "추천금액": amount,
        "근거": " · ".join([f"{int(r['마번'])}번 {r.get('마명','')} 점수상위" for _, r in x.head(3).iterrows()]),
    }
    combo_rows = [{"조합":" - ".join(k), "반복횟수":v, "비율":round(v/int(sim_count)*100,1)} for k,v in combos]
    return x, result, combo_rows

def load_local_hub():
    if LOCAL_HUB_FILE.exists():
        try:
            return pd.read_csv(LOCAL_HUB_FILE)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def append_local_hub(row):
    old = load_local_hub()
    new = pd.concat([old, pd.DataFrame([row])], ignore_index=True)
    new.to_csv(LOCAL_HUB_FILE, index=False, encoding="utf-8-sig")
    return len(new)

def sheets_secret_get(names, default=""):
    try:
        if "google_sheets" in st.secrets:
            for n in names:
                if n in st.secrets["google_sheets"]:
                    return st.secrets["google_sheets"][n]
        for n in names:
            if n in st.secrets:
                return st.secrets[n]
    except Exception:
        pass
    return default

def get_gsheet_client():
    sheet_id = sheets_secret_get(["SHEET_ID","sheet_id"], "")
    if not sheet_id:
        return None, "SHEET_ID 없음"
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        raw = sheets_secret_get(["SERVICE_ACCOUNT_JSON","service_account_json"], "")
        info = None
        if raw:
            info = json.loads(raw) if isinstance(raw, str) else dict(raw)
        elif "google_sheets" in st.secrets and "service_account" in st.secrets["google_sheets"]:
            info = dict(st.secrets["google_sheets"]["service_account"])
        if not info:
            return None, "서비스계정 JSON 없음"
        scopes = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(info, scopes=scopes)
        return gspread.authorize(creds), ""
    except Exception as e:
        return None, str(e)[:120]

def hub_append_sheet(sheet_name, row):
    sheet_id = sheets_secret_get(["SHEET_ID","sheet_id"], "")
    client, msg = get_gsheet_client()
    if client is None:
        return False, msg
    try:
        sh = client.open_by_key(str(sheet_id))
        try:
            ws = sh.worksheet(sheet_name)
        except Exception:
            ws = sh.add_worksheet(title=sheet_name, rows=1000, cols=30)
        existing = ws.get_all_values()
        headers = list(row.keys())
        if not existing:
            ws.append_row(headers)
        else:
            headers = existing[0]
            missing = [k for k in row.keys() if k not in headers]
            if missing:
                headers = headers + missing
                ws.update("1:1", [headers])
        ws.append_row([row.get(h, "") for h in headers], value_input_option="USER_ENTERED")
        return True, "Google Sheet 허브 저장 성공"
    except Exception as e:
        return False, str(e)[:120]

def hub_read_sheet(sheet_name, limit=100):
    client, msg = get_gsheet_client()
    if client is None:
        return pd.DataFrame()
    try:
        sheet_id = sheets_secret_get(["SHEET_ID","sheet_id"], "")
        sh = client.open_by_key(str(sheet_id))
        ws = sh.worksheet(sheet_name)
        vals = ws.get_all_records()
        return pd.DataFrame(vals).tail(limit)
    except Exception:
        return pd.DataFrame()

def fetch_all_live(rc_date, meet, race_no, selected_keys):
    data = {}
    statuses = []
    progress = st.progress(0)
    label_map = dict(API_LABELS)
    for i, key in enumerate(selected_keys):
        df, msg, used_url = fetch_one_api(key, rc_date, meet, race_no)
        data[key] = df
        statuses.append({
            "API": label_map.get(key, key),
            "key": key,
            "행수": len(df),
            "컬럼수": len(df.columns) if not df.empty else 0,
            "상태": msg,
            "요청URL": mask_key(used_url),
        })
        progress.progress((i+1)/max(1,len(selected_keys)))
    progress.empty()
    pd.DataFrame(statuses).to_csv(API_STATUS_FILE, index=False, encoding="utf-8-sig")
    return data, pd.DataFrame(statuses)

def render():
    css()
    st.markdown("""
<div class="hero">
<h2>🏇 MARU KRA 실시간 19API HUB</h2>
<div class="muted">API Key 저장 입력란 · 원본 NO_REINPUT API 주소 유지 · 한국시간 KST · 모바일/PC 허브 저장/불러오기</div>
</div>
""", unsafe_allow_html=True)

    with st.sidebar:
        st.title("🐎 MARU KRA")
        st.success("API URL 19개는 원본 ZIP 값 자동 적용")
        st.info(f"현재 한국시간: {now_kst().strftime('%Y-%m-%d %H:%M:%S')} KST")

        current_key = get_api_key()
        key_input = st.text_input(
            "공공데이터 API Key",
            value=current_key,
            type="password",
            placeholder="공공데이터 일반 인증키 입력"
        )
        if st.button("API Key 저장", use_container_width=True):
            if key_input.strip():
                st.session_state["api_key_saved"] = key_input.strip()
                if save_local_settings({"api_key": key_input.strip(), "saved_at_kst": now_str()}):
                    st.success("API Key 저장 완료")
                    st.rerun()
                else:
                    st.warning("세션에는 저장됐지만 파일 저장은 실패했습니다.")
            else:
                st.warning("API Key를 입력해 주세요.")

        if get_api_key():
            st.success("공공데이터 API Key 사용 가능")
        else:
            st.error("API Key 없음: 입력 후 [API Key 저장]을 눌러주세요.")

        target_date = st.text_input("분석 날짜", value=today_kst())
        meet = st.selectbox("경마장", ["서울","부산경남","제주"], index=0)
        race_no = st.number_input("경주번호", min_value=1, max_value=20, value=1, step=1)
        sim_count = st.slider("시뮬레이션", 300, 5000, 1200, step=100)
        risk_mode = st.selectbox("전략", ["균형형","안전형","공격형"], index=0)
        auto_refresh = st.selectbox("자동 새로고침", [0, 30, 60, 120, 300], index=0)
        st.divider()
        core_default = ["race_url","entry_url","body_url","rating_url","today_odds_url","jockey_change_url","corner_pace_url","popularity_url"]
        selected = st.multiselect(
            "실시간 호출 API",
            options=[k for k,_ in API_LABELS],
            default=core_default,
            format_func=lambda k: dict(API_LABELS).get(k,k),
        )
        with st.expander("API URL 확인/복사용", expanded=False):
            for k, label in API_LABELS:
                st.caption(f"{label}: {get_url(k)}")
        st.divider()
        st.caption("Google Sheet 허브는 Secrets의 SHEET_ID/SERVICE_ACCOUNT_JSON이 있으면 사용됩니다.")

    rc_date = str(target_date).replace("-","").strip() or today_kst()

    if auto_refresh:
        st.caption(f"자동 새로고침 {auto_refresh}초")
        time.sleep(0.1)

    local_hub = load_local_hub()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("API Key", "자동로드" if API_KEY else "없음")
    c2.metric("허브 로컬", f"{len(local_hub)}건")
    c3.metric("경주", f"{meet} {int(race_no)}R")
    c4.metric("날짜", rc_date)

    tab1, tab2, tab3, tab4 = st.tabs(["🏇 실시간 분석", "📦 허브", "🔌 API 진단", "📘 Secrets"])

    with tab1:
        st.markdown("### 실시간 KRA 분석")
        if "live_data" not in st.session_state:
            st.session_state["live_data"] = {}
            st.session_state["api_status"] = pd.DataFrame()

        col_a, col_b = st.columns([1,1])
        with col_a:
            run = st.button("실시간 데이터 불러오기", type="primary")
        with col_b:
            run_sim = st.button("불러오기 + 시뮬레이션")

        if run or run_sim or not st.session_state["live_data"]:
            data, status = fetch_all_live(rc_date, meet, int(race_no), selected)
            st.session_state["live_data"] = data
            st.session_state["api_status"] = status

        data = st.session_state["live_data"]
        status = st.session_state["api_status"]

        env = fetch_weather(meet)
        base = build_base_horses(data, rc_date, meet, int(race_no))
        horses = merge_score_features(base, data, rc_date, meet, int(race_no))
        score_df, result, combos = score_and_recommend(horses, env, sim_count, risk_mode)

        live_rows = sum(len(v) for v in data.values()) if data else 0
        if live_rows == 0:
            st.warning("실시간 API 데이터 0건입니다. 현재 화면은 샘플/보정 분석입니다. API Key/승인/상세 URL을 확인해야 합니다.")
        else:
            st.success(f"실시간 API 데이터 {live_rows}행 반영")

        left, right = st.columns([1.1, 1])
        with left:
            st.markdown(f"""
<div class="green">
<div class="muted">{meet} {int(race_no)}R · {rc_date} · {env.get('날씨')}/{env.get('주로')}</div>
<div class="combo">{result.get('공격삼쌍승','-')}</div>
<div><b>{result.get('판정','대기')}</b> · 추천금액 {int(result.get('추천금액',0)):,}원</div>
<hr>
<b>방어:</b> {result.get('방어삼복승','-')}<br>
<b>예상배당:</b> {result.get('예상배당',0)}배<br>
<b>근거:</b> {result.get('근거','')}
</div>
""", unsafe_allow_html=True)
            st.caption("경마 결과는 보장되지 않습니다. 실구매는 본인 판단과 책임, 소액 원칙으로만 진행하세요.")

            if st.button("현재 분석 허브 저장", type="primary"):
                row = {
                    "저장시각": now_str(),
                    "날짜": rc_date,
                    "경마장": meet,
                    "경주번호": int(race_no),
                    "판정": result.get("판정",""),
                    "공격삼쌍승": result.get("공격삼쌍승",""),
                    "방어삼복승": result.get("방어삼복승",""),
                    "예상배당": result.get("예상배당",""),
                    "신뢰도": result.get("신뢰도",""),
                    "추천금액": result.get("추천금액",""),
                    "날씨": env.get("날씨",""),
                    "주로": env.get("주로",""),
                    "모래": env.get("모래",""),
                    "바람": env.get("바람",""),
                    "실시간행수": live_rows,
                    "근거": result.get("근거",""),
                }
                n = append_local_hub(row)
                ok, msg = hub_append_sheet("recommendations", row)
                if ok:
                    st.success(f"허브 저장 완료: Google Sheet + 로컬 {n}건")
                else:
                    st.info(f"로컬 허브 저장 완료 {n}건 / Google Sheet: {msg}")

        with right:
            m1,m2,m3 = st.columns(3)
            m1.metric("신뢰도", f"{result.get('신뢰도',0)}%")
            m2.metric("실시간행", live_rows)
            m3.metric("추천금액", f"{int(result.get('추천금액',0)):,}")
            st.markdown("#### 말별 점수")
            st.dataframe(score_df, use_container_width=True, height=360)

        st.markdown("#### 시뮬레이션 조합")
        st.dataframe(pd.DataFrame(combos), use_container_width=True, height=260)

    with tab2:
        st.markdown("### 허브 저장/불러오기")
        sheet_df = hub_read_sheet("recommendations", 100)
        if not sheet_df.empty:
            st.success(f"Google Sheet 허브 {len(sheet_df)}건 불러옴")
            st.dataframe(sheet_df, use_container_width=True, height=420)
        else:
            st.info("Google Sheet 허브가 없거나 비어 있습니다. 로컬 허브를 표시합니다.")
            st.dataframe(load_local_hub().tail(100), use_container_width=True, height=420)

    with tab3:
        st.markdown("### API 진단")
        if not st.session_state.get("api_status", pd.DataFrame()).empty:
            st.dataframe(st.session_state["api_status"], use_container_width=True, height=420)
        else:
            st.write("아직 API 호출 전입니다.")
        st.markdown("#### 원본 ZIP 기반 API URL")
        st.dataframe(pd.DataFrame([{"API":label, "key":k, "URL":get_url(k)} for k,label in API_LABELS]), use_container_width=True)

    with tab4:
        st.markdown("""
### Streamlit Secrets 예시

앱 화면에서 `공공데이터 API Key: ************` 형태로 입력/저장할 수 있습니다. Streamlit Secrets를 써도 자동으로 불러옵니다.

```toml
[maru]
API_KEY = "공공데이터_일반인증키"
```

Google Sheet 허브까지 쓰려면:

```toml
[google_sheets]
SHEET_ID = "구글시트_ID"
SERVICE_ACCOUNT_JSON = "서비스계정_JSON_전체"
```

현재 ZIP은 사용자가 올린 `MARU_KRA_NO_REINPUT_API_ENGINE(1).zip` 안의 API URL 19개를 유지했고, 시간 기준은 한국시간(KST)입니다.
""")

render()
