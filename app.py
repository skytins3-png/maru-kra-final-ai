
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from itertools import permutations
import xml.etree.ElementTree as ET

import pandas as pd
import requests
import streamlit as st


st.set_page_config(
    page_title="MARU KRA FULL 19API REALTIME",
    layout="wide",
    initial_sidebar_state="expanded",
)

KST = ZoneInfo("Asia/Seoul")
SETTINGS_FILE = Path("maru_full19_settings.json")
RECO_FILE = Path("maru_recommendations.csv")
COMPARE_FILE = Path("maru_comparisons.csv")
RESULT_FILE = Path("maru_results.csv")


API_ITEMS = [
    ("race", "race_url", "1. 경주정보"),
    ("entry", "entry_url", "2. 출전등록말"),
    ("horse", "horse_url", "3. 경주마정보"),
    ("body", "body_url", "4. 출전마 체중"),
    ("gear", "gear_url", "5. 장구/폐출혈"),
    ("rating", "rating_url", "6. 레이팅"),
    ("odds", "odds_url", "7. 배당/매출"),
    ("today_odds", "today_odds_url", "8. 시행당일 배당"),
    ("result_detail", "result_detail_url", "9. AI 경주결과상세"),
    ("race_record", "race_record_url", "10. 경주기록/요약성적"),
    ("start_exam", "start_exam_url", "11. 출발심사"),
    ("judge", "judge_url", "12. 경주심판"),
    ("jockey_change", "jockey_change_url", "13. 기수변경"),
    ("weather_alert", "weather_alert_url", "14. 기상특보"),
    ("corner_pace", "corner_pace_url", "15. 코너별 통과/주로빠르기"),
    ("popularity", "popularity_url", "16. 인기투표"),
    ("first_odds", "first_odds_url", "17. 1착마 적중승식"),
    ("second_odds", "second_odds_url", "18. 2착마 적중승식"),
    ("third_odds", "third_odds_url", "19. 3착마 적중승식"),
]


def now_kst():
    return datetime.now(KST)


def today_ymd():
    return now_kst().strftime("%Y%m%d")


def now_text():
    return now_kst().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path, default=None):
    default = default if default is not None else {}
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_secret(key, default=""):
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


def get_setting(settings, key, default=""):
    if key in settings and settings.get(key) not in [None, ""]:
        return settings.get(key)
    if key.upper() in settings and settings.get(key.upper()) not in [None, ""]:
        return settings.get(key.upper())
    sec = get_secret(key, "")
    if sec:
        return sec
    return default


def mask_url(url):
    s = str(url or "")
    s = re.sub(r"(serviceKey=)[^&]+", r"\1***", s, flags=re.I)
    return s


def build_url(raw_url, api_key, target_date, track_place, target_rc_no, add_filter_params=False):
    url = str(raw_url or "").strip()
    if not url:
        return ""

    if "{serviceKey}" in url:
        url = url.replace("{serviceKey}", api_key)

    if "servicekey=" not in url.lower() and api_key:
        sep = "&" if "?" in url else "?"
        url += sep + "serviceKey=" + api_key

    params = {
        "pageNo": "1",
        "numOfRows": "100",
        "resultType": "json",
    }

    # 실시간 API 중 일부는 rcDate/meet/rcNo 파라미터가 필요하고,
    # 일부는 붙이면 500이 나므로 기본은 OFF. 사용자가 켤 수 있음.
    if add_filter_params:
        meet_code = {"서울": "1", "제주": "2", "부산경남": "3"}.get(track_place, "1")
        params.update({
            "rcDate": str(target_date),
            "meet": meet_code,
            "rcNo": str(int(target_rc_no)),
        })

    lower = url.lower()
    for k, v in params.items():
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
            # 공공데이터 표준 구조 우선
            for key in ["item", "items", "body", "response"]:
                if key in x:
                    walk(x[key])
                    return

            row = {}
            nested = []
            for k, v in x.items():
                if isinstance(v, (dict, list)):
                    nested.append(v)
                else:
                    row[k] = v
            if row:
                rows.append(row)
            for v in nested:
                walk(v)

    walk(obj)
    return rows


def parse_response(resp):
    text = resp.text.strip()
    if not text:
        return pd.DataFrame()

    try:
        obj = resp.json()
        return pd.DataFrame(flatten_json(obj))
    except Exception:
        pass

    try:
        root = ET.fromstring(text)
        rows = []
        for item in root.iter("item"):
            row = {child.tag: child.text for child in list(item)}
            if row:
                rows.append(row)
        if rows:
            return pd.DataFrame(rows)

        # item 태그가 없는 XML도 한 줄로 표시
        row = {child.tag: child.text for child in list(root)}
        return pd.DataFrame([row]) if row else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def fetch_api(name, url, timeout=12):
    if not url:
        return pd.DataFrame(), ""
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code != 200:
            return pd.DataFrame(), f"{name}: HTTP {r.status_code}"
        df = parse_response(r)
        return df, ""
    except Exception as e:
        return pd.DataFrame(), f"{name}: {e}"


def normalize_meet(x):
    s = str(x or "").strip()
    if s in ["1", "서울", "SEOUL", "Seoul", "seoul"]:
        return "서울"
    if s in ["2", "제주", "JEJU", "Jeju", "jeju"]:
        return "제주"
    if s in ["3", "부산경남", "부경", "부산", "BUSAN", "Busan", "busan"]:
        return "부산경남"
    return s


def find_col(df, candidates):
    if df is None or df.empty:
        return None
    lower = {str(c).lower(): c for c in df.columns}
    for x in candidates:
        if str(x).lower() in lower:
            return lower[str(x).lower()]
    for c in df.columns:
        cl = str(c).lower()
        for x in candidates:
            if str(x).lower() in cl:
                return c
    return None


def filter_current(df, target_date, track_place, target_rc_no, strict):
    if df is None or df.empty:
        return df

    d = df.copy()
    original = d.copy()

    date_col = find_col(d, ["rcDate", "raceDate", "meetDate", "ymd", "date"])
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

    if d.empty and not strict:
        return original
    return d


def chul_col(df):
    if df is None or df.empty:
        return None

    exact = ["chulNo", "chulno", "출전번호", "출전마번", "마번"]
    banned = ["enno", "hrno", "horseno", "age", "rcno", "meet", "rating", "chaksun", "prize", "amt"]

    for c in df.columns:
        if str(c) in exact or str(c).lower() in [e.lower() for e in exact]:
            vals = pd.to_numeric(df[c], errors="coerce")
            if vals.between(1, 14, inclusive="both").sum() >= 3:
                return c

    # chul 포함 컬럼만 보조 인정
    for c in df.columns:
        cl = str(c).lower()
        if any(b in cl for b in banned):
            continue
        if "chul" in cl or "출전" in cl or "마번" in cl:
            vals = pd.to_numeric(df[c], errors="coerce")
            if vals.between(1, 14, inclusive="both").sum() >= 3:
                return c
    return None


def valid_chulno_base(data):
    # 실전 마번 기준으로 신뢰 가능한 소스
    trusted = ["body", "gear", "today_odds", "first_odds", "third_odds", "popularity"]
    nums = {}
    evidence = {}

    for key in trusted:
        df = data.get(key, pd.DataFrame())
        if df is None or df.empty:
            continue
        col = chul_col(df)
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
    for n in sorted(nums.keys()):
        ev = evidence.get(n, set())
        score = 50
        score += 7 if "today_odds" in ev else 0
        score += 6 if "body" in ev else 0
        score += 5 if "gear" in ev else 0
        score += 4 if "popularity" in ev else 0
        score += 3 if "first_odds" in ev else 0
        score += 3 if "third_odds" in ev else 0

        rows.append({
            "마번": n,
            "마명": nums[n],
            "점수": score,
            "근거": ",".join(sorted(ev)),
        })

    return pd.DataFrame(rows)


def add_context_scores(score_df, data):
    if score_df is None or score_df.empty:
        return score_df

    df = score_df.copy()

    # 체중/장구/인기/배당 등은 컬럼명이 API마다 달라서 있는 경우만 보조 반영
    # 잘못된 숫자(enNo/hrNo/chaksun)는 절대 마번으로 쓰지 않음.
    df["점수"] = pd.to_numeric(df["점수"], errors="coerce").fillna(50)

    # popularity API에 chulNo가 잡히면 인기 존재 자체를 약간 가산
    pop = data.get("popularity", pd.DataFrame())
    if pop is not None and not pop.empty:
        col = chul_col(pop)
        if col:
            vals = pd.to_numeric(pop[col], errors="coerce").dropna().astype(int).tolist()
            df.loc[df["마번"].isin(vals), "점수"] += 2

    # jockey_change가 있으면 변동 리스크로 전체 과열 방지
    jc = data.get("jockey_change", pd.DataFrame())
    if jc is not None and len(jc) > 0:
        df["점수"] = df["점수"] - 1

    df["점수"] = df["점수"].round(2)
    return df.sort_values("점수", ascending=False)


def simulate(score_df):
    if score_df is None or score_df.empty or len(score_df) < 3:
        return pd.DataFrame()

    top = score_df.sort_values("점수", ascending=False).head(8)
    nums = top["마번"].astype(int).tolist()
    score = dict(zip(top["마번"].astype(int), pd.to_numeric(top["점수"], errors="coerce")))

    rows = []
    for a, b, c in permutations(nums, 3):
        val = score.get(a, 0) * 0.52 + score.get(b, 0) * 0.31 + score.get(c, 0) * 0.17
        rows.append({"조합": f"{a}-{b}-{c}", "점수": round(val, 2)})

    out = pd.DataFrame(rows).sort_values("점수", ascending=False).head(20)
    return out


def make_result(score_df, sim_df, data, env):
    result = {
        "판정": "관망",
        "신뢰도": 49,
        "추천금액": 0,
        "공격삼쌍승": "-",
        "방어삼복승": "-",
        "보조삼쌍승": "-",
        "상태": "현재 경주 chulNo 부족 / 데이터 섞임 방지",
    }

    if score_df is None or score_df.empty or len(score_df) < 3 or sim_df is None or sim_df.empty:
        return result

    connected_core = 0
    for k in ["body", "gear", "today_odds", "popularity", "corner_pace", "race_record", "jockey_change"]:
        if data.get(k, pd.DataFrame()) is not None and len(data.get(k, pd.DataFrame())) > 0:
            connected_core += 1

    confidence = min(72, 45 + len(score_df) * 2 + connected_core * 3)

    if confidence < 55:
        return result

    top = sim_df.iloc[0]["조합"]
    second = sim_df.iloc[1]["조합"] if len(sim_df) > 1 else "-"
    third = sim_df.iloc[2]["조합"] if len(sim_df) > 2 else "-"

    result.update({
        "판정": "소액검토" if confidence < 62 else "소액가능",
        "신뢰도": int(confidence),
        "추천금액": 1000 if confidence >= 62 else 0,
        "공격삼쌍승": top,
        "방어삼복승": " / ".join(top.split("-")),
        "보조삼쌍승": second if second != top else third,
        "상태": "수동구매 검토 / 손실제한",
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


def sheets_status():
    try:
        if "google_sheets" in st.secrets and ("SHEET_ID" in st.secrets["google_sheets"] or "sheet_id" in st.secrets["google_sheets"]):
            return "Google Sheets 허브 설정 있음"
    except Exception:
        pass
    return "Google Sheets 허브 미설정: 로컬 저장만 사용"



def parse_race_time_value(x):
    s = str(x or "").strip()
    if not s:
        return None

    # Examples: 10:35, 1035, 10시35분, 202606141035
    digits = re.sub(r"[^0-9]", "", s)

    try:
        if ":" in s:
            hh, mm = s.split(":")[:2]
            return int(hh) * 60 + int(mm[:2])
    except Exception:
        pass

    try:
        if len(digits) >= 12:  # yyyymmddhhmm
            hh = int(digits[-4:-2])
            mm = int(digits[-2:])
            return hh * 60 + mm
        if len(digits) == 4:
            hh = int(digits[:2])
            mm = int(digits[2:])
            return hh * 60 + mm
        if len(digits) == 3:
            hh = int(digits[:1])
            mm = int(digits[1:])
            return hh * 60 + mm
    except Exception:
        pass

    return None


def auto_pick_race_from_schedule(race_df, default_meet, default_rc):
    """
    경주정보 API에서 오늘 시간표를 읽어서 현재 한국시간 기준 가장 가까운 경주를 자동 선택.
    race_df에 시간/경주번호/경마장 컬럼이 없으면 기본값 유지.
    """
    if race_df is None or race_df.empty:
        return default_meet, int(default_rc), "경주정보 API 비어 있음"

    d = race_df.copy()

    # 날짜는 오늘만 우선
    date_col = find_col(d, ["rcDate", "raceDate", "meetDate", "ymd", "date"])
    if date_col:
        try:
            ds = d[date_col].astype(str).str.replace("-", "", regex=False).str.strip()
            today_s = today_ymd()
            only_today = d[ds == today_s]
            if not only_today.empty:
                d = only_today
        except Exception:
            pass

    time_col = find_col(d, ["rcTime", "raceTime", "출발시각", "출발시간", "time", "startTime"])
    rc_col = find_col(d, ["rcNo", "raceNo", "경주번호"])
    meet_col = find_col(d, ["meet", "meetCd", "rcourse", "경마장"])

    if not time_col or not rc_col:
        return default_meet, int(default_rc), "경주시간/경주번호 컬럼 없음"

    now_min = now_kst().hour * 60 + now_kst().minute

    candidates = []
    for _, r in d.iterrows():
        t = parse_race_time_value(r.get(time_col))
        if t is None:
            continue
        try:
            rc = int(float(r.get(rc_col)))
        except Exception:
            continue

        meet = default_meet
        if meet_col:
            meet = normalize_meet(r.get(meet_col))

        # 현재 이후 경주 우선, 이미 지난 경주는 다음 후보에서 밀림
        diff = t - now_min
        priority = diff if diff >= -3 else diff + 10000
        candidates.append((priority, diff, meet, rc, t))

    if not candidates:
        return default_meet, int(default_rc), "시간표 후보 없음"

    candidates.sort(key=lambda x: x[0])
    _, diff, meet, rc, t = candidates[0]
    hh, mm = divmod(t, 60)
    return meet, int(rc), f"자동선택: {meet} {rc}R {hh:02d}:{mm:02d} / 현재차이 {diff}분"


def force_analysis_even_if_low(score_df, data):
    """
    추천이 관망이어도 분석표는 반드시 보이도록 점수표를 보강.
    chulNo가 있는 모든 API를 스캔하되, 마번은 1~14만 인정.
    """
    if score_df is not None and not score_df.empty:
        return score_df

    nums = {}
    evidence = {}
    for key, df in data.items():
        if df is None or df.empty:
            continue
        col = chul_col(df)
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
        ev = evidence.get(n, set())
        rows.append({
            "마번": n,
            "마명": nums[n],
            "점수": 45 + len(ev) * 4,
            "근거": ",".join(sorted(ev)),
        })
    if rows:
        return pd.DataFrame(rows).sort_values("점수", ascending=False)
    return pd.DataFrame()

settings = read_json(SETTINGS_FILE, {})

st.title("🐎 MARU KRA FULL 19API REALTIME")
st.caption(f"한국시간: {now_text()} / 분석 날짜: {today_ymd()}")
st.info("전체 1~19번 API 실시간 호출 + 경주시간표 기준 자동 경마장/경주 선택 + chulNo 분석판입니다.")

# Sidebar
st.sidebar.title("🐎 MARU KRA 메뉴")
st.sidebar.caption("1~19번 API 전체 입력 / 실시간 분석")

api_key = st.sidebar.text_input(
    "공공데이터 API Key",
    value=str(get_setting(settings, "api_key", get_secret("API_KEY", ""))),
    type="password",
)

st.sidebar.divider()
st.sidebar.subheader("분석 기준")
target_date = st.sidebar.text_input("분석 날짜", value=str(get_setting(settings, "target_date", today_ymd())))
track_place = st.sidebar.selectbox(
    "경마장",
    ["서울", "부산경남", "제주"],
    index=["서울", "부산경남", "제주"].index(str(get_setting(settings, "track_place", "서울"))) if str(get_setting(settings, "track_place", "서울")) in ["서울", "부산경남", "제주"] else 0,
)
target_rc_no = st.sidebar.number_input(
    "경주번호",
    min_value=1,
    max_value=20,
    value=int(get_setting(settings, "target_rc_no", 1) or 1),
    step=1,
)

auto_schedule_pick = st.sidebar.checkbox("경주시간표 기준 자동 경마장/경주 선택", value=True)
st.sidebar.caption("경주정보 API가 시간표를 주면 현재 한국시간 기준 다음 경주를 자동 선택합니다.")

strict_filter = st.sidebar.checkbox("현재 경주 필터 엄격 적용", value=False)
add_filter_params = st.sidebar.checkbox("URL에 rcDate/meet/rcNo 자동 추가", value=False, help="HTTP 500이 늘면 OFF")
auto_refresh = st.sidebar.selectbox("자동 새로고침", [0, 30, 60, 120, 300], index=0)

st.sidebar.divider()
st.sidebar.subheader("핵심 API 1~8")
api_urls = {}
for api_name, key, label in API_ITEMS[:8]:
    api_urls[api_name] = st.sidebar.text_input(label, value=str(get_setting(settings, key, "")))

with st.sidebar.expander("보조 API 9~19", expanded=True):
    for api_name, key, label in API_ITEMS[8:]:
        api_urls[api_name] = st.text_input(label, value=str(get_setting(settings, key, "")))

st.sidebar.divider()
st.sidebar.subheader("환경/날씨")
manual_weather = st.sidebar.selectbox("날씨", ["맑음", "흐림", "비", "눈", "안개"], index=1)
track_condition = st.sidebar.selectbox("주로", ["양호", "다습", "포화", "불량", "건조"], index=0)
sand_condition = st.sidebar.selectbox("모래", ["빠름", "보통", "무거움"], index=1)
wind_condition = st.sidebar.selectbox("바람", ["약함", "보통", "강함"], index=1)

payload = {
    "api_key": api_key,
    "target_date": target_date,
    "track_place": track_place,
    "target_rc_no": int(target_rc_no),
}
for api_name, key, label in API_ITEMS:
    payload[key] = api_urls.get(api_name, "")

if st.sidebar.button("API 저장", use_container_width=True):
    save_json(SETTINGS_FILE, payload)
    st.sidebar.success("저장 완료")

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

if auto_refresh > 0:
    st.sidebar.info(f"{auto_refresh}초 자동 새로고침 사용 중")
    st.markdown(f"<meta http-equiv='refresh' content='{auto_refresh}'>", unsafe_allow_html=True)


if "data" not in st.session_state:
    st.session_state["data"] = {}
    st.session_state["errors"] = []
    st.session_state["last_loaded"] = ""

load_clicked = st.button("실시간 데이터 불러오기", use_container_width=True)

if load_clicked or auto_refresh > 0:
    data = {}
    errors = []

    selected_track = track_place
    selected_rc = int(target_rc_no)
    schedule_msg = "수동 선택"

    # 1단계: 경주정보 API 먼저 호출해서 시간표 기반 자동 선택
    race_full = build_url(
        api_urls.get("race", ""),
        api_key,
        target_date,
        track_place,
        target_rc_no,
        add_filter_params=add_filter_params,
    )
    race_df, race_err = fetch_api("race", race_full)
    if race_err:
        errors.append(race_err)

    if auto_schedule_pick and race_df is not None and not race_df.empty:
        selected_track, selected_rc, schedule_msg = auto_pick_race_from_schedule(race_df, track_place, target_rc_no)

    st.session_state["selected_track"] = selected_track
    st.session_state["selected_rc"] = selected_rc
    st.session_state["schedule_msg"] = schedule_msg

    # 2단계: 선택된 경마장/경주번호 기준으로 1~19번 전체 호출
    for api_name, key, label in API_ITEMS:
        full = build_url(
            api_urls.get(api_name, ""),
            api_key,
            target_date,
            selected_track,
            selected_rc,
            add_filter_params=add_filter_params,
        )
        df, err = fetch_api(api_name, full)
        if df is not None and not df.empty:
            df = filter_current(df, target_date, selected_track, selected_rc, strict_filter)
        data[api_name] = df
        if err:
            errors.append(err)

    st.session_state["data"] = data
    st.session_state["errors"] = errors
    st.session_state["last_loaded"] = now_text()

data = st.session_state["data"]
errors = st.session_state["errors"]
selected_track = st.session_state.get("selected_track", track_place)
selected_rc = st.session_state.get("selected_rc", int(target_rc_no))
schedule_msg = st.session_state.get("schedule_msg", "수동 선택")

env = {
    "weather": manual_weather,
    "track": track_condition,
    "sand": sand_condition,
    "wind": wind_condition,
}

score_df = valid_chulno_base(data)
score_df = force_analysis_even_if_low(score_df, data)
score_df = add_context_scores(score_df, data)
sim_df = simulate(score_df)
result = make_result(score_df, sim_df, data, env)

connected_rows = sum(len(v) for v in data.values() if isinstance(v, pd.DataFrame))
connected_apis = sum(1 for v in data.values() if isinstance(v, pd.DataFrame) and len(v) > 0)

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("자동 선택", f"{selected_track} {selected_rc}R")
m2.metric("연결 API", f"{connected_apis}/19")
m3.metric("연결 행수", connected_rows)
m4.metric("신뢰도", f"{result['신뢰도']}%")
m5.metric("마지막 수집", st.session_state.get("last_loaded", "-")[-8:] if st.session_state.get("last_loaded") else "-")
st.caption(f"경주시간표 선택 상태: {schedule_msg}")

if errors:
    st.warning(f"오류/미응답 API {len(errors)}개. 정상 연결 API만 분석에 반영합니다.")
    with st.expander("오류 상세"):
        st.write(errors)

st.subheader("최종 판단")
if result["판정"] == "관망":
    st.warning("관망")
else:
    st.success(result["판정"])

left, right = st.columns([1.2, 1])
with left:
    st.subheader("추천 조합")
    st.markdown(f"## {result['공격삼쌍승']}")
    st.write(f"방어 삼복승: {result['방어삼복승']}")
    st.write(f"보조 삼쌍승: {result['보조삼쌍승']}")
    st.write(f"상태: {result['상태']}")
    st.caption("자동구매 아님 · 공식 화면 수동 확인 · 수익 보장 아님")

with right:
    st.subheader("환경")
    st.write(f"날씨: {manual_weather}")
    st.write(f"주로: {track_condition}")
    st.write(f"모래: {sand_condition}")
    st.write(f"바람: {wind_condition}")
    st.info(sheets_status())

st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs(["API 연결", "말별 점수표", "삼쌍승 시뮬레이션", "원본 컬럼", "로그"])

with tab1:
    rows = []
    for api_name, key, label in API_ITEMS:
        df = data.get(api_name, pd.DataFrame())
        rows.append({
            "번호": label,
            "API": api_name,
            "행수": len(df) if isinstance(df, pd.DataFrame) else 0,
            "컬럼수": len(df.columns) if isinstance(df, pd.DataFrame) and not df.empty else 0,
            "chulNo컬럼": chul_col(df) if isinstance(df, pd.DataFrame) and not df.empty else "",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, height=520)

    with st.expander("자동 완성 URL 예시 — API Key 숨김"):
        ex = []
        for api_name, key, label in API_ITEMS:
            raw = api_urls.get(api_name, "")
            if raw:
                ex.append({
                    "API": api_name,
                    "요청URL": mask_url(build_url(raw, api_key, target_date, track_place, target_rc_no, add_filter_params)),
                })
        st.dataframe(pd.DataFrame(ex), use_container_width=True)

with tab2:
    st.caption("body/gear/today_odds/first_odds/third_odds/popularity 등 chulNo가 있는 API는 모두 분석 점수에 반영합니다.")
    if score_df is None or score_df.empty:
        st.warning("현재 선택 경주에서 chulNo 마번 데이터가 아직 없습니다. API 연결 탭에서 chulNo컬럼을 확인하세요.")
    st.dataframe(score_df, use_container_width=True, height=520)

with tab3:
    if result["판정"] == "관망":
        st.warning("관망 상태라 실전 추천 조합은 숨깁니다. chulNo 데이터가 충분히 들어오면 표시됩니다.")
    st.dataframe(sim_df, use_container_width=True, height=520)

with tab4:
    diag = []
    for api_name, key, label in API_ITEMS:
        df = data.get(api_name, pd.DataFrame())
        diag.append({
            "API": api_name,
            "행수": len(df) if isinstance(df, pd.DataFrame) else 0,
            "컬럼목록": ", ".join(map(str, list(df.columns)[:40])) if isinstance(df, pd.DataFrame) and not df.empty else "",
        })
    st.dataframe(pd.DataFrame(diag), use_container_width=True, height=520)

    api_choice = st.selectbox("원본 미리보기 API 선택", [x[0] for x in API_ITEMS])
    preview = data.get(api_choice, pd.DataFrame())
    st.dataframe(preview.head(100) if isinstance(preview, pd.DataFrame) else pd.DataFrame(), use_container_width=True, height=420)

with tab5:
    st.write("과거 추천 로그")
    st.dataframe(read_table(RECO_FILE), use_container_width=True, height=260)
    st.write("과거 예상 vs 실제 비교 로그")
    st.dataframe(read_table(COMPARE_FILE), use_container_width=True, height=260)

# Save recommendation only if real recommendation
if result["판정"] != "관망" and result["공격삼쌍승"] != "-":
    if st.button("현재 추천 로그 저장", use_container_width=True):
        append_table(RECO_FILE, {
            "저장시각": now_text(),
            "날짜": target_date,
            "경마장": track_place,
            "경주번호": int(target_rc_no),
            "판정": result["판정"],
            "공격삼쌍승": result["공격삼쌍승"],
            "방어삼복승": result["방어삼복승"],
            "신뢰도": result["신뢰도"],
            "추천금액": result["추천금액"],
        })
        st.success("추천 로그 저장 완료")
