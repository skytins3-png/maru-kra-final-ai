
import streamlit as st
import pandas as pd
import requests
import json
import random
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from collections import Counter

st.set_page_config(
    page_title="MARU KRA SECRETS AUTOLOAD",
    page_icon="🐎",
    layout="centered"
)

DATA_DIR = Path("maru_kra_data")
DATA_DIR.mkdir(exist_ok=True)

SETTINGS_FILE = DATA_DIR / "api_settings.json"
RECO_FILE = DATA_DIR / "recommendation_bigdata_log.csv"
RESULT_FILE = DATA_DIR / "race_result_records.csv"
COMPARE_FILE = DATA_DIR / "prediction_result_compare_log.csv"
WEIGHT_FILE = DATA_DIR / "learning_weights.json"

DEFAULT_SETTINGS = {
    "api_key": "",
    "save_api_key": False,
    "race_url": "",
    "entry_url": "",
    "horse_url": "",
    "body_url": "",
    "gear_url": "",
    "rating_url": "",
    "odds_url": "",
    "today_odds_url": "",
    "result_detail_url": "",
    "race_record_url": "",
    "start_exam_url": "",
    "judge_url": "",
    "jockey_change_url": "",
    "weather_alert_url": "",
    "corner_pace_url": "",
    "popularity_url": "",
    "first_odds_url": "",
    "second_odds_url": "",
    "third_odds_url": "",
    "kra_url": "https://m.kra.co.kr/main.do",
    "track_place": "서울",
    "bankroll": 100000,
    "unit_bet": 1000,
    "daily_loss_limit": 30000,
    "profit_unlock": 200000,
    "daily_budget": 30000,
    "daily_entries_limit": 3
}

DEFAULT_WEIGHTS = {
    "recent": 2.2,
    "win_rate": 0.45,
    "place_rate": 0.30,
    "rating": 0.55,
    "rating_delta": 1.8,
    "odds_value": 1.0,
    "environment": 1.0,
    "weight_penalty": 1.4,
    "risk_penalty": 1.0,
}

SECRET_MAP = {
    "api_key": ["API_KEY", "api_key"],
    "race_url": ["RACE_URL", "race_url"],
    "entry_url": ["ENTRY_URL", "entry_url"],
    "horse_url": ["HORSE_URL", "horse_url"],
    "body_url": ["BODY_URL", "body_url"],
    "gear_url": ["GEAR_URL", "gear_url"],
    "rating_url": ["RATING_URL", "rating_url"],
    "odds_url": ["ODDS_URL", "odds_url"],
    "today_odds_url": ["TODAY_ODDS_URL", "today_odds_url"],
    "result_detail_url": ["RESULT_DETAIL_URL", "result_detail_url"],
    "race_record_url": ["RACE_RECORD_URL", "race_record_url"],
    "start_exam_url": ["START_EXAM_URL", "start_exam_url"],
    "judge_url": ["JUDGE_URL", "judge_url"],
    "jockey_change_url": ["JOCKEY_CHANGE_URL", "jockey_change_url"],
    "weather_alert_url": ["WEATHER_ALERT_URL", "weather_alert_url"],
    "corner_pace_url": ["CORNER_PACE_URL", "corner_pace_url"],
    "popularity_url": ["POPULARITY_URL", "popularity_url"],
    "first_odds_url": ["FIRST_ODDS_URL", "first_odds_url"],
    "second_odds_url": ["SECOND_ODDS_URL", "second_odds_url"],
    "third_odds_url": ["THIRD_ODDS_URL", "third_odds_url"],
    "kra_url": ["KRA_URL", "kra_url"],
}



def mask_secret_url(url):
    s = str(url or "")
    try:
        import re as _re
        s = _re.sub(r"(serviceKey=)[^&]+", r"\1***", s)
        s = _re.sub(r"(servicekey=)[^&]+", r"\1***", s)
    except Exception:
        if "serviceKey=" in s:
            head, tail = s.split("serviceKey=", 1)
            rest = tail.split("&", 1)
            s = head + "serviceKey=***" + (("&" + rest[1]) if len(rest) > 1 else "")
    return s

def secret_get(names, default=""):
    """
    Streamlit Secrets에서 값 가져오기.
    [maru] 그룹 안과 최상단 둘 다 지원합니다.
    """
    try:
        # st.secrets는 일반 dict처럼 접근 가능
        if "maru" in st.secrets:
            for n in names:
                if n in st.secrets["maru"]:
                    return str(st.secrets["maru"][n])
        for n in names:
            if n in st.secrets:
                return str(st.secrets[n])
    except Exception:
        pass
    return default

def load_local_json(path, default):
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            merged = dict(default)
            merged.update(data)
            return merged
        except Exception:
            return dict(default)
    return dict(default)

def load_settings():
    """
    우선순위:
    1. DEFAULT
    2. 앱 내부 저장파일
    3. Streamlit Secrets
    Secrets가 있으면 항상 최종 우선 적용.
    """
    s = load_local_json(SETTINGS_FILE, DEFAULT_SETTINGS)
    for key, names in SECRET_MAP.items():
        val = secret_get(names, "")
        if val:
            s[key] = val
    if secret_get(["API_KEY", "api_key"], ""):
        s["save_api_key"] = True
    return s

def save_json(path, data):
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        (DATA_DIR / "api_settings_backup.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

def read_table(path):
    if path.exists():
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def append_table(path, row):
    df = read_table(path)
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return df

def today():
    return datetime.now().strftime("%Y-%m-%d")

settings = load_settings()
weights = load_local_json(WEIGHT_FILE, DEFAULT_WEIGHTS)
save_json(WEIGHT_FILE, weights)

st.title("🐎 MARU KRA AI")
st.caption("Secrets 자동불러오기 · API Key 숨김 · 현재 경주 부족 시 관망")

st.sidebar.header("MARU KRA 저장형")
if any(secret_get(names, "") for names in SECRET_MAP.values()):
    st.sidebar.success("Secrets 값 자동 불러옴")
else:
    st.sidebar.info("Secrets 미설정: 앱 입력값/저장값 사용")

api_key = st.sidebar.text_input(
    "공공데이터 API Key",
    value=settings.get("api_key", "") if settings.get("save_api_key") else "",
    type="password"
)
save_api_key = st.sidebar.checkbox("API Key도 저장", value=bool(settings.get("save_api_key", False)))

st.sidebar.caption("기본 주소만 넣으면 serviceKey/pageNo/numOfRows/resultType까지만 자동으로 붙입니다. 날짜/경마장 변수는 API별 URL에 직접 포함하세요.")

with st.sidebar.expander("API URL 입력 / Secrets 자동 채움", expanded=True):
    race_url = st.text_area("1. 경주정보 API URL", value=settings.get("race_url",""), height=64)
    entry_url = st.text_area("2. 출전 등록말 API URL", value=settings.get("entry_url",""), height=64)
    horse_url = st.text_area("3. 경주마 상세정보 API URL", value=settings.get("horse_url",""), height=64)
    body_url = st.text_area("4. 출전마 체중 API URL", value=settings.get("body_url",""), height=64)
    gear_url = st.text_area("5. 장구/폐출혈 API URL", value=settings.get("gear_url",""), height=64)
    rating_url = st.text_area("6. 레이팅 API URL", value=settings.get("rating_url",""), height=64)
    odds_url = st.text_area("7. 매출/확정배당률 API URL", value=settings.get("odds_url",""), height=64)
    today_odds_url = st.text_area("8. 시행당일 확정배당률 API URL", value=settings.get("today_odds_url",""), height=64)
    result_detail_url = st.text_area("9. AI기반 경주결과상세 API URL", value=settings.get("result_detail_url",""), height=64)
    race_record_url = st.text_area("10. 경주기록/요약성적표 API URL", value=settings.get("race_record_url",""), height=64)
    start_exam_url = st.text_area("11. 출발심사 결과 API URL", value=settings.get("start_exam_url",""), height=64)
    judge_url = st.text_area("12. 경주심판 정보 API URL", value=settings.get("judge_url",""), height=64)
    jockey_change_url = st.text_area("13. 기수변경 API URL", value=settings.get("jockey_change_url",""), height=64)
    weather_alert_url = st.text_area("14. 기상특보 API URL", value=settings.get("weather_alert_url",""), height=64)
    corner_pace_url = st.text_area("15. 코너별 통과순위/주로빠르기 API URL", value=settings.get("corner_pace_url",""), height=64)
    popularity_url = st.text_area("16. 경주마 인기투표 API URL", value=settings.get("popularity_url",""), height=64)
    first_odds_url = st.text_area("17. 1착마 적중승식 배당 API URL", value=settings.get("first_odds_url",""), height=64)
    second_odds_url = st.text_area("18. 2착마 적중승식 배당 API URL", value=settings.get("second_odds_url",""), height=64)
    third_odds_url = st.text_area("19. 3착마 적중승식 배당 API URL", value=settings.get("third_odds_url",""), height=64)

places = ["서울", "부산경남", "제주"]
track_place = st.sidebar.selectbox(
    "경마장",
    places,
    index=places.index(settings.get("track_place", "서울")) if settings.get("track_place", "서울") in places else 0
)


target_date = st.sidebar.text_input(
    "분석 날짜",
    value=settings.get("target_date", "") or datetime.now().strftime("%Y%m%d"),
    help="예: 20260614"
)
target_rc_no = st.sidebar.number_input(
    "분석 경주번호",
    min_value=1,
    max_value=20,
    value=int(settings.get("target_rc_no", 6)),
    step=1
)
strict_race_filter = st.sidebar.checkbox(
    "선택 경주만 엄격 필터",
    value=False,
    help="데이터가 충분할 때만 켜세요. 켜면 rcDate/meet/rcNo가 정확히 맞는 행만 분석합니다."
)

auto_weather = st.sidebar.checkbox("날씨/바람 자동수집", True)
manual_weather = st.sidebar.selectbox("날씨 보정", ["자동", "맑음", "흐림", "비", "눈"])
manual_track = st.sidebar.selectbox("주로 보정", ["자동", "건조", "양호", "다습", "포화", "불량"])
manual_sand = st.sidebar.selectbox("모래 보정", ["자동", "가벼움", "보통", "무거움"])
manual_wind = st.sidebar.selectbox("바람 보정", ["자동", "없음", "뒷바람", "맞바람", "측풍"])
distance_type = st.sidebar.selectbox("거리 성향", ["단거리", "중거리", "장거리"], index=1)

st.sidebar.divider()
sim_count = st.sidebar.selectbox("시뮬레이션 횟수", [100, 300, 500, 1000], index=1)
risk_mode = st.sidebar.selectbox("위험 성향", ["안전형", "균형형", "공격형"])
bankroll = st.sidebar.number_input("운영잔고", min_value=0, max_value=10000000, value=int(settings.get("bankroll",100000)), step=10000)
unit_bet = st.sidebar.number_input("20만원 전 1회 기준금액", min_value=100, max_value=10000, value=int(settings.get("unit_bet",1000)), step=100)
daily_loss_limit = st.sidebar.number_input("하루 손실 투자금지", min_value=10000, max_value=300000, value=int(settings.get("daily_loss_limit",30000)), step=1000)
profit_unlock = st.sidebar.number_input("3만원 운영 허용 기준", min_value=50000, max_value=1000000, value=int(settings.get("profit_unlock",200000)), step=10000)
daily_budget = st.sidebar.number_input("허용 후 하루 투자한도", min_value=10000, max_value=100000, value=int(settings.get("daily_budget",30000)), step=1000)
daily_entries_limit = st.sidebar.number_input("하루 최대 진입", min_value=1, max_value=10, value=int(settings.get("daily_entries_limit",3)))
auto_save_reco = st.sidebar.checkbox("추천 자동저장", True)
use_sample = st.sidebar.checkbox("데이터 없으면 샘플 사용", True)
kra_url = st.sidebar.text_input("KRA 공식 바로가기", value=settings.get("kra_url","https://m.kra.co.kr/main.do"))

def current_setting_payload():
    return {
        "api_key": api_key if save_api_key else "",
        "save_api_key": save_api_key,
        "race_url": race_url,
        "entry_url": entry_url,
        "horse_url": horse_url,
        "body_url": body_url,
        "gear_url": gear_url,
        "rating_url": rating_url,
        "odds_url": odds_url,
        "today_odds_url": today_odds_url,
        "result_detail_url": result_detail_url,
        "race_record_url": race_record_url,
        "start_exam_url": start_exam_url,
        "judge_url": judge_url,
        "jockey_change_url": jockey_change_url,
        "weather_alert_url": weather_alert_url,
        "corner_pace_url": corner_pace_url,
        "popularity_url": popularity_url,
        "first_odds_url": first_odds_url,
        "second_odds_url": second_odds_url,
        "third_odds_url": third_odds_url,
        "kra_url": kra_url,
        "track_place": track_place,
        "bankroll": bankroll,
        "unit_bet": unit_bet,
        "daily_loss_limit": daily_loss_limit,
        "profit_unlock": profit_unlock,
        "daily_budget": daily_budget,
        "daily_entries_limit": daily_entries_limit,
        "target_rc_no": int(target_rc_no),
        "target_date": target_date
    }

if st.sidebar.button("API 저장", use_container_width=True):
    save_json(SETTINGS_FILE, current_setting_payload())
    st.sidebar.success("저장 완료")


if st.sidebar.button("추천/비교 로그 초기화", use_container_width=True):
    for p in [RECO_FILE, COMPARE_FILE, RESULT_FILE]:
        try:
            if p.exists():
                p.unlink()
        except Exception:
            pass
    st.sidebar.warning("추천/비교/결과 로그 초기화 완료")

if st.sidebar.button("API 설정 초기화", use_container_width=True):
    if SETTINGS_FILE.exists():
        SETTINGS_FILE.unlink()
    st.sidebar.warning("앱 내부 저장값 초기화 완료. Secrets 값은 유지됩니다.")

def build_api_url(url):
    """
    안전형 자동완성:
    기본 주소만 넣으면 serviceKey/pageNo/numOfRows/resultType까지만 붙입니다.
    rcDate, meet 같은 API별 변수는 자동으로 붙이지 않습니다.
    이유: API마다 필수 변수 이름이 달라서 잘못 붙이면 HTTP 500이 늘어납니다.
    """
    url = str(url or "").strip()
    if not url:
        return ""

    key = str(api_key or "").strip()
    ymd = datetime.now().strftime("%Y%m%d")

    url = url.replace("{serviceKey}", key)
    url = url.replace("{today}", ymd)
    url = url.replace("{ymd}", ymd)

    sep = "&" if "?" in url else "?"
    extras = []
    low = url.lower()

    if "servicekey=" not in low and key:
        extras.append("serviceKey=" + key)
    if "pageno=" not in low:
        extras.append("pageNo=1")
    if "numofrows=" not in low:
        extras.append("numOfRows=100")
    if "resulttype=" not in low and "_type=" not in low and "type=" not in low:
        extras.append("resultType=json")

    if extras:
        url = url + sep + "&".join(extras)

    return url

def json_to_df(obj):
    if isinstance(obj, dict):
        for path in [["response","body","items","item"], ["response","body","item"], ["items","item"], ["data"], ["result"], ["body","items","item"]]:
            cur = obj
            ok = True
            for p in path:
                if isinstance(cur, dict) and p in cur:
                    cur = cur[p]
                else:
                    ok = False
                    break
            if ok:
                obj = cur
                break
    if isinstance(obj, dict):
        obj = [obj]
    return make_unique_columns(pd.json_normalize(obj))

def xml_to_df(text):
    root = ET.fromstring(text)
    rows = []
    for item in root.findall(".//item"):
        rows.append({c.tag: c.text for c in item})
    return make_unique_columns(pd.DataFrame(rows))

def fetch_api(url):
    if not str(url).strip():
        return pd.DataFrame(), ""
    if not api_key.strip() and "serviceKey=" not in str(url):
        return pd.DataFrame(), "API Key 미입력"
    try:
        req_url = build_api_url(url)
        res = requests.get(req_url, timeout=15)
        if res.status_code != 200:
            return pd.DataFrame(), f"HTTP {res.status_code}"
        txt = res.text.strip()
        if txt.startswith("{") or txt.startswith("[") or "json" in res.headers.get("content-type", ""):
            return json_to_df(res.json()), ""
        return xml_to_df(txt), ""
    except Exception as e:
        return pd.DataFrame(), str(e)

def fetch_env():
    env = {"weather":"맑음", "track":"양호", "sand":"보통", "wind":"없음", "source":"기본", "precip":0, "wind_speed":0}
    if auto_weather:
        coords = {"서울":(37.4438,127.0165), "부산경남":(35.1545,128.8782), "제주":(33.4097,126.3934)}
        lat, lon = coords[track_place]
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation,weather_code,wind_speed_10m&timezone=Asia%2FSeoul"
            cur = requests.get(url, timeout=8).json().get("current", {})
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
            env = {"weather":weather, "track":track, "sand":sand, "wind":wind, "source":"자동수집", "precip":precip, "wind_speed":wind_speed}
        except Exception:
            env["source"] = "자동실패"

    if manual_weather != "자동": env["weather"] = manual_weather
    if manual_track != "자동": env["track"] = manual_track
    if manual_sand != "자동": env["sand"] = manual_sand
    if manual_wind != "자동": env["wind"] = manual_wind
    return env

def sample_data():
    race = pd.DataFrame([{"경마장":track_place, "경주번호":"6", "출발시간":"16:05"}])
    horse = pd.DataFrame([
        {"마번":5,"마명":"마루스피드","최근순위":2,"승률":18,"복승률":42,"부담중량":55,"예상배당":9.2,"레이팅":78,"레이팅변화":4,"선행력":82,"추입력":70,"파워":78,"순발력":84,"습주로":72,"모래적응":80},
        {"마번":11,"마명":"그린파워","최근순위":3,"승률":15,"복승률":38,"부담중량":54.5,"예상배당":7.8,"레이팅":75,"레이팅변화":2,"선행력":75,"추입력":78,"파워":82,"순발력":77,"습주로":80,"모래적응":83},
        {"마번":2,"마명":"블루런","최근순위":4,"승률":12,"복승률":35,"부담중량":53,"예상배당":12.5,"레이팅":72,"레이팅변화":3,"선행력":70,"추입력":83,"파워":76,"순발력":79,"습주로":84,"모래적응":75},
        {"마번":7,"마명":"라스트킹","최근순위":5,"승률":10,"복승률":30,"부담중량":55.5,"예상배당":15.4,"레이팅":70,"레이팅변화":-1,"선행력":68,"추입력":72,"파워":85,"순발력":69,"습주로":86,"모래적응":88},
        {"마번":3,"마명":"해피로드","최근순위":6,"승률":8,"복승률":25,"부담중량":56,"예상배당":22,"레이팅":66,"레이팅변화":1,"선행력":65,"추입력":74,"파워":70,"순발력":73,"습주로":68,"모래적응":71}
    ])
    risk = pd.DataFrame([
        {"마번":5,"출발위험":0,"주행위험":1},
        {"마번":11,"출발위험":1,"주행위험":0},
        {"마번":2,"출발위험":0,"주행위험":0},
        {"마번":7,"출발위험":1,"주행위험":1},
        {"마번":3,"출발위험":2,"주행위험":1}
    ])
    return race, horse, risk


def normalize_meet_value(x):
    s = str(x or "").strip()
    if s in ["1", "서울", "SEOUL", "Seoul"]:
        return "서울"
    if s in ["2", "제주", "JEJU", "Jeju"]:
        return "제주"
    if s in ["3", "부산경남", "부경", "BUSAN", "Busan", "부산"]:
        return "부산경남"
    return s

def find_col_by_names(df, names):
    if df is None or df.empty:
        return None
    lower = {str(c).lower(): c for c in df.columns}
    for n in names:
        if n.lower() in lower:
            return lower[n.lower()]
    for c in df.columns:
        cl = str(c).lower()
        for n in names:
            if n.lower() in cl:
                return c
    return None

def soft_filter_one_api(df, key="api"):
    """
    선택 경주 필터는 기본적으로 부드럽게 적용합니다.
    엄격 필터를 켠 경우에만 rcDate/meet/rcNo가 정확히 맞는 행만 남깁니다.
    단, 필터 후 데이터가 완전히 비면 원본을 유지합니다.
    """
    if df is None or df.empty:
        return df

    try:
        strict = bool(strict_race_filter)
    except Exception:
        strict = False

    if not strict:
        return df

    d = df.copy()
    original = d.copy()

    desired_date = str(target_date or datetime.now().strftime("%Y%m%d")).replace("-", "").strip()
    desired_meet = normalize_meet_value(track_place)
    desired_rc = int(target_rc_no)

    date_col = find_col_by_names(d, ["rcDate", "raceDate", "meetDate", "date", "ymd"])
    meet_col = find_col_by_names(d, ["meet", "meetCd", "rcourse", "경마장"])
    rc_col = find_col_by_names(d, ["rcNo", "raceNo", "경주번호"])

    try:
        if date_col:
            ds = d[date_col].astype(str).str.replace("-", "", regex=False).str.strip()
            d = d[ds == desired_date]
    except Exception:
        pass

    try:
        if meet_col:
            ms = d[meet_col].apply(normalize_meet_value)
            d = d[ms == desired_meet]
    except Exception:
        pass

    try:
        if rc_col:
            rs = pd.to_numeric(d[rc_col], errors="coerce")
            d = d[rs == desired_rc]
    except Exception:
        pass

    # 너무 많이 걸러져 비면 원본 유지
    if d.empty:
        return original
    return d

def get_data():
    urls = {
        "race":race_url,
        "entry":entry_url,
        "horse":horse_url,
        "body":body_url,
        "gear":gear_url,
        "rating":rating_url,
        "odds":odds_url,
        "today_odds":today_odds_url,
        "result_detail":result_detail_url,
        "race_record":race_record_url,
        "start_exam":start_exam_url,
        "judge":judge_url,
        "jockey_change":jockey_change_url,
        "weather_alert":weather_alert_url,
        "corner_pace":corner_pace_url,
        "popularity":popularity_url,
        "first_odds":first_odds_url,
        "second_odds":second_odds_url,
        "third_odds":third_odds_url,
    }
    data = {}
    errors = []
    for name, url in urls.items():
        df, err = fetch_api(url)
        df = soft_filter_one_api(df, name)
        data[name] = df
        if err:
            errors.append(f"{name}:{err}")

    if use_sample and data.get("entry", pd.DataFrame()).empty and data.get("horse", pd.DataFrame()).empty:
        race, horse, risk = sample_data()
        data["race"] = race
        data["entry"] = horse
        data["horse"] = horse
        data["start_exam"] = risk

    return data, fetch_env(), errors





def horse_no_col(df):
    """
    실제 구매용 마번 컬럼만 찾습니다.
    age, rcNo, meet, rating 같은 숫자 컬럼은 마번으로 사용하지 않습니다.
    """
    if df.empty:
        return None

    exact_priority = [
        "chulNo", "chulno", "chul_no", "chulNum", "entryNo",
        "출전번호", "출전마번", "마번"
    ]

    for key in exact_priority:
        for c in df.columns:
            if str(c).lower() == key.lower():
                vals = pd.to_numeric(df[c], errors="coerce")
                if vals.between(1, 30, inclusive="both").sum() > 0:
                    return c

    for c in df.columns:
        cl = str(c).lower()
        if any(k in cl for k in ["chul", "출전", "마번"]):
            vals = pd.to_numeric(df[c], errors="coerce")
            if vals.between(1, 30, inclusive="both").sum() > 0:
                return c

    return None

def normalize_horse(df):
    if df.empty:
        return df
    d = df.copy()
    c = horse_no_col(d)

    if c:
        d["마번"] = pd.to_numeric(d[c], errors="coerce")

    # 0/고유번호/결측 제거 가능하도록 NaN 처리
    if "마번" in d.columns:
        d["마번"] = pd.to_numeric(d["마번"], errors="coerce")
        d.loc[~d["마번"].between(1, 30, inclusive="both"), "마번"] = pd.NA

    return d

def make_unique_columns(df):
    """
    API마다 같은 컬럼명이 반복될 때 pandas merge 오류를 막기 위해
    중복 컬럼명을 자동으로 고유하게 바꿉니다.
    """
    if df.empty:
        return df
    cols = []
    seen = {}
    for c in df.columns:
        c = str(c)
        if c not in seen:
            seen[c] = 0
            cols.append(c)
        else:
            seen[c] += 1
            cols.append(f"{c}_{seen[c]}")
    df = df.copy()
    df.columns = cols
    return df

def merge_horse(base, df, source_name="api"):
    """
    여러 API 데이터를 마번 기준으로 합칩니다.
    겹치는 컬럼은 source_name을 붙여서 MergeError를 방지합니다.
    """
    if base.empty or df.empty:
        return base

    base = make_unique_columns(base.copy())
    d = make_unique_columns(df.copy())

    base = normalize_horse(base)
    d = normalize_horse(d)

    if "마번" not in base.columns or "마번" not in d.columns:
        return base

    try:
        d = d.drop_duplicates(subset=["마번"], keep="first")
    except Exception:
        pass

    rename_map = {}
    for c in d.columns:
        if c != "마번" and c in base.columns:
            rename_map[c] = f"{c}_{source_name}"
    if rename_map:
        d = d.rename(columns=rename_map)

    try:
        return base.merge(d, on="마번", how="left")
    except Exception:
        return base

def num(df, names, default):
    for c in names:
        if c in df.columns:
            return pd.to_numeric(df[c], errors="coerce").fillna(default)
    return pd.Series([default] * len(df), index=df.index)

def budget_status():
    df = read_table(RESULT_FILE)
    if df.empty:
        return {"today_bet":0, "today_profit":0, "total_profit":0, "entries":0, "locked":False, "reason":"정상"}
    if "저장시각" in df.columns:
        df["날짜"] = pd.to_datetime(df["저장시각"], errors="coerce").dt.strftime("%Y-%m-%d")
    else:
        df["날짜"] = ""
    for c in ["투입금", "환급금"]:
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
    return {"today_bet":today_bet, "today_profit":today_profit, "total_profit":total_profit, "entries":entries, "locked":locked, "reason":reason}


def current_race_ready(result):
    """
    현재 경주번호/출발시간이 비어 있거나 조합이 이상하면 실전 추천/저장을 막습니다.
    """
    if not result:
        return False
    rc = str(result.get("경주번호", "")).strip()
    combo = str(result.get("공격삼쌍승", "")).strip()
    if rc in ["", "-", "nan", "None"]:
        return False
    parts = [p.strip() for p in combo.replace("/", "-").split("-")]
    if len(parts) != 3:
        return False
    try:
        nums = [int(p) for p in parts]
        # 일반 경주 마번 범위 안전장치. 15번 이상은 데이터 섞임 가능성으로 관망 처리.
        if not all(1 <= n <= 14 for n in nums):
            return False
    except Exception:
        return False
    return True

def env_bonus(row, env):
    front = float(row.get("선행력", 70))
    late = float(row.get("추입력", 70))
    power = float(row.get("파워", 70))
    speed = float(row.get("순발력", 70))
    wet = float(row.get("습주로", 70))
    sandfit = float(row.get("모래적응", 70))
    b = 0
    if env["weather"] in ["비", "눈"] or env["track"] in ["다습", "포화", "불량"]:
        b += (wet - 70) * 0.13 + (power - 70) * 0.08
    else:
        b += (speed - 70) * 0.10 + (front - 70) * 0.06
    if env["sand"] == "무거움":
        b += (sandfit - 70) * 0.12
    if env["wind"] == "맞바람":
        b += (late - 70) * 0.07 - (front - 75) * 0.04
    if distance_type == "단거리":
        b += (speed - 70) * 0.09 + (front - 70) * 0.08
    elif distance_type == "장거리":
        b += (power - 70) * 0.08 + (late - 70) * 0.07
    return round(b, 1)




def build_candidate_base_from_all(data):
    """
    entry에 chulNo가 없을 때, 신뢰 가능한 chulNo 소스만 모아 출전마 후보표를 만듭니다.
    horse 기본정보나 age/rcNo는 마번 기준표로 쓰지 않습니다.
    """
    priority_keys = ["body", "gear", "today_odds", "first_odds", "second_odds", "third_odds", "odds", "corner_pace"]
    nums = set()
    names = {}

    for key in priority_keys:
        df = data.get(key, pd.DataFrame())
        if df is None or df.empty:
            continue

        no_col = horse_no_col(df)
        if not no_col:
            continue

        tmp = df.copy()
        tmp["_tmp_no"] = pd.to_numeric(tmp[no_col], errors="coerce")
        tmp = tmp[tmp["_tmp_no"].between(1, 30, inclusive="both")]

        for _, r in tmp.iterrows():
            n = int(r["_tmp_no"])
            nums.add(n)
            for name_col in ["hrName", "마명", "horseName", "hr_name"]:
                if name_col in tmp.columns and pd.notna(r.get(name_col, None)):
                    names[n] = str(r.get(name_col))
                    break

    if len(nums) >= 3:
        return pd.DataFrame([{"마번": n, "마명": names.get(n, f"{n}번")} for n in sorted(nums)])

    return pd.DataFrame()

def analyze(data, env):
    base = normalize_horse(data.get("entry", pd.DataFrame()))
    if not base.empty and "마번" in base.columns:
        base = base[pd.to_numeric(base["마번"], errors="coerce").between(1, 30, inclusive="both")].copy()

    if base.empty:
        base = build_candidate_base_from_all(data)

    if base.empty:
        return pd.DataFrame(), {
            "경마장": track_place,
            "경주번호": "-",
            "출발시간": "-",
            "판정": "관망",
            "공격삼쌍승": "출전마 번호 인식 실패",
            "방어삼복승": "-",
            "보조삼쌍승": "-",
            "놓치기아까운1": "",
            "놓치기아까운2": "",
            "예상배당": 0,
            "신뢰도": 0,
            "추천금액": 0,
            "오늘투입": int(budget_status().get("today_bet",0)),
            "오늘손익": int(budget_status().get("today_profit",0)),
            "누적손익": int(budget_status().get("total_profit",0)),
            "오늘진입": int(budget_status().get("entries",0)),
            "자금상태": "출전마 번호 인식 실패",
            "기상특보위험": 0,
        }, []

    for key in ["horse","body","gear","rating","odds","today_odds","start_exam","judge","jockey_change","corner_pace","popularity","first_odds","second_odds","third_odds"]:
        base = merge_horse(base, data.get(key, pd.DataFrame()), key)

    if "마번" not in base.columns:
        base["마번"] = range(1, len(base) + 1)

    base["마번"] = pd.to_numeric(base["마번"], errors="coerce")
    base = base[base["마번"].between(1, 30, inclusive="both")].copy()
    base["마번"] = base["마번"].astype(int)
    base = base.drop_duplicates(subset=["마번"], keep="first")

    if base.empty or len(base["마번"].unique()) < 3:
        return pd.DataFrame(), {
            "경마장": track_place,
            "경주번호": "-",
            "출발시간": "-",
            "판정": "관망",
            "공격삼쌍승": "출전마 3두 이상 필요",
            "방어삼복승": "-",
            "보조삼쌍승": "-",
            "놓치기아까운1": "",
            "놓치기아까운2": "",
            "예상배당": 0,
            "신뢰도": 0,
            "추천금액": 0,
            "오늘투입": int(budget_status().get("today_bet",0)),
            "오늘손익": int(budget_status().get("today_profit",0)),
            "누적손익": int(budget_status().get("total_profit",0)),
            "오늘진입": int(budget_status().get("entries",0)),
            "자금상태": "출전마 번호 부족",
            "기상특보위험": 0,
        }, []

    h = base.copy()

    recent = num(h, ["최근순위", "최근성적", "rank", "ord", "착순"], 5)
    win = num(h, ["승률", "winRate"], 10)
    place = num(h, ["복승률", "placeRate"], 25)
    rating = num(h, ["레이팅", "rating", "rt"], 65)
    delta = num(h, ["레이팅변화", "ratingDelta"], 0)
    weight = num(h, ["부담중량", "weight", "wgBudam"], 55)
    odds = num(h, ["예상배당", "배당", "odds", "winOdds", "단승배당", "확정배당률"], 12)
    srisk = num(h, ["출발위험", "startRisk"], 0)
    rrisk = num(h, ["주행위험", "runRisk"], 0)
    corner_rank = num(h, ["코너순위", "cornerRank", "passRank", "통과순위", "코너통과순위"], 5)
    late_gain = num(h, ["4코너상승", "cornerGain", "추입상승", "순위상승"], 0)
    pace_fast = num(h, ["주로빠르기", "trackSpeed", "paceSpeed", "빠르기"], 0)
    popularity = num(h, ["인기", "popularity", "인기순위", "인기투표순위"], 5)

    h["환경보정"] = h.apply(lambda r: env_bonus(r, env), axis=1)
    h["코너보정"] = (10 - corner_rank.clip(1, 10)) * 0.9 + late_gain.clip(-5, 5) * 1.2 + pace_fast.clip(-5, 5) * 0.7
    h["인기보정"] = (10 - popularity.clip(1, 10)) * 0.55

    h["최종점수"] = (
        (10 - recent.clip(1, 10)) * weights["recent"]
        + win.clip(0, 50) * weights["win_rate"]
        + place.clip(0, 80) * weights["place_rate"]
        + (rating.clip(40, 100) - 40) * weights["rating"]
        + delta.clip(-10, 10) * weights["rating_delta"]
        + odds.clip(1, 100).apply(lambda x: 12 if 6 <= x <= 25 else (7 if 25 < x <= 45 else 2)) * weights["odds_value"]
        + h["환경보정"] * weights["environment"]
        + h["코너보정"]
        + h["인기보정"]
        - (weight - 54).clip(lower=0) * weights["weight_penalty"]
        - (srisk * 2 + rrisk * 1.5) * weights["risk_penalty"]
    )

    weather_alert_df = data.get("weather_alert", pd.DataFrame())
    alert_risk = 0
    if not weather_alert_df.empty:
        alert_text = " ".join(weather_alert_df.astype(str).head(20).values.flatten().tolist())
        if any(x in alert_text for x in ["강풍","호우","대설","폭염","한파","주의보","경보"]):
            alert_risk = 1

    volatility = 5.5
    if env["weather"] in ["비", "눈"]:
        volatility += 1.8
    if env["wind"] in ["맞바람", "측풍"]:
        volatility += 0.8
    if alert_risk:
        volatility += 1.2
    if risk_mode == "안전형":
        volatility *= 0.9
    elif risk_mode == "공격형":
        volatility *= 1.15

    nums = [int(x) for x in h["마번"].tolist() if pd.notna(x) and 1 <= int(x) <= 30]
    h = h[pd.to_numeric(h["마번"], errors="coerce").between(1, 30, inclusive="both")].copy()
    scores = h["최종점수"].tolist()
    counter = Counter()
    random.seed(42)
    for _ in range(sim_count):
        noisy = [(n, s + random.gauss(0, volatility)) for n, s in zip(nums, scores)]
        top = tuple(str(x[0]) for x in sorted(noisy, key=lambda x: x[1], reverse=True)[:3])
        counter[top] += 1

    combos = counter.most_common(10)
    top = combos[0][0]
    confidence = min(95, max(35, round(combos[0][1] / sim_count * 100 + 48)))

    if confidence >= 75:
        decision = "소액 공격"
    elif confidence >= 62:
        decision = "소액 가능"
    else:
        decision = "관망"

    b = budget_status()
    remaining = max(0, float(daily_budget) - b["today_bet"])
    unlocked = b["total_profit"] >= profit_unlock or bankroll >= profit_unlock

    if b["locked"] or remaining <= 0:
        decision = "투자금지"
        amount = 0
    elif decision == "관망":
        amount = 0
    else:
        amount = int(min(10000 if unlocked else unit_bet, remaining))

    race = data.get("race", pd.DataFrame()).iloc[0].to_dict() if not data.get("race", pd.DataFrame()).empty else {}
    result = {
        "경마장": race.get("경마장", track_place),
        "경주번호": race.get("경주번호", "-"),
        "출발시간": race.get("출발시간", "-"),
        "판정": decision,
        "공격삼쌍승": " - ".join(top),
        "방어삼복승": " / ".join(top),
        "보조삼쌍승": " - ".join(combos[1][0]) if len(combos) > 1 else " - ".join(top),
        "놓치기아까운1": " - ".join(combos[2][0]) if len(combos) > 2 else "",
        "놓치기아까운2": " - ".join(combos[3][0]) if len(combos) > 3 else "",
        "예상배당": round(float(odds.head(3).sum() * 0.9), 1) if len(odds) >= 3 else 46.8,
        "신뢰도": confidence,
        "추천금액": amount,
        "오늘투입": int(b["today_bet"]),
        "오늘손익": int(b["today_profit"]),
        "누적손익": int(b["total_profit"]),
        "오늘진입": int(b["entries"]),
        "자금상태": b["reason"],
        "기상특보위험": alert_risk,
    }

    combo_rows = [{"조합":" - ".join(k), "반복횟수":v, "비율":round(v / sim_count * 100, 1)} for k, v in combos]
    return h.sort_values("최종점수", ascending=False), result, combo_rows

c1, c2 = st.columns(2)
if c1.button("데이터 불러오기", use_container_width=True):
    st.session_state["data"], st.session_state["env"], st.session_state["errors"] = get_data()
if c2.button("시뮬레이션", use_container_width=True):
    st.session_state["data"], st.session_state["env"], st.session_state["errors"] = get_data()

if "data" not in st.session_state:
    st.session_state["data"], st.session_state["env"], st.session_state["errors"] = get_data()

data = st.session_state["data"]
env = st.session_state["env"]
errors = st.session_state["errors"]

score_df, result, combos = analyze(data, env)
if result and not current_race_ready(result):
    result["판정"] = "관망"
    result["추천금액"] = 0
    result["신뢰도"] = min(int(result.get("신뢰도", 0)), 49)
    result["자금상태"] = "현재 경주정보 부족 / 데이터 섞임 방지"

try:
    entry_candidate = horse_no_col(data.get("entry", pd.DataFrame()))
    if not entry_candidate:
        st.info("마번 기준: entry에 chulNo가 없어 body/gear/today_odds의 chulNo를 우선 사용합니다.")
except Exception:
    pass


def is_valid_combo_text(x):
    s = str(x or "")
    parts = [p.strip() for p in s.replace("/", "-").split("-")]
    if len(parts) != 3:
        return False
    try:
        nums = [int(p) for p in parts]
        return all(1 <= n <= 30 for n in nums)
    except Exception:
        return False

if auto_save_reco and result and current_race_ready(result) and is_valid_combo_text(result.get("공격삼쌍승","")) and int(result.get("신뢰도",0)) > 0:
    append_table(RECO_FILE, {
        "저장시각":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "날짜":target_date if "target_date" in globals() else today(),
        **result,
        "날씨":env.get("weather",""),
        "주로":env.get("track",""),
        "모래":env.get("sand",""),
        "바람":env.get("wind","")
    })

rows = sum(len(v) for v in data.values())
reco_df = read_table(RECO_FILE)
compare_df = read_table(COMPARE_FILE)

st.info(f"선택 기준: {target_date} · {track_place} · {int(target_rc_no)}R · 엄격필터={strict_race_filter}")
m1, m2, m3 = st.columns(3)
st.caption("URL 예시는 API Key를 숨겨 표시합니다. 과거 캡처에 키가 보였다면 재발급을 권장합니다.")
m1.metric("연결 데이터", rows)
m2.metric("추천 저장", len(reco_df))
m3.metric("비교 저장", len(compare_df))

if errors:
    st.warning(f"보조 API 오류 {len(errors)}개. 핵심 데이터가 있으면 분석은 계속됩니다.")
    with st.expander("오류 상세 보기"):
        st.write(errors)

st.subheader("최종 판단")
st.success(result.get("판정", "대기"))

a, b, c = st.columns(3)
a.metric("신뢰도", f"{result.get('신뢰도', 0)}%")
b.metric("추천금액", f"{result.get('추천금액', 0):,}원")
c.metric("오늘진입", f"{result.get('오늘진입', 0)} / {int(daily_entries_limit)}")

st.info(f"{result.get('경마장','-')} {result.get('경주번호','-')}R · 출발 {result.get('출발시간','-')}")

st.markdown("### 공격 삼쌍승")
st.markdown(f"## {result.get('공격삼쌍승','-')}")
st.caption(f"예상배당: {result.get('예상배당','-')}배")

st.markdown("### 손실 방어 조합")
st.write(f"방어 삼복승: **{result.get('방어삼복승','-')}**")
st.write(f"보조 삼쌍승: **{result.get('보조삼쌍승','-')}**")
st.write(f"놓치기 아까운 삼쌍승: **{result.get('놓치기아까운1','')}** / **{result.get('놓치기아까운2','')}**")

st.markdown("### 자금 잠금 규칙")
st.write(f"오늘 투입: **{result.get('오늘투입',0):,}원 / {int(daily_budget):,}원**")
st.write(f"오늘 손익: **{result.get('오늘손익',0):,}원**")
st.write(f"누적 손익: **{result.get('누적손익',0):,}원**")
st.write(f"상태: **{result.get('자금상태','-')}**")
st.write(f"기상특보 위험: **{result.get('기상특보위험',0)}**")

st.markdown("### 환경 반영")
e1, e2, e3 = st.columns(3)
e1.metric("날씨", env.get("weather", "-"))
e2.metric("주로", env.get("track", "-"))
e3.metric("모래", env.get("sand", "-"))

st.link_button("KRA 공식 바로가기", kra_url, use_container_width=True)
st.caption("자동구매 아님 · 공식 화면 이동 · 수익 보장 아님 · 손실 제한/기록학습")

with st.expander("결과 입력 / 예상비교 / 자가학습"):
    actual_combo = st.text_input("실제 삼쌍 1-2-3", placeholder="예: 5-11-2")
    actual_trio = st.text_input("실제 삼복 1~3착", placeholder="예: 5/11/2")
    bet_amount = st.number_input("투입금", min_value=0, value=int(result.get("추천금액",0)), step=100)
    return_amount = st.number_input("환급금", min_value=0, value=0, step=100)
    memo = st.text_input("메모")
    if st.button("결과 저장하고 AI 학습", use_container_width=True):
        pred = result.get("공격삼쌍승","").replace(" ","")
        actual = actual_combo.replace(" ","")
        trio_pred = set(result.get("방어삼복승","").replace(" ","").split("/"))
        trio_actual = set((actual_trio or actual_combo).replace(" ","").replace("-","/").split("/"))
        tri_hit = int(pred == actual)
        trio_hit = int(trio_pred == trio_actual)
        roi = ((return_amount - bet_amount) / bet_amount) if bet_amount > 0 else 0
        if tri_hit:
            typ = "삼쌍승 적중"
        elif trio_hit:
            typ = "삼복승 방어"
        elif return_amount > 0:
            typ = "부분환급"
        else:
            typ = "미적중"
        rec = {
            "저장시각":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "날짜":today(),
            **result,
            "투입금":bet_amount,
            "환급금":return_amount,
            "수익률":roi,
            "실제삼쌍":actual_combo,
            "실제삼복":actual_trio,
            "분석결과":typ,
            "메모":memo
        }
        append_table(RESULT_FILE, rec)
        append_table(COMPARE_FILE, rec)
        st.success(f"저장 완료: {typ}")

with st.expander("숨겨진 분석 / 저장 데이터"):
    
    st.subheader("API 원본 컬럼 진단")
    debug_keys = ["race", "entry", "horse", "body", "gear", "rating", "odds", "today_odds", "corner_pace"]
    rows = []
    for k in debug_keys:
        df = data.get(k, pd.DataFrame())
        if df is not None and not df.empty:
            rows.append({
                "API": k,
                "행수": len(df),
                "컬럼수": len(df.columns),
                "마번후보": str(horse_no_col(df)),
                "컬럼목록": ", ".join([str(c) for c in list(df.columns)[:25]])
            })
        else:
            rows.append({"API": k, "행수": 0, "컬럼수": 0, "마번후보": "", "컬럼목록": ""})
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    st.subheader("2번 출전 등록말 원본 미리보기")
    if not data.get("entry", pd.DataFrame()).empty:
        st.dataframe(data.get("entry", pd.DataFrame()).head(20), use_container_width=True)
    else:
        st.write("entry 데이터 없음")

    st.subheader("API 연결 데이터 행수")
    st.dataframe(pd.DataFrame([{"API":k, "행수":len(v)} for k, v in data.items()]), use_container_width=True)

    st.subheader("말별 점수표")
    st.dataframe(score_df, use_container_width=True)

    st.subheader("삼쌍승 시뮬레이션")
    st.dataframe(pd.DataFrame(combos), use_container_width=True)

    st.subheader("과거 추천 로그")
    st.dataframe(read_table(RECO_FILE).tail(100), use_container_width=True)

    st.subheader("과거 예상 vs 실제 비교 로그")
    st.dataframe(read_table(COMPARE_FILE).tail(100), use_container_width=True)

    st.subheader("자동 완성된 URL 예시 — API Key 숨김")
    examples = []
    for name, url in {
        "race":race_url,
        "entry":entry_url,
        "horse":horse_url,
        "rating":rating_url,
        "today_odds":today_odds_url,
        "corner_pace":corner_pace_url,
    }.items():
        examples.append({"API":name, "요청URL":mask_secret_url(build_api_url(url))})
    st.dataframe(pd.DataFrame(examples), use_container_width=True)
