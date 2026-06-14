
import streamlit as st
import pandas as pd
import requests
import json
import hashlib
import traceback
import random
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import Counter

KST = ZoneInfo("Asia/Seoul")

def now_kst():
    return datetime.now(KST)

def today_kst():
    return now_kst().strftime("%Y%m%d")

def now_kst_str():
    return now_kst().strftime("%Y-%m-%d %H:%M:%S")


st.set_page_config(
    page_title="MARU KRA PC DASHBOARD",
    page_icon="🐎",
    layout="wide"
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

def sheets_enabled():
    return bool(sheets_secret_get(["SHEET_ID", "sheet_id"], ""))

def get_gsheet_client():
    """
    Streamlit Secrets의 [google_sheets] 서비스계정 JSON으로 Google Sheets 연결.
    없거나 실패하면 None 반환하고 앱은 로컬 CSV로 계속 작동.
    """
    if not sheets_enabled():
        return None, "Google Sheets 미설정"

    try:
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        # 방법 1: SERVICE_ACCOUNT_JSON 전체를 TOML multiline string으로 저장
        raw = sheets_secret_get(["SERVICE_ACCOUNT_JSON", "service_account_json"], "")
        if raw:
            if isinstance(raw, str):
                info = json.loads(raw)
            else:
                info = dict(raw)
        else:
            # 방법 2: [google_sheets.service_account] 형태의 TOML table
            info = {}
            try:
                if "google_sheets" in st.secrets and "service_account" in st.secrets["google_sheets"]:
                    info = dict(st.secrets["google_sheets"]["service_account"])
            except Exception:
                info = {}

        if not info:
            return None, "서비스계정 정보 없음"

        creds = Credentials.from_service_account_info(info, scopes=scopes)
        client = gspread.authorize(creds)
        return client, ""
    except Exception as e:
        return None, "Google Sheets 연결 실패: " + str(e)

def get_sheet_workbook():
    client, err = get_gsheet_client()
    if client is None:
        return None, err
    try:
        sheet_id = str(sheets_secret_get(["SHEET_ID", "sheet_id"], "")).strip()
        if not sheet_id:
            return None, "SHEET_ID 없음"
        return client.open_by_key(sheet_id), ""
    except Exception as e:
        return None, "시트 열기 실패: " + str(e)

def get_or_create_ws(wb, title, headers):
    try:
        ws = wb.worksheet(title)
    except Exception:
        ws = wb.add_worksheet(title=title, rows=1000, cols=max(20, len(headers) + 5))
        ws.append_row(headers)
        return ws

    try:
        first = ws.row_values(1)
        if not first:
            ws.append_row(headers)
    except Exception:
        pass
    return ws

def df_from_worksheet(title, headers):
    wb, err = get_sheet_workbook()
    if wb is None:
        return pd.DataFrame(), err
    try:
        ws = get_or_create_ws(wb, title, headers)
        records = ws.get_all_records()
        return pd.DataFrame(records), ""
    except Exception as e:
        return pd.DataFrame(), "시트 읽기 실패: " + str(e)

def append_sheet_row(title, row, headers):
    wb, err = get_sheet_workbook()
    if wb is None:
        return False, err
    try:
        ws = get_or_create_ws(wb, title, headers)
        all_headers = ws.row_values(1)
        if not all_headers:
            all_headers = headers
            ws.append_row(all_headers)

        # 새 컬럼이 생기면 헤더 확장
        changed = False
        for k in row.keys():
            if k not in all_headers:
                all_headers.append(k)
                changed = True
        if changed:
            ws.update("1:1", [all_headers])

        values = [row.get(h, "") for h in all_headers]
        ws.append_row(values, value_input_option="USER_ENTERED")
        return True, ""
    except Exception as e:
        return False, "시트 저장 실패: " + str(e)

def file_to_sheet_title(path):
    name = str(path)
    if "recommendation" in name:
        return "recommendations"
    if "compare" in name:
        return "comparisons"
    if "result" in name:
        return "results"
    return "logs"

def default_headers_for_path(path):
    title = file_to_sheet_title(path)
    if title == "recommendations":
        return ["저장시각","날짜","경마장","경주번호","출발시간","판정","공격삼쌍승","방어삼복승","보조삼쌍승","예상배당","신뢰도","추천금액","오늘손익","누적손익","날씨","주로","모래","바람"]
    if title == "comparisons":
        return ["저장시각","날짜","경마장","경주번호","공격삼쌍승","실제삼쌍","실제삼복","투입금","환급금","수익률","분석결과","메모"]
    if title == "results":
        return ["저장시각","날짜","경마장","경주번호","공격삼쌍승","투입금","환급금","수익률","분석결과","메모"]
    return ["저장시각","내용"]


def read_table(path):
    # Google Sheets가 설정되어 있으면 PC/모바일 공용 기록을 우선 읽음
    try:
        if sheets_enabled():
            title = file_to_sheet_title(path)
            headers = default_headers_for_path(path)
            df, err = df_from_worksheet(title, headers)
            if not df.empty:
                return df
    except Exception:
        pass

    if path.exists():
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def append_table(path, row):
    # 1) Google Sheets 저장: PC/모바일 공용
    try:
        if sheets_enabled():
            title = file_to_sheet_title(path)
            headers = default_headers_for_path(path)
            ok, err = append_sheet_row(title, row, headers)
            if not ok:
                st.warning("Google Sheets 저장 실패: " + str(err))
    except Exception as e:
        try:
            st.warning("Google Sheets 저장 중 오류: " + str(e))
        except Exception:
            pass

    # 2) 로컬 CSV도 백업 저장
    df = pd.DataFrame()
    if path.exists():
        try:
            df = pd.read_csv(path)
        except Exception:
            df = pd.DataFrame()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return df


def today():
    return today_kst()


def current_setting_payload():
    payload = {}
    # 기존 설정값 유지
    try:
        if isinstance(settings, dict):
            payload.update(settings)
    except Exception:
        pass

    # API Key / URL 저장
    for k in [
        "api_key",
        "race_url", "entry_url", "horse_url", "body_url", "gear_url",
        "rating_url", "odds_url", "today_odds_url", "result_detail_url",
        "race_record_url", "start_exam_url", "judge_url", "jockey_change_url",
        "weather_alert_url", "corner_pace_url", "popularity_url",
        "first_odds_url", "second_odds_url", "third_odds_url"
    ]:
        try:
            payload[k] = globals().get(k, payload.get(k, ""))
        except Exception:
            pass

    # 분석 설정 저장
    for k in [
        "target_date", "target_rc_no", "track_place",
        "daily_loss_stop", "daily_entries_limit"
    ]:
        try:
            payload[k] = globals().get(k, payload.get(k, ""))
        except Exception:
            pass

    return payload

def resolve_api_url(var_name, secret_keys=None, default=""):
    """
    API URL 변수가 누락되어도 앱이 멈추지 않게 Secrets/settings/session_state에서 안전하게 찾습니다.
    """
    secret_keys = secret_keys or []
    try:
        val = globals().get(var_name, "")
        if val:
            return val
    except Exception:
        pass

    try:
        if "settings" in globals() and isinstance(settings, dict):
            for k in [var_name] + secret_keys:
                if settings.get(k):
                    return settings.get(k)
    except Exception:
        pass

    try:
        if "maru" in st.secrets:
            for k in secret_keys:
                if k in st.secrets["maru"]:
                    return st.secrets["maru"][k]
    except Exception:
        pass

    try:
        for k in secret_keys:
            if k in st.secrets:
                return st.secrets[k]
    except Exception:
        pass

    try:
        for k in [var_name] + secret_keys:
            if k in st.session_state:
                return st.session_state[k]
    except Exception:
        pass

    return default

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
    ymd = today_kst()

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

    desired_date = str(target_date or today_kst()).replace("-", "").strip()
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


def _safe_str(x):
    return str(x or "").strip()

def _num_series(s):
    return pd.to_numeric(s, errors="coerce")

def current_target_values():
    try:
        d = str(target_date).replace("-", "").strip()
    except Exception:
        d = today()
    try:
        rc = int(target_rc_no)
    except Exception:
        rc = None
    try:
        meet = track_place
    except Exception:
        meet = ""
    return d, meet, rc

def normalize_meet_for_filter(x):
    s = str(x or "").strip()
    if s in ["1", "서울", "SEOUL", "Seoul", "seoul"]:
        return "서울"
    if s in ["2", "제주", "JEJU", "Jeju", "jeju"]:
        return "제주"
    if s in ["3", "부산경남", "부경", "부산", "BUSAN", "Busan", "busan"]:
        return "부산경남"
    return s

def find_any_col(df, names):
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

def smart_current_filter(df, api_name=""):
    """
    현재 선택 경주만 우선 사용합니다.
    rcDate / meet / rcNo 컬럼이 있으면 자동 필터.
    필터 후 1행 이상이면 필터된 데이터 사용.
    완전히 비면 원본 유지하되 추천 단계에서는 관망 처리.
    """
    if df is None or df.empty:
        return df

    d = df.copy()
    original = d.copy()
    target_date_s, target_meet, target_rc = current_target_values()

    date_col = find_any_col(d, ["rcDate", "raceDate", "meetDate", "date", "ymd"])
    meet_col = find_any_col(d, ["meet", "meetCd", "rcourse", "경마장"])
    rc_col = find_any_col(d, ["rcNo", "raceNo", "경주번호"])

    try:
        if date_col:
            ds = d[date_col].astype(str).str.replace("-", "", regex=False).str.strip()
            d = d[ds == target_date_s]
    except Exception:
        pass

    try:
        if meet_col:
            ms = d[meet_col].apply(normalize_meet_for_filter)
            d = d[ms == normalize_meet_for_filter(target_meet)]
    except Exception:
        pass

    try:
        if rc_col and target_rc is not None:
            rs = pd.to_numeric(d[rc_col], errors="coerce")
            d = d[rs == target_rc]
    except Exception:
        pass

    if not d.empty:
        return d

    return original

def has_current_chulno_source(data):
    """
    현재 경주 기준 chulNo 소스가 있는지 확인.
    body/gear/today_odds 중 현재 경주 필터 후 chulNo가 3개 이상이면 True.
    """
    trusted = ["body", "gear", "today_odds"]
    for key in trusted:
        df = data.get(key, pd.DataFrame())
        if df is None or df.empty:
            continue
        f = smart_current_filter(df, key)
        col = horse_no_col(f)
        if col:
            vals = pd.to_numeric(f[col], errors="coerce")
            if vals.between(1, 14, inclusive="both").sum() >= 3:
                return True
    return False

def clean_result_for_display(result, data):
    """
    관망/무효 상태에서는 조합을 화면에서 숨깁니다.
    """
    if not result:
        return result
    try:
        combo = str(result.get("공격삼쌍승", "")).replace("/", "-").strip()
        nums = [int(x.strip()) for x in combo.split("-") if x.strip()]
        invalid_combo = len(nums) != 3 or any(n < 1 or n > 14 for n in nums)
    except Exception:
        invalid_combo = True

    if invalid_combo or not has_current_chulno_source(data):
        result["판정"] = "관망"
        result["추천금액"] = 0
        result["신뢰도"] = min(int(result.get("신뢰도", 0)), 49)
        result["자금상태"] = "현재 경주 chulNo 부족 / 데이터 섞임 방지"
        result["공격삼쌍승"] = "-"
        result["방어삼복승"] = "-"
        result["보조삼쌍승"] = "-"
        result["예상배당"] = 0
    return result


# 전역 API URL 기본값 보강
race_url = globals().get("race_url", "")
entry_url = globals().get("entry_url", "")
horse_url = globals().get("horse_url", "")
body_url = globals().get("body_url", "")
gear_url = globals().get("gear_url", "")
rating_url = globals().get("rating_url", "")
odds_url = globals().get("odds_url", "")
today_odds_url = globals().get("today_odds_url", "")
result_detail_url = globals().get("result_detail_url", "")
race_record_url = globals().get("race_record_url", "")
start_exam_url = globals().get("start_exam_url", "")
judge_url = globals().get("judge_url", "")
jockey_change_url = globals().get("jockey_change_url", "")
weather_alert_url = globals().get("weather_alert_url", "")
corner_pace_url = globals().get("corner_pace_url", "")
popularity_url = globals().get("popularity_url", "")
first_odds_url = globals().get("first_odds_url", "")
second_odds_url = globals().get("second_odds_url", "")
third_odds_url = globals().get("third_odds_url", "")


# 샘플데이터 사용 여부 기본값 보강
use_sample = globals().get("use_sample", False)

def get_data():

    # use_sample 변수 누락 방지
    use_sample = bool(globals().get("use_sample", False))
    try:
        if "use_sample" in st.session_state:
            use_sample = bool(st.session_state["use_sample"])
    except Exception:
        pass


    # API URL 변수 누락 방지
    race_url = resolve_api_url("race_url", ["RACE_URL", "race_url"])
    entry_url = resolve_api_url("entry_url", ["ENTRY_URL", "entry_url"])
    horse_url = resolve_api_url("horse_url", ["HORSE_URL", "horse_url"])
    body_url = resolve_api_url("body_url", ["BODY_URL", "body_url"])
    gear_url = resolve_api_url("gear_url", ["GEAR_URL", "gear_url"])
    rating_url = resolve_api_url("rating_url", ["RATING_URL", "rating_url"])
    odds_url = resolve_api_url("odds_url", ["ODDS_URL", "odds_url"])
    today_odds_url = resolve_api_url("today_odds_url", ["TODAY_ODDS_URL", "today_odds_url"])
    result_detail_url = resolve_api_url("result_detail_url", ["RESULT_DETAIL_URL", "result_detail_url"])
    race_record_url = resolve_api_url("race_record_url", ["RACE_RECORD_URL", "race_record_url"])
    start_exam_url = resolve_api_url("start_exam_url", ["START_EXAM_URL", "start_exam_url"])
    judge_url = resolve_api_url("judge_url", ["JUDGE_URL", "judge_url"])
    jockey_change_url = resolve_api_url("jockey_change_url", ["JOCKEY_CHANGE_URL", "jockey_change_url"])
    weather_alert_url = resolve_api_url("weather_alert_url", ["WEATHER_ALERT_URL", "weather_alert_url"])
    corner_pace_url = resolve_api_url("corner_pace_url", ["CORNER_PACE_URL", "corner_pace_url"])
    popularity_url = resolve_api_url("popularity_url", ["POPULARITY_URL", "popularity_url"])
    first_odds_url = resolve_api_url("first_odds_url", ["FIRST_ODDS_URL", "first_odds_url"])
    second_odds_url = resolve_api_url("second_odds_url", ["SECOND_ODDS_URL", "second_odds_url"])
    third_odds_url = resolve_api_url("third_odds_url", ["THIRD_ODDS_URL", "third_odds_url"])

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
        df = smart_current_filter(df, name)
        data[name] = smart_current_filter(df, name)
        if err:
            errors.append(f"{name}:{err}")

    if bool(globals().get('use_sample', locals().get('use_sample', False))) and data.get("entry", pd.DataFrame()).empty and data.get("horse", pd.DataFrame()).empty:
        race, horse, risk = sample_data()
        data["race"] = race
        data["entry"] = horse
        data["horse"] = horse
        data["start_exam"] = risk

    return data, fetch_env(), errors






def horse_no_col(df):
    """
    실제 구매용 마번 컬럼만 사용합니다.
    enNo/hrNo/age/rcNo/meet/rating/chaksun 등은 절대 마번으로 쓰지 않습니다.
    """
    if df is None or df.empty:
        return None

    allowed_exact = ["chulNo", "chulno", "chul_no", "출전번호", "출전마번", "마번"]
    banned_words = ["enno", "hrno", "horseno", "age", "rcno", "meet", "rating", "chaksun", "prize", "amt"]

    for key in allowed_exact:
        for c in df.columns:
            if str(c).lower() == key.lower():
                vals = pd.to_numeric(df[c], errors="coerce")
                if vals.between(1, 14, inclusive="both").sum() >= 3:
                    return c

    for c in df.columns:
        cl = str(c).lower()
        if any(b in cl for b in banned_words):
            continue
        if "chul" in cl or "출전" in cl or "마번" in cl:
            vals = pd.to_numeric(df[c], errors="coerce")
            if vals.between(1, 14, inclusive="both").sum() >= 3:
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


def hub_headers(title):
    common_time = ["저장시각","날짜","경마장","경주번호"]
    if title == "api_status":
        return common_time + ["API","행수","컬럼수","마번후보","상태"]
    if title == "score_snapshots":
        return common_time + ["마번","마명","점수","순위","근거"]
    if title == "hub_status":
        return ["저장시각","날짜","경마장","경주번호","연결데이터","추천","판정","상태"]
    if title == "recommendations":
        return ["저장시각","날짜","경마장","경주번호","출발시간","판정","공격삼쌍승","방어삼복승","보조삼쌍승","예상배당","신뢰도","추천금액","오늘손익","누적손익","날씨","주로","모래","바람"]
    if title == "comparisons":
        return ["저장시각","날짜","경마장","경주번호","공격삼쌍승","실제삼쌍","실제삼복","투입금","환급금","수익률","분석결과","메모"]
    if title == "results":
        return ["저장시각","날짜","경마장","경주번호","공격삼쌍승","투입금","환급금","수익률","분석결과","메모"]
    return ["저장시각","내용"]

def safe_target_date():
    try:
        return str(target_date)
    except Exception:
        return today()

def safe_target_rc():
    try:
        return int(target_rc_no)
    except Exception:
        try:
            return result.get("경주번호","")
        except Exception:
            return ""

def hub_append(title, row):
    if not sheets_enabled():
        return False, "Google Sheets 미설정"
    return append_sheet_row(title, row, hub_headers(title))

def hub_sync_now(data, score_df, result):
    """
    실시간 API 수집 결과와 분석 결과를 허브에 저장.
    같은 실행에서 같은 추천은 중복 저장하지 않도록 session_state key 사용.
    """
    if not sheets_enabled():
        return False, "Google Sheets 미설정"

    now = now_kst_str()
    d = safe_target_date()
    rc = safe_target_rc()
    try:
        place = track_place
    except Exception:
        place = ""

    try:
        total_rows = sum(len(v) for v in data.values() if v is not None)
    except Exception:
        total_rows = 0

    rec = ""
    judge = ""
    try:
        rec = result.get("공격삼쌍승","")
        judge = result.get("판정","")
    except Exception:
        pass

    sync_key = hashlib.md5(f"{d}-{place}-{rc}-{total_rows}-{rec}-{judge}".encode("utf-8")).hexdigest()
    if st.session_state.get("_hub_last_sync_key") == sync_key:
        return True, "이미 동기화됨"

    # 1. API 연결 상태 저장
    for k, v in data.items():
        try:
            rows = len(v) if v is not None else 0
            cols = len(v.columns) if v is not None and not v.empty else 0
            hcol = ""
            try:
                hcol = str(horse_no_col(v)) if v is not None and not v.empty else ""
            except Exception:
                hcol = ""
            hub_append("api_status", {
                "저장시각": now, "날짜": d, "경마장": place, "경주번호": rc,
                "API": k, "행수": rows, "컬럼수": cols, "마번후보": hcol,
                "상태": "OK" if rows > 0 else "EMPTY"
            })
        except Exception:
            pass

    # 2. 말별 점수 상위 저장
    try:
        if score_df is not None and not score_df.empty:
            tmp = score_df.copy().head(30)
            for idx, r in tmp.iterrows():
                row = {
                    "저장시각": now, "날짜": d, "경마장": place, "경주번호": rc,
                    "마번": r.get("마번",""),
                    "마명": r.get("마명",""),
                    "점수": r.get("점수", r.get("score","")),
                    "순위": int(idx) + 1,
                    "근거": r.get("근거", r.get("reason",""))
                }
                hub_append("score_snapshots", row)
    except Exception:
        pass

    # 3. 허브 상태 저장
    hub_append("hub_status", {
        "저장시각": now, "날짜": d, "경마장": place, "경주번호": rc,
        "연결데이터": total_rows, "추천": rec, "판정": judge, "상태": "SYNCED"
    })

    st.session_state["_hub_last_sync_key"] = sync_key
    return True, "허브 동기화 완료"

def hub_read_recent(title, limit=100):
    if not sheets_enabled():
        return pd.DataFrame()
    df, err = df_from_worksheet(title, hub_headers(title))
    if df is None or df.empty:
        return pd.DataFrame()
    return df.tail(limit)

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
    현재 선택 경주에서 신뢰 가능한 chulNo 소스만 모아 출전마 후보표를 만듭니다.
    entry의 enNo/hrNo, horse 기본정보는 사용하지 않습니다.
    """
    priority_keys = ["body", "gear", "today_odds"]
    nums = set()
    names = {}

    for key in priority_keys:
        df = data.get(key, pd.DataFrame())
        if df is None or df.empty:
            continue

        tmp = smart_current_filter(df, key)
        no_col = horse_no_col(tmp)
        if not no_col:
            continue

        tmp = tmp.copy()
        tmp["_tmp_no"] = pd.to_numeric(tmp[no_col], errors="coerce")
        tmp = tmp[tmp["_tmp_no"].between(1, 14, inclusive="both")]

        for _, r in tmp.iterrows():
            n = int(r["_tmp_no"])
            nums.add(n)
            for name_col in ["hrName", "마명", "horseName", "hr_name", "rcName"]:
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


def valid_chulno_base(data):
    trusted = ["body", "gear", "today_odds"]
    nums = {}
    evidence = {}

    for key in trusted:
        df = data.get(key, pd.DataFrame())
        if df is None or df.empty:
            continue

        try:
            tmp = smart_current_filter(df, key)
        except Exception:
            tmp = df.copy()

        if tmp is None or tmp.empty:
            continue

        chul_cols = []
        for c in tmp.columns:
            cl = str(c).lower()
            if cl == "chulno" or str(c) in ["chulNo", "출전번호", "출전마번", "마번"]:
                chul_cols.append(c)

        if not chul_cols:
            continue

        col = chul_cols[0]
        tmp = tmp.copy()
        tmp["_valid_chulno"] = pd.to_numeric(tmp[col], errors="coerce")
        tmp = tmp[tmp["_valid_chulno"].between(1, 14, inclusive="both")]

        for _, r in tmp.iterrows():
            n = int(r["_valid_chulno"])
            name = f"{n}번"
            for nc in ["hrName", "마명", "horseName", "rcName"]:
                if nc in tmp.columns and pd.notna(r.get(nc, None)) and str(r.get(nc)).strip():
                    name = str(r.get(nc)).strip()
                    break
            nums[n] = name
            evidence.setdefault(n, set()).add(key)

    rows = []
    for n in sorted(nums.keys()):
        ev = ",".join(sorted(evidence.get(n, [])))
        base_score = 50 + len(evidence.get(n, [])) * 5
        rows.append({"마번": n, "마명": nums[n], "점수": base_score, "근거": ev})
    return pd.DataFrame(rows)

def valid_combo_only(combo):
    try:
        parts = [int(x.strip()) for x in str(combo).replace("/", "-").split("-") if str(x).strip()]
        return len(parts) == 3 and len(set(parts)) == 3 and all(1 <= n <= 14 for n in parts)
    except Exception:
        return False

def combo_inside_valid_nums(combo, valid_nums):
    try:
        parts = [int(x.strip()) for x in str(combo).replace("/", "-").split("-") if str(x).strip()]
        return len(parts) == 3 and all(n in valid_nums for n in parts)
    except Exception:
        return False

def filter_combos_to_valid(combos, valid_nums):
    if not combos:
        return []
    valid_nums = set(int(x) for x in valid_nums)
    out = []
    for c in combos:
        try:
            combo_text = c.get("조합", c.get("combo", c.get("공격삼쌍승", "")))
            if valid_combo_only(combo_text) and combo_inside_valid_nums(combo_text, valid_nums):
                out.append(c)
        except Exception:
            pass
    return out

def force_chulno_only_after_analysis(data, score_df, result, combos):
    base = valid_chulno_base(data)

    if base.empty or len(base) < 3:
        if result:
            result["판정"] = "관망"
            result["추천금액"] = 0
            result["신뢰도"] = min(int(result.get("신뢰도", 0)), 49)
            result["공격삼쌍승"] = "-"
            result["방어삼복승"] = "-"
            result["보조삼쌍승"] = "-"
            result["예상배당"] = 0
            result["자금상태"] = "현재 경주 chulNo 부족 / 점수표 생성 차단"
        return base, result, []

    valid_nums = set(base["마번"].astype(int).tolist())
    clean_score = base.copy()

    # 기존 점수표에 같은 마번이 있을 때만 점수 반영
    try:
        if score_df is not None and not score_df.empty and "마번" in score_df.columns:
            tmp = score_df.copy()
            tmp["마번"] = pd.to_numeric(tmp["마번"], errors="coerce")
            tmp = tmp[tmp["마번"].isin(valid_nums)]
            if "점수" in tmp.columns and not tmp.empty:
                score_map = dict(zip(tmp["마번"].astype(int), tmp["점수"]))
                clean_score["점수"] = clean_score["마번"].map(score_map).fillna(clean_score["점수"])
    except Exception:
        pass

    clean_combos = filter_combos_to_valid(combos, valid_nums)

    if result:
        combo = result.get("공격삼쌍승", "")
        if (not valid_combo_only(combo)) or (not combo_inside_valid_nums(combo, valid_nums)):
            result["판정"] = "관망"
            result["추천금액"] = 0
            result["신뢰도"] = min(int(result.get("신뢰도", 0)), 49)
            result["공격삼쌍승"] = "-"
            result["방어삼복승"] = "-"
            result["보조삼쌍승"] = "-"
            result["예상배당"] = 0
            result["자금상태"] = "현재 경주 출전마 외 조합 차단"

    return clean_score, result, clean_combos

score_df, result, combos = analyze(data, env)
score_df, result, combos = force_chulno_only_after_analysis(data, score_df, result, combos)
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

if auto_save_reco and result and result.get("공격삼쌍승","-") != "-" and valid_combo_only(result.get("공격삼쌍승","")) and current_race_ready(result) and is_valid_combo_text(result.get("공격삼쌍승","")) and int(result.get("신뢰도",0)) > 0:
    append_table(RECO_FILE, {
        "저장시각":now_kst_str(),
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


st.divider()
pc_left, pc_mid, pc_right = st.columns([1.15, 1.4, 1.0])

with pc_left:
    st.subheader("현재 선택")
    try:
        st.write(f"**날짜:** {target_date}")
        st.write(f"**경마장:** {track_place}")
        st.write(f"**경주번호:** {int(target_rc_no)}R")
        if "strict_race_filter" in globals():
            st.write(f"**엄격 필터:** {strict_race_filter}")
    except Exception:
        st.write(f"**경마장:** {track_place}")

with pc_mid:
    st.subheader("추천 핵심")
    try:
        st.write(f"**판정:** {result.get('판정','대기')}")
        st.write(f"**공격 삼쌍승:** {result.get('공격삼쌍승','-')}")
        st.write(f"**방어 삼복승:** {result.get('방어삼복승','-')}")
        st.write(f"**추천금액:** {result.get('추천금액',0):,}원")
    except Exception:
        st.write("분석 대기")

with pc_right:
    st.subheader("운영 상태")
    try:
        st.write(f"**오늘손익:** {result.get('오늘손익',0):,}원")
        st.write(f"**누적손익:** {result.get('누적손익',0):,}원")
        st.write(f"**자금상태:** {result.get('자금상태','-')}")
        st.write(f"**기상특보:** {result.get('기상특보위험',0)}")
    except Exception:
        st.write("운영 상태 대기")

st.divider()
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
            "저장시각":now_kst_str(),
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
    st.caption("점수표와 추천은 body/gear/today_odds의 chulNo만 사용합니다. enNo/hrNo/chaksun은 마번으로 쓰지 않습니다.")
    st.dataframe(pd.DataFrame([{"API":k, "행수":len(v)} for k, v in data.items()]), use_container_width=True)

    st.subheader("말별 점수표(chulNo)")
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



st.divider()
st.subheader("PC 상세 분석 패널")

tab_score, tab_sim, tab_api, tab_logs = st.tabs(["말별 점수표(chulNo)", "삼쌍승 시뮬레이션", "API 원본/진단", "과거 로그"])

with tab_score:
    try:
        st.dataframe(score_df, use_container_width=True, height=420)
    except Exception:
        st.write("점수표 없음")

with tab_sim:
    try:
        st.dataframe(pd.DataFrame(combos), use_container_width=True, height=360)
    except Exception:
        st.write("시뮬레이션 없음")

with tab_api:
    try:
        api_rows = []
        for k, v in data.items():
            api_rows.append({
                "API": k,
                "행수": len(v) if v is not None else 0,
                "컬럼수": len(v.columns) if v is not None and not v.empty else 0,
                "마번후보": str(horse_no_col(v)) if v is not None and not v.empty else ""
            })
        st.dataframe(pd.DataFrame(api_rows), use_container_width=True, height=360)
        if "entry" in data and not data["entry"].empty:
            st.write("2번 출전 등록말 원본 미리보기")
            st.dataframe(data["entry"].head(50), use_container_width=True, height=360)
    except Exception:
        st.write("API 진단 표시 실패")

with tab_logs:
    try:
        col_a, col_b = st.columns(2)
        with col_a:
            st.write("과거 추천 로그")
            st.dataframe(read_table(RECO_FILE).tail(100), use_container_width=True, height=360)
        with col_b:
            st.write("과거 예상 vs 실제 비교 로그")
            st.dataframe(read_table(COMPARE_FILE).tail(100), use_container_width=True, height=360)
    except Exception:
        st.write("로그 없음")



st.divider()
st.subheader("허브 실시간 패널")
try:
    if sheets_enabled():
        st.success("Google Sheets 허브 사용 중: PC/모바일 기록 공유")
    else:
        st.info("Google Sheets 허브 미설정: Streamlit Secrets에 SHEET_ID와 SERVICE_ACCOUNT_JSON을 넣어야 PC/모바일 실시간 공유가 됩니다.")
except Exception:
    st.info("허브 상태 확인 대기")

hub_tab1, hub_tab2, hub_tab3 = st.tabs(["허브 상태", "허브 점수 기록", "허브 추천/비교"])

with hub_tab1:
    try:
        if hub_read_mode:
            st.dataframe(hub_read_recent("hub_status", 100), use_container_width=True, height=320)
        else:
            st.write("허브 불러오기 OFF")
    except Exception:
        st.write("허브 상태 없음")

with hub_tab2:
    try:
        if hub_read_mode:
            st.dataframe(hub_read_recent("score_snapshots", 100), use_container_width=True, height=420)
        else:
            st.write("허브 불러오기 OFF")
    except Exception:
        st.write("허브 점수 기록 없음")

with hub_tab3:
    try:
        c1, c2 = st.columns(2)
        with c1:
            st.write("허브 추천 기록")
            st.dataframe(hub_read_recent("recommendations", 100), use_container_width=True, height=360)
        with c2:
            st.write("허브 비교 기록")
            st.dataframe(hub_read_recent("comparisons", 100), use_container_width=True, height=360)
    except Exception:
        st.write("허브 추천/비교 기록 없음")
