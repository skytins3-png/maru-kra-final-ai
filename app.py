
import json
import re
import random
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from itertools import permutations

import pandas as pd
import requests
import streamlit as st
import xml.etree.ElementTree as ET


st.set_page_config(
    page_title="MARU KRA CLEAN REBUILD",
    layout="wide",
    initial_sidebar_state="expanded",
)

KST = ZoneInfo("Asia/Seoul")
BASE_DIR = Path(".")
SETTINGS_FILE = BASE_DIR / "maru_settings.json"
RECO_FILE = BASE_DIR / "recommendations.csv"
COMPARE_FILE = BASE_DIR / "comparisons.csv"
RESULT_FILE = BASE_DIR / "results.csv"

API_ITEMS = [
    ("race", "race_url", "1. 경주정보 URL"),
    ("entry", "entry_url", "2. 출전등록말 URL"),
    ("horse", "horse_url", "3. 경주마정보 URL"),
    ("body", "body_url", "4. 출전마 체중 URL"),
    ("gear", "gear_url", "5. 장구/폐출혈 URL"),
    ("rating", "rating_url", "6. 레이팅 URL"),
    ("odds", "odds_url", "7. 배당/매출 URL"),
    ("today_odds", "today_odds_url", "8. 시행당일 배당 URL"),
    ("result_detail", "result_detail_url", "9. AI 경주결과상세 URL"),
    ("race_record", "race_record_url", "10. 경주기록 URL"),
    ("start_exam", "start_exam_url", "11. 출발심사 URL"),
    ("judge", "judge_url", "12. 경주심판 URL"),
    ("jockey_change", "jockey_change_url", "13. 기수변경 URL"),
    ("weather_alert", "weather_alert_url", "14. 기상특보 URL"),
    ("corner_pace", "corner_pace_url", "15. 코너/주로빠르기 URL"),
    ("popularity", "popularity_url", "16. 인기투표 URL"),
    ("first_odds", "first_odds_url", "17. 1착마 적중승식 URL"),
    ("second_odds", "second_odds_url", "18. 2착마 적중승식 URL"),
    ("third_odds", "third_odds_url", "19. 3착마 적중승식 URL"),
]


def now_kst():
    return datetime.now(KST)


def today():
    return now_kst().strftime("%Y%m%d")


def now_str():
    return now_kst().strftime("%Y-%m-%d %H:%M:%S")


def load_json(path, default=None):
    default = default if default is not None else {}
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def save_json(path, payload):
    try:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def secret_get(key, default=""):
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
    return default


def setting_get(settings, key, default=""):
    if key in settings and settings.get(key) not in [None, ""]:
        return settings.get(key)
    if key.upper() in settings and settings.get(key.upper()) not in [None, ""]:
        return settings.get(key.upper())
    sec = secret_get(key, "")
    if sec:
        return sec
    return default


def mask_secret_url(url):
    s = str(url or "")
    s = re.sub(r"(serviceKey=)[^&]+", r"\1***", s)
    s = re.sub(r"(servicekey=)[^&]+", r"\1***", s)
    return s


def build_api_url(url, api_key):
    url = str(url or "").strip()
    if not url:
        return ""

    if "{serviceKey}" in url:
        url = url.replace("{serviceKey}", api_key)

    if "serviceKey=" not in url and "servicekey=" not in url.lower() and api_key:
        sep = "&" if "?" in url else "?"
        url += sep + "serviceKey=" + api_key

    # 기본 파라미터만 보강. rcDate/meet/rcNo는 강제로 붙이지 않음.
    lower = url.lower()
    defaults = {
        "pageNo": "1",
        "numOfRows": "100",
        "resultType": "json",
    }
    for k, v in defaults.items():
        if k.lower() + "=" not in lower:
            sep = "&" if "?" in url else "?"
            url += sep + f"{k}={v}"
            lower = url.lower()

    return url


def flatten_json(obj):
    rows = []

    def walk(x):
        if isinstance(x, list):
            for item in x:
                walk(item)
        elif isinstance(x, dict):
            # common public API response path
            if "item" in x:
                walk(x["item"])
            elif "items" in x:
                walk(x["items"])
            elif "body" in x:
                walk(x["body"])
            elif "response" in x:
                walk(x["response"])
            else:
                # a row-like dict
                if any(not isinstance(v, (dict, list)) for v in x.values()):
                    rows.append({k: v for k, v in x.items() if not isinstance(v, (dict, list))})
                for v in x.values():
                    if isinstance(v, (dict, list)):
                        walk(v)

    walk(obj)
    return rows


def parse_response(resp):
    text = resp.text.strip()
    if not text:
        return pd.DataFrame()

    # JSON
    try:
        obj = resp.json()
        rows = flatten_json(obj)
        return pd.DataFrame(rows)
    except Exception:
        pass

    # XML
    try:
        root = ET.fromstring(text)
        rows = []
        for item in root.iter("item"):
            row = {child.tag: child.text for child in list(item)}
            if row:
                rows.append(row)
        if rows:
            return pd.DataFrame(rows)

        # fallback: direct children
        row = {child.tag: child.text for child in list(root)}
        return pd.DataFrame([row]) if row else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def fetch_api(url, timeout=15):
    if not url:
        return pd.DataFrame(), ""
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code != 200:
            return pd.DataFrame(), f"HTTP {r.status_code}"
        df = parse_response(r)
        return df, ""
    except Exception as e:
        return pd.DataFrame(), str(e)


def normalize_meet(x):
    s = str(x or "").strip()
    if s in ["1", "서울", "SEOUL", "Seoul", "seoul"]:
        return "서울"
    if s in ["2", "제주", "JEJU", "Jeju", "jeju"]:
        return "제주"
    if s in ["3", "부산경남", "부경", "부산", "BUSAN", "Busan", "busan"]:
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


def filter_current_race(df, target_date, track_place, target_rc_no, strict=False):
    if df is None or df.empty:
        return df

    d = df.copy()
    original = d.copy()

    date_col = find_col(d, ["rcDate", "raceDate", "meetDate", "date", "ymd"])
    meet_col = find_col(d, ["meet", "meetCd", "rcourse", "경마장"])
    rc_col = find_col(d, ["rcNo", "raceNo", "경주번호"])

    try:
        if date_col:
            ds = d[date_col].astype(str).str.replace("-", "", regex=False).str.strip()
            d = d[ds == str(target_date).replace("-", "").strip()]
    except Exception:
        pass

    try:
        if meet_col:
            ms = d[meet_col].apply(normalize_meet)
            d = d[ms == normalize_meet(track_place)]
    except Exception:
        pass

    try:
        if rc_col:
            rs = pd.to_numeric(d[rc_col], errors="coerce")
            d = d[rs == int(target_rc_no)]
    except Exception:
        pass

    # strict면 빈 결과 그대로, 아니면 원본 유지
    if d.empty and not strict:
        return original
    return d


def chulno_col(df):
    if df is None or df.empty:
        return None
    allowed = ["chulNo", "chulno", "출전번호", "출전마번", "마번"]
    for c in df.columns:
        if str(c) in allowed or str(c).lower() in [a.lower() for a in allowed]:
            vals = pd.to_numeric(df[c], errors="coerce")
            if vals.between(1, 14, inclusive="both").sum() >= 3:
                return c
    return None


def valid_chulno_base(data):
    trusted = ["body", "gear", "today_odds"]
    nums = {}
    evidence = {}

    for key in trusted:
        df = data.get(key, pd.DataFrame())
        if df is None or df.empty:
            continue

        col = chulno_col(df)
        if not col:
            continue

        tmp = df.copy()
        tmp["_chulNo"] = pd.to_numeric(tmp[col], errors="coerce")
        tmp = tmp[tmp["_chulNo"].between(1, 14, inclusive="both")]

        for _, r in tmp.iterrows():
            n = int(r["_chulNo"])
            name = f"{n}번"
            for nc in ["hrName", "마명", "horseName", "rcName"]:
                if nc in tmp.columns and pd.notna(r.get(nc, None)) and str(r.get(nc)).strip():
                    name = str(r.get(nc)).strip()
                    break
            nums[n] = name
            evidence.setdefault(n, set()).add(key)

    rows = []
    for n in sorted(nums):
        ev = ",".join(sorted(evidence.get(n, [])))
        score = 50 + len(evidence.get(n, [])) * 5
        rows.append({"마번": n, "마명": nums[n], "점수": score, "근거": ev})
    return pd.DataFrame(rows)


def simulate_combos(score_df):
    if score_df is None or score_df.empty or len(score_df) < 3:
        return []

    ranked = score_df.sort_values("점수", ascending=False).head(8)
    nums = ranked["마번"].astype(int).tolist()
    score_map = dict(zip(ranked["마번"].astype(int), ranked["점수"]))

    rows = []
    for a, b, c in permutations(nums, 3):
        val = score_map.get(a, 0) * 0.5 + score_map.get(b, 0) * 0.3 + score_map.get(c, 0) * 0.2
        rows.append({"조합": f"{a}-{b}-{c}", "점수": round(val, 2)})

    rows = sorted(rows, key=lambda x: x["점수"], reverse=True)
    # 중복 너무 많지 않게 상위 10개
    return rows[:10]


def analyze(score_df, combos, env):
    result = {
        "판정": "관망",
        "신뢰도": 49,
        "추천금액": 0,
        "공격삼쌍승": "-",
        "방어삼복승": "-",
        "보조삼쌍승": "-",
        "예상배당": 0,
        "자금상태": "현재 경주 chulNo 부족 / 데이터 섞임 방지",
    }

    if score_df is None or score_df.empty or len(score_df) < 3 or not combos:
        return result

    top = combos[0]["조합"]
    confidence = min(70, 45 + len(score_df) * 2)
    result.update({
        "판정": "소액검토" if confidence >= 55 else "관망",
        "신뢰도": confidence,
        "추천금액": 1000 if confidence >= 60 else 0,
        "공격삼쌍승": top if confidence >= 55 else "-",
        "방어삼복승": top.replace("-", " / ") if confidence >= 55 else "-",
        "보조삼쌍승": combos[1]["조합"] if len(combos) > 1 and confidence >= 55 else "-",
        "예상배당": "변동",
        "자금상태": "소액/손실제한" if confidence >= 55 else "관망",
    })
    return result


def read_table(path):
    try:
        if path.exists():
            return pd.read_csv(path)
    except Exception:
        pass
    return pd.DataFrame()


def append_table(path, row):
    df = read_table(path)
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return df


def env_dict():
    return {
        "weather": globals().get("manual_weather", "흐림"),
        "track": globals().get("track_condition", "양호"),
        "sand": globals().get("sand_condition", "보통"),
        "wind": globals().get("wind_condition", "보통"),
        "alert": 0,
    }


def google_sheets_status():
    try:
        if "google_sheets" in st.secrets and ("SHEET_ID" in st.secrets["google_sheets"] or "sheet_id" in st.secrets["google_sheets"]):
            return "Google Sheets 허브 설정 있음"
    except Exception:
        pass
    return "Google Sheets 허브 미설정: 로컬 저장만 사용"


settings = load_json(SETTINGS_FILE, {})

st.title("🐎 MARU KRA AI — Clean Rebuild")
st.caption(f"한국시간 기준 날짜: {today()} / 현재시각: {now_str()}")
st.info("깨끗한 새 기본판: 사이드바 복구 · API 입력 · chulNo 전용 점수표 · 관망 안전장치")


# Sidebar
st.sidebar.title("🐎 MARU KRA 메뉴")
st.sidebar.caption("API 입력 / 경주 선택 / 환경 설정")

api_key = st.sidebar.text_input(
    "공공데이터 API Key",
    value=str(setting_get(settings, "api_key", secret_get("API_KEY", ""))),
    type="password"
)

st.sidebar.divider()
st.sidebar.subheader("분석 기준")
target_date = st.sidebar.text_input("분석 날짜", value=str(setting_get(settings, "target_date", today())))
track_place = st.sidebar.selectbox(
    "경마장",
    ["서울", "부산경남", "제주"],
    index=["서울", "부산경남", "제주"].index(str(setting_get(settings, "track_place", "서울"))) if str(setting_get(settings, "track_place", "서울")) in ["서울", "부산경남", "제주"] else 0
)
target_rc_no = st.sidebar.number_input(
    "경주번호",
    min_value=1,
    max_value=20,
    value=int(setting_get(settings, "target_rc_no", 1) or 1),
    step=1
)
strict_filter = st.sidebar.checkbox("선택 경주만 엄격 필터", value=False)

st.sidebar.divider()
st.sidebar.subheader("핵심 API 주소")
api_urls = {}
for api_name, key, label in API_ITEMS[:8]:
    api_urls[api_name] = st.sidebar.text_input(label, value=str(setting_get(settings, key, "")))

with st.sidebar.expander("보조 API 주소 9~19번", expanded=False):
    for api_name, key, label in API_ITEMS[8:]:
        api_urls[api_name] = st.text_input(label, value=str(setting_get(settings, key, "")))

st.sidebar.divider()
st.sidebar.subheader("환경/날씨 설정")
auto_weather = st.sidebar.checkbox("날씨/바람 자동수집", value=False, help="오류 방지를 위해 기본 OFF")
manual_weather = st.sidebar.selectbox("날씨", ["맑음", "흐림", "비", "눈", "안개"], index=1)
track_condition = st.sidebar.selectbox("주로", ["양호", "다습", "포화", "불량", "건조"], index=0)
sand_condition = st.sidebar.selectbox("모래", ["빠름", "보통", "무거움"], index=1)
wind_condition = st.sidebar.selectbox("바람", ["약함", "보통", "강함"], index=1)

st.sidebar.divider()
use_sample = st.sidebar.checkbox("샘플 데이터 사용", value=False, help="실전에서는 OFF")

payload = {
    "api_key": api_key,
    "target_date": target_date,
    "track_place": track_place,
    "target_rc_no": int(target_rc_no),
}
for api_name, key, label in API_ITEMS:
    payload[key] = api_urls.get(api_name, "")

if st.sidebar.button("API 저장", use_container_width=True):
    if save_json(SETTINGS_FILE, payload):
        st.sidebar.success("저장 완료")
    else:
        st.sidebar.error("저장 실패")

if st.sidebar.button("추천/비교 로그 초기화", use_container_width=True):
    for p in [RECO_FILE, COMPARE_FILE, RESULT_FILE]:
        try:
            if p.exists():
                p.unlink()
        except Exception:
            pass
    st.sidebar.warning("로그 초기화 완료")

if st.sidebar.button("API 설정 초기화", use_container_width=True):
    try:
        if SETTINGS_FILE.exists():
            SETTINGS_FILE.unlink()
        st.sidebar.warning("API 설정 초기화 완료")
    except Exception:
        st.sidebar.warning("초기화 시도 완료")


# main action
load_clicked = st.button("데이터 불러오기", use_container_width=True)

if "data" not in st.session_state:
    st.session_state["data"] = {}
    st.session_state["errors"] = []
    st.session_state["env"] = env_dict()

if load_clicked:
    data = {}
    errors = []
    for api_name, key, label in API_ITEMS:
        raw = api_urls.get(api_name, "")
        full_url = build_api_url(raw, api_key)
        df, err = fetch_api(full_url)
        df = filter_current_race(df, target_date, track_place, target_rc_no, strict=strict_filter)
        data[api_name] = df
        if err:
            errors.append(f"{api_name}: {err}")
    st.session_state["data"] = data
    st.session_state["errors"] = errors
    st.session_state["env"] = env_dict()

data = st.session_state["data"]
errors = st.session_state["errors"]
env = st.session_state["env"]

total_rows = sum(len(v) for v in data.values() if isinstance(v, pd.DataFrame))
score_df = valid_chulno_base(data)
combos = simulate_combos(score_df)
result = analyze(score_df, combos, env)

# Metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("연결 데이터", total_rows)
m2.metric("신뢰도", f"{result['신뢰도']}%")
m3.metric("추천금액", f"{result['추천금액']:,}원")
m4.metric("오늘진입", "0 / 3")

st.subheader("최종 판단")
if result["판정"] == "관망":
    st.warning("관망")
else:
    st.success(result["판정"])

c1, c2 = st.columns([1.2, 1])
with c1:
    st.subheader("공격 삼쌍승")
    st.markdown(f"## {result['공격삼쌍승']}")
    st.write(f"방어 삼복승: {result['방어삼복승']}")
    st.write(f"보조 삼쌍승: {result['보조삼쌍승']}")
    st.write(f"상태: {result['자금상태']}")

with c2:
    st.subheader("환경 반영")
    st.write(f"날씨: {env.get('weather')}")
    st.write(f"주로: {env.get('track')}")
    st.write(f"모래: {env.get('sand')}")
    st.write(f"바람: {env.get('wind')}")
    st.caption("자동구매 아님 · 공식 화면 이동/수동 판단용 · 수익 보장 아님")

if errors:
    st.warning(f"보조 API 오류 {len(errors)}개. 핵심 데이터가 있으면 분석은 계속됩니다.")
    with st.expander("오류 상세 보기"):
        st.write(errors)

st.divider()
st.subheader("API 연결 데이터 행수")
api_rows = []
for api_name, key, label in API_ITEMS:
    df = data.get(api_name, pd.DataFrame())
    api_rows.append({
        "API": api_name,
        "행수": len(df) if isinstance(df, pd.DataFrame) else 0,
        "컬럼수": len(df.columns) if isinstance(df, pd.DataFrame) and not df.empty else 0,
        "chulNo컬럼": chulno_col(df) if isinstance(df, pd.DataFrame) and not df.empty else "",
    })
st.dataframe(pd.DataFrame(api_rows), use_container_width=True, height=360)

st.subheader("말별 점수표 — chulNo 기준")
st.caption("body / gear / today_odds의 chulNo만 사용합니다. enNo/hrNo/chaksun/age는 마번으로 쓰지 않습니다.")
st.dataframe(score_df, use_container_width=True, height=360)

st.subheader("삼쌍승 시뮬레이션")
st.dataframe(pd.DataFrame(combos), use_container_width=True, height=360)

with st.expander("API 원본 컬럼 진단"):
    diag = []
    for api_name, key, label in API_ITEMS:
        df = data.get(api_name, pd.DataFrame())
        diag.append({
            "API": api_name,
            "행수": len(df) if isinstance(df, pd.DataFrame) else 0,
            "컬럼목록": ", ".join(map(str, df.columns[:30])) if isinstance(df, pd.DataFrame) and not df.empty else "",
        })
    st.dataframe(pd.DataFrame(diag), use_container_width=True)

with st.expander("자동 완성된 URL 예시 — API Key 숨김"):
    examples = []
    for api_name, key, label in API_ITEMS:
        raw = api_urls.get(api_name, "")
        if raw:
            examples.append({"API": api_name, "요청URL": mask_secret_url(build_api_url(raw, api_key))})
    st.dataframe(pd.DataFrame(examples), use_container_width=True)

st.divider()
st.subheader("허브 상태")
st.info(google_sheets_status())

st.subheader("과거 추천 로그")
st.dataframe(read_table(RECO_FILE), use_container_width=True, height=240)

st.subheader("과거 예상 vs 실제 비교 로그")
st.dataframe(read_table(COMPARE_FILE), use_container_width=True, height=240)
