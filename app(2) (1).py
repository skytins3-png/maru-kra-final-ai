# -*- coding: utf-8 -*-
"""
MARU KRA FINAL ALL-IN-ONE APP
- 덮어쓰기용 단일 app.py
- 19개 KRA/기상 API URL 기본 적용
- API별 ON/OFF + 전체 실시간 ON/OFF
- HTTP 500/무응답/0건이어도 앱 중단 없이 샘플/최근 캐시로 계속 분석
- 실시간 분석, 허브 저장, API 진단, 시간표/빅데이터, 10초 수동구매 모드 포함
- 자동구매/자동결제 없음: 공식 페이지 이동 + 사용자가 직접 입력/확정
"""

from __future__ import annotations

import os
import re
import json
import time
import random
import math
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from typing import Dict, List, Tuple, Any

import pandas as pd
import requests
import streamlit as st

# -----------------------------------------------------------------------------
# Streamlit basic
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="MARU KRA 실전 대시보드 ALL-IN-ONE",
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
SCHEDULE_HUB_FILE = DATA_DIR / "maru_kra_schedule_hub.csv"
BIGDATA_FILE = DATA_DIR / "maru_kra_bigdata_result_log.csv"
AUTO_RUN_STATE_FILE = DATA_DIR / "maru_kra_auto_run_state.json"
LIVE_CACHE_FILE = DATA_DIR / "maru_kra_last_live_cache.json"

# -----------------------------------------------------------------------------
# 19 default API URLs from latest MARU KRA base
# -----------------------------------------------------------------------------
FORCE_DEFAULT_URLS: Dict[str, str] = {
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

API_LABELS: List[Tuple[str, str]] = [
    ("race_url", "① 경주정보"),
    ("entry_url", "② 출전등록말/출전표"),
    ("horse_url", "③ 경주마정보"),
    ("body_url", "④ 출전마 체중"),
    ("gear_url", "⑤ 장구/폐출혈"),
    ("rating_url", "⑥ 레이팅"),
    ("odds_url", "⑦ 배당/매출"),
    ("today_odds_url", "⑧ 시행당일 배당종합"),
    ("result_detail_url", "⑨ 경주결과상세"),
    ("race_record_url", "⑩ 경주기록"),
    ("start_exam_url", "⑪ 출발심사"),
    ("judge_url", "⑫ 경주심판"),
    ("jockey_change_url", "⑬ 기수변경"),
    ("weather_alert_url", "⑭ 기상특보"),
    ("corner_pace_url", "⑮ 코너/주로빠르기"),
    ("popularity_url", "⑯ 인기투표"),
    ("first_odds_url", "⑰ 1착마 적중승식"),
    ("second_odds_url", "⑱ 2착마 적중승식"),
    ("third_odds_url", "⑲ 3착마 적중승식"),
]

CORE_DEFAULT_API_KEYS = [
    "race_url", "entry_url", "body_url", "rating_url", "today_odds_url",
    "jockey_change_url", "corner_pace_url", "popularity_url",
]

# KRA official link: no auto-purchase, only a user-controlled jump to official page.
KRA_BUY_URLS = {
    "서울": "https://m.kra.co.kr",
    "부산경남": "https://m.kra.co.kr",
    "제주": "https://m.kra.co.kr",
}

# -----------------------------------------------------------------------------
# Time/settings helpers
# -----------------------------------------------------------------------------
def now_kst() -> datetime:
    return datetime.now(KST)


def today_kst() -> str:
    return now_kst().strftime("%Y%m%d")


def now_str() -> str:
    return now_kst().strftime("%Y-%m-%d %H:%M:%S")


def load_json_file(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def save_json_file(path: Path, payload: Any) -> bool:
    try:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def load_local_settings() -> Dict[str, Any]:
    return load_json_file(LOCAL_SETTINGS_FILE, {})


def save_local_settings(payload: Dict[str, Any]) -> bool:
    current = load_local_settings()
    current.update(payload)
    return save_json_file(LOCAL_SETTINGS_FILE, current)


def secret_get(names: List[str], default: str = "") -> str:
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


def get_api_key() -> str:
    if st.session_state.get("api_key_saved"):
        return str(st.session_state.get("api_key_saved", "")).strip()
    local = load_local_settings()
    if local.get("api_key"):
        return str(local.get("api_key", "")).strip()
    return secret_get(["API_KEY", "api_key", "PUBLIC_DATA_API_KEY", "SERVICE_KEY", "serviceKey"], "").strip()


def get_url(key: str) -> str:
    # URL can be overridden in Streamlit secrets/env, otherwise latest built-in URL is used.
    val = secret_get([key, key.upper()], "")
    if val:
        return val
    return FORCE_DEFAULT_URLS.get(key, "")


def kra_buy_url(meet: str = "서울") -> str:
    return KRA_BUY_URLS.get(str(meet), "https://m.kra.co.kr")


def mask_key(text: str) -> str:
    s = str(text or "")
    key = get_api_key()
    if key and key in s:
        if len(key) > 10:
            s = s.replace(key, key[:5] + "****" + key[-4:])
        else:
            s = s.replace(key, "****")
    return s

# -----------------------------------------------------------------------------
# CSS: mobile large mode
# -----------------------------------------------------------------------------
def css() -> None:
    st.markdown(
        """
<style>
.main .block-container {padding-top: 0.7rem; max-width: 1180px;}
.hero {
  background:linear-gradient(135deg,#031c49,#042a67,#001738);
  color:#fff; border-radius:30px; padding:28px 28px; box-shadow:0 10px 30px rgba(0,0,0,.18);
}
.hero h2 {font-size:3.0rem; line-height:1.05; margin:0; color:#fff; font-weight:1000; letter-spacing:-1px;}
.hero .muted {color:#d6ddf2; font-size:1.15rem; margin-top:8px; font-weight:800;}
.focus-card {
  background:#fff; border:5px solid #12a038; border-radius:34px; padding:28px 26px 24px 26px; box-shadow:0 8px 28px rgba(0,0,0,.08);
}
.focus-badge {display:inline-block; background:#e8f7e9; color:#13792f; padding:12px 26px; border-radius:18px; font-weight:1000; font-size:1.55rem; margin-bottom:14px;}
.focus-combo {font-size:clamp(4.8rem, 15vw, 8.6rem); font-weight:1000; color:#0b9d2e; text-align:center; letter-spacing:3px; line-height:1.0; margin:6px 0 16px 0;}
.reco-meta {font-size:1.45rem; color:#1f2937; font-weight:900; text-align:center; margin:8px 0 12px 0;}
.metric-wrap {display:flex; gap:14px;}
.metric-box {flex:1; text-align:center; padding:6px 8px; border-radius:18px; background:#f8fafc; border:1px solid #e5e7eb;}
.metric-box .m-title {font-size:1.25rem; font-weight:900; color:#172554; margin-bottom:6px;}
.metric-box .m-value-green {font-size:3.0rem; font-weight:1000; color:#109b2e; line-height:1.0;}
.metric-box .m-value-orange {font-size:3.0rem; font-weight:1000; color:#f48b00; line-height:1.0;}
.metric-box .m-value-blue {font-size:2.5rem; font-weight:1000; color:#1d4ed8; line-height:1.0;}
.manual-box {background:#fff7ed;border:3px solid #fb923c;border-radius:24px;padding:18px 18px;margin:14px 0;box-shadow:0 6px 20px rgba(0,0,0,.06);}
.manual-title {font-size:1.55rem;font-weight:1000;color:#9a3412;}
.manual-note {font-size:1.05rem;font-weight:800;color:#7c2d12;margin-top:6px;}
.bigline {font-size:2.3rem; font-weight:1000; color:#111827; text-align:center; padding:14px; background:#f8fafc; border:2px dashed #94a3b8; border-radius:20px;}
.info-box-ok {background:#efffed; border:1px solid rgba(25,135,84,.25); border-radius:18px; padding:15px 16px; font-size:1.1rem; font-weight:800;}
.info-box-warn {background:#fff7e8; border:1px solid rgba(217,119,6,.28); border-radius:18px; padding:15px 16px; font-size:1.1rem; font-weight:800;}
.stButton > button, .stLinkButton a {width:100%; border-radius:18px !important; min-height:58px !important; font-weight:900 !important; font-size:1.25rem !important;}
[data-testid="stMetricValue"] {font-size:2rem !important; font-weight:1000 !important;}
[data-testid="stExpander"] summary p {font-size:1.1rem !important; font-weight:900 !important;}
@media (max-width: 760px) {
  .main .block-container {padding:0.45rem 0.55rem 1.5rem 0.55rem;}
  .hero {border-radius:22px; padding:20px 18px;}
  .hero h2 {font-size:2.25rem; line-height:1.04;}
  .hero .muted {font-size:1rem;}
  .focus-card {border-radius:24px; padding:20px 12px 18px 12px; border-width:4px;}
  .focus-badge {font-size:1.1rem; padding:8px 14px; border-radius:14px;}
  .focus-combo {font-size:clamp(4.8rem, 21vw, 7.2rem); line-height:.95; margin:8px 0 12px 0;}
  .reco-meta {font-size:1.05rem; margin:4px 0 10px 0;}
  .metric-wrap {gap:4px;}
  .metric-box {padding:6px 3px;}
  .metric-box .m-title {font-size:.88rem; margin-bottom:6px;}
  .metric-box .m-value-green, .metric-box .m-value-orange {font-size:1.85rem;}
  .metric-box .m-value-blue {font-size:1.25rem; word-break:keep-all;}
  .bigline {font-size:1.45rem; padding:12px 8px;}
  .stButton > button, .stLinkButton a {min-height:64px !important; font-size:1.05rem !important;}
}
</style>
""",
        unsafe_allow_html=True,
    )

# -----------------------------------------------------------------------------
# API ON/OFF state
# -----------------------------------------------------------------------------
def default_onoff_state() -> Dict[str, bool]:
    return {k: (k in CORE_DEFAULT_API_KEYS) for k, _ in API_LABELS}


def get_api_switches() -> Dict[str, bool]:
    state = {}
    defaults = default_onoff_state()
    for k, _ in API_LABELS:
        state[k] = bool(st.session_state.get(f"api_on_{k}", defaults.get(k, True)))
    return state


def render_api_onoff_panel() -> None:
    with st.sidebar.expander("🔌 실시간 API ON/OFF", expanded=False):
        st.toggle(
            "전체 실시간 API 호출",
            value=st.session_state.get("api_master_on", True),
            key="api_master_on",
            help="끄면 API를 부르지 않고 캐시/샘플로 화면만 확인합니다.",
        )
        st.caption("현장에서 HTTP 500 나는 항목만 OFF 해도 앱은 계속 돌아갑니다.")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("핵심 ON", use_container_width=True):
                st.session_state["api_master_on"] = True
                for k, _ in API_LABELS:
                    st.session_state[f"api_on_{k}"] = k in CORE_DEFAULT_API_KEYS
                st.rerun()
        with c2:
            if st.button("전체 ON", use_container_width=True):
                st.session_state["api_master_on"] = True
                for k, _ in API_LABELS:
                    st.session_state[f"api_on_{k}"] = True
                st.rerun()
        with c3:
            if st.button("전체 OFF", use_container_width=True):
                st.session_state["api_master_on"] = False
                for k, _ in API_LABELS:
                    st.session_state[f"api_on_{k}"] = False
                st.rerun()

        defaults = default_onoff_state()
        for k, label in API_LABELS:
            st.toggle(label, value=st.session_state.get(f"api_on_{k}", defaults.get(k, True)), key=f"api_on_{k}")
        switches = get_api_switches()
        st.caption(f"현재 ON: {sum(1 for v in switches.values() if v)}/19개")

# -----------------------------------------------------------------------------
# API request/parsing
# -----------------------------------------------------------------------------
def add_or_replace_params(url: str, params: Dict[str, Any]) -> str:
    parsed = urlparse(url)
    q = dict(parse_qsl(parsed.query, keep_blank_values=True))
    for k, v in params.items():
        if v is not None and str(v) != "":
            q[k] = str(v)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, urlencode(q, doseq=True), parsed.fragment))


def endpoint_with_placeholders(url: str, rc_date: str, meet: str, race_no: int) -> str:
    key = get_api_key()
    repl = {
        "{serviceKey}": key,
        "{SERVICE_KEY}": key,
        "{api_key}": key,
        "{API_KEY}": key,
        "{today}": rc_date,
        "{ymd}": rc_date,
        "{rcDate}": rc_date,
        "{raceDate}": rc_date,
        "{raceNo}": str(race_no),
        "{rcNo}": str(race_no),
        "{meet}": meet,
        "{track_place}": meet,
    }
    out = str(url or "")
    for a, b in repl.items():
        out = out.replace(a, b)
    return out


def request_variants(base_url: str, rc_date: str, meet: str, race_no: int) -> List[str]:
    url = endpoint_with_placeholders(base_url, rc_date, meet, race_no)
    key = get_api_key()
    base_params = {"serviceKey": key, "pageNo": 1, "numOfRows": 100}
    variants: List[str] = []

    for typ_key, typ_val in [("resultType", "json"), ("_type", "json"), ("type", "json")]:
        p = dict(base_params)
        p[typ_key] = typ_val
        variants.append(add_or_replace_params(url, p))

    for date_name in ["rcDate", "raceDate", "meetDate", "ymd"]:
        for race_name in ["rcNo", "raceNo", "raceNum"]:
            p = dict(base_params)
            p.update({date_name: rc_date, race_name: race_no, "resultType": "json"})
            variants.append(add_or_replace_params(url, p))

    meet_map = {"서울": "1", "제주": "2", "부산경남": "3", "부경": "3", "부산": "3"}
    for meet_name in ["meet", "meetCd", "rcourse", "raceTrack"]:
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


def json_to_df(obj: Any) -> pd.DataFrame:
    if obj is None:
        return pd.DataFrame()
    candidates: Any = []
    if isinstance(obj, dict):
        paths = [
            ["response", "body", "items", "item"],
            ["response", "body", "item"],
            ["body", "items", "item"],
            ["items", "item"],
            ["data"],
            ["result"],
            ["list"],
        ]
        for path in paths:
            cur: Any = obj
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
            def walk(x: Any):
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
        try:
            return pd.DataFrame(candidates)
        except Exception:
            return pd.DataFrame()


def xml_to_df(txt: str) -> pd.DataFrame:
    try:
        root = ET.fromstring(txt)
        rows = []
        for item in root.findall(".//item"):
            rows.append({c.tag: c.text for c in item})
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


def save_live_cache(data: Dict[str, pd.DataFrame], status: pd.DataFrame) -> None:
    payload: Dict[str, Any] = {"saved_at": now_str(), "data": {}, "status": []}
    try:
        for k, df in data.items():
            if isinstance(df, pd.DataFrame) and not df.empty:
                payload["data"][k] = df.head(300).astype(str).to_dict("records")
        if isinstance(status, pd.DataFrame) and not status.empty:
            payload["status"] = status.astype(str).to_dict("records")
        save_json_file(LIVE_CACHE_FILE, payload)
    except Exception:
        pass


def load_live_cache() -> Dict[str, pd.DataFrame]:
    payload = load_json_file(LIVE_CACHE_FILE, {})
    out: Dict[str, pd.DataFrame] = {}
    try:
        for k, rows in payload.get("data", {}).items():
            df = pd.DataFrame(rows)
            if not df.empty:
                out[k] = df
    except Exception:
        pass
    return out


def fetch_one_api(key: str, rc_date: str, meet: str, race_no: int) -> Tuple[pd.DataFrame, str, str]:
    url = get_url(key)
    if not url:
        return pd.DataFrame(), "URL 없음", ""
    if not get_api_key() and "serviceKey=" not in url:
        return pd.DataFrame(), "API_KEY 없음", ""

    last_msg = ""
    last_url = ""
    for req_url in request_variants(url, rc_date, meet, race_no):
        last_url = req_url
        try:
            r = requests.get(req_url, timeout=12)
            if r.status_code != 200:
                last_msg = f"HTTP {r.status_code}"
                continue
            txt = r.text.strip()
            err_words = [
                "SERVICE_KEY_IS_NOT_REGISTERED",
                "INVALID_REQUEST_PARAMETER",
                "SERVICE_ACCESS_DENIED",
                "LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR",
                "NO_OPENAPI_SERVICE_ERROR",
            ]
            if any(w in txt for w in err_words):
                last_msg = txt[:180]
                continue
            ctype = r.headers.get("content-type", "").lower()
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
    return pd.DataFrame(), last_msg or "실패", last_url


def fetch_all_live(rc_date: str, meet: str, race_no: int, selected: List[str]) -> Tuple[Dict[str, pd.DataFrame], pd.DataFrame]:
    master_on = bool(st.session_state.get("api_master_on", True))
    switches = get_api_switches()
    data: Dict[str, pd.DataFrame] = {}
    status_rows: List[Dict[str, Any]] = []

    if not master_on:
        cache = load_live_cache()
        return cache, pd.DataFrame([{"API": "전체", "행수": sum(len(v) for v in cache.values()), "상태": "전체 OFF: 최근 캐시/샘플 사용", "URL": ""}])

    for key, label in API_LABELS:
        if key not in selected:
            status_rows.append({"API": label, "key": key, "행수": 0, "상태": "선택 안 함", "URL": ""})
            continue
        if not switches.get(key, True):
            status_rows.append({"API": label, "key": key, "행수": 0, "상태": "OFF: 건너뜀", "URL": ""})
            continue
        df, msg, used_url = fetch_one_api(key, rc_date, meet, race_no)
        if not df.empty:
            data[key] = df
        status_rows.append({"API": label, "key": key, "행수": int(len(df)), "상태": msg, "URL": mask_key(used_url)})
        time.sleep(0.05)

    status = pd.DataFrame(status_rows)
    if data:
        save_live_cache(data, status)
    else:
        cache = load_live_cache()
        if cache:
            data = cache
            status_rows.append({"API": "캐시", "key": "cache", "행수": sum(len(v) for v in cache.values()), "상태": "실시간 0건 → 최근 캐시 사용", "URL": ""})
            status = pd.DataFrame(status_rows)
    try:
        status.to_csv(API_STATUS_FILE, index=False, encoding="utf-8-sig")
    except Exception:
        pass
    return data, status

# -----------------------------------------------------------------------------
# Data normalization / scoring
# -----------------------------------------------------------------------------
def normalize_meet(x: Any) -> str:
    s = str(x or "").strip()
    if s in ["1", "서울", "SEOUL", "Seoul", "seoul"]:
        return "서울"
    if s in ["2", "제주", "JEJU", "Jeju", "jeju"]:
        return "제주"
    if s in ["3", "부산경남", "부경", "부산", "BUSAN", "Busan", "busan"]:
        return "부산경남"
    return s


def find_col(df: pd.DataFrame, names: List[str]) -> str | None:
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


def horse_no_col(df: pd.DataFrame) -> str | None:
    return find_col(df, ["chulNo", "출전번호", "출전마번", "마번", "horseNo", "hrNo", "no"])


def horse_name_col(df: pd.DataFrame) -> str | None:
    return find_col(df, ["hrName", "horseName", "마명", "경주마명", "name"])


def num_series(s: Any, default: float = 0) -> pd.Series:
    try:
        return pd.to_numeric(s, errors="coerce").fillna(default)
    except Exception:
        return pd.Series([], dtype=float)


def current_filter(df: pd.DataFrame, rc_date: str, meet: str, race_no: int) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    d = df.copy()
    original = d.copy()
    date_col = find_col(d, ["rcDate", "raceDate", "meetDate", "날짜", "경주일자"])
    meet_col = find_col(d, ["meet", "meetCd", "rcourse", "경마장"])
    rc_col = find_col(d, ["rcNo", "raceNo", "경주번호"])

    try:
        if date_col:
            ds = d[date_col].astype(str).str.replace("-", "", regex=False).str.strip()
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


def sample_data() -> pd.DataFrame:
    # Realistic fallback so field use never stops when data is unstable.
    return pd.DataFrame([
        {"마번": 5, "마명": "마루스피드", "레이팅": 78, "최근순위": 2, "승률": 18, "복승률": 42, "예상배당": 9.2, "체중변화": -2, "기수점수": 75, "인기": 4},
        {"마번": 11, "마명": "그린파워", "레이팅": 75, "최근순위": 3, "승률": 15, "복승률": 38, "예상배당": 7.8, "체중변화": -1, "기수점수": 72, "인기": 5},
        {"마번": 2, "마명": "블루런", "레이팅": 72, "최근순위": 4, "승률": 12, "복승률": 35, "예상배당": 12.5, "체중변화": 0, "기수점수": 69, "인기": 7},
        {"마번": 7, "마명": "라스트킹", "레이팅": 70, "최근순위": 5, "승률": 10, "복승률": 30, "예상배당": 15.4, "체중변화": 2, "기수점수": 67, "인기": 8},
        {"마번": 3, "마명": "해피로드", "레이팅": 66, "최근순위": 6, "승률": 8, "복승률": 25, "예상배당": 22.0, "체중변화": -4, "기수점수": 65, "인기": 9},
        {"마번": 9, "마명": "스톰로드", "레이팅": 64, "최근순위": 7, "승률": 7, "복승률": 20, "예상배당": 31.0, "체중변화": 1, "기수점수": 62, "인기": 10},
    ])


def build_base_horses(data: Dict[str, pd.DataFrame], rc_date: str, meet: str, race_no: int) -> pd.DataFrame:
    priority = ["entry_url", "body_url", "gear_url", "today_odds_url", "odds_url", "rating_url", "horse_url"]
    rows: Dict[int, Dict[str, Any]] = {}
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
            rows.setdefault(n, {"마번": n, "마명": f"{n}번", "근거API": []})
            if name_col and str(r.get(name_col, "")).strip():
                rows[n]["마명"] = str(r.get(name_col)).strip()
            rows[n]["근거API"].append(key.replace("_url", ""))
    if not rows:
        return sample_data()
    return pd.DataFrame(list(rows.values())).sort_values("마번")


def merge_score_features(base: pd.DataFrame, data: Dict[str, pd.DataFrame], rc_date: str, meet: str, race_no: int) -> pd.DataFrame:
    h = base.copy()
    defaults = {"레이팅": 60, "최근순위": 5, "승률": 8, "복승률": 25, "예상배당": 12.0, "체중변화": 0, "기수점수": 65, "인기": 7}
    for c, v in defaults.items():
        if c not in h.columns:
            h[c] = v

    def map_by_no(key: str, target_col: str, candidate_cols: List[str]):
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

    map_by_no("rating_url", "레이팅", ["rating", "레이팅", "rt", "ratingValue"])
    map_by_no("race_record_url", "최근순위", ["ord", "rank", "chaksun", "최근순위", "순위"])
    map_by_no("odds_url", "예상배당", ["odds", "배당", "winOdds", "dividend", "배당률"])
    map_by_no("today_odds_url", "예상배당", ["odds", "배당", "winOdds", "dividend", "배당률"])
    map_by_no("body_url", "체중변화", ["wgBudam", "weightDiff", "체중변화", "증감", "diff"])
    map_by_no("popularity_url", "인기", ["popRank", "popularity", "인기", "인기순위"])
    map_by_no("jockey_change_url", "기수점수", ["jockeyScore", "기수점수"])

    fallback = sample_data()
    for c in defaults:
        fb = float(pd.to_numeric(fallback[c], errors="coerce").median()) if c in fallback else defaults[c]
        h[c] = pd.to_numeric(h[c], errors="coerce").fillna(fb)
    return h


def fetch_weather(meet: str) -> Dict[str, Any]:
    coords = {"서울": (37.4438, 127.0165), "부산경남": (35.1545, 128.8782), "제주": (33.4097, 126.3934)}
    lat, lon = coords.get(meet, coords["서울"])
    env = {"날씨": "기본", "강수": 0.0, "바람": 0.0, "주로": "양호", "모래": "보통"}
    # Weather is best-effort only. If it fails, the app still runs.
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation,weather_code,wind_speed_10m&timezone=Asia%2FSeoul"
        cur = requests.get(url, timeout=6).json().get("current", {})
        precip = float(cur.get("precipitation", 0) or 0)
        wind = float(cur.get("wind_speed_10m", 0) or 0)
        code = int(cur.get("weather_code", 0) or 0)
        weather = "비" if precip >= 0.3 or code in [51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99] else ("흐림" if code in [1, 2, 3, 45, 48] else "맑음")
        track = "포화" if precip >= 3 else ("다습" if precip >= 0.3 else "양호")
        sand = "무거움" if precip >= 1 else "보통"
        env = {"날씨": weather, "강수": precip, "바람": wind, "주로": track, "모래": sand}
    except Exception:
        pass
    return env


def score_and_recommend(h: pd.DataFrame, env: Dict[str, Any], sim_count: int = 1200, risk_mode: str = "균형형") -> Tuple[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]:
    x = h.copy()
    recent_score = (10 - num_series(x["최근순위"], 5).clip(1, 10)) * 4.0
    rating_score = (num_series(x["레이팅"], 60).clip(40, 100) - 40) * 0.85
    win_score = num_series(x["승률"], 8).clip(0, 50) * 0.9
    place_score = num_series(x["복승률"], 25).clip(0, 80) * 0.45
    odds = num_series(x["예상배당"], 12).clip(1, 100)
    value_score = odds.apply(lambda v: 18 if 6 <= v <= 25 else (11 if 25 < v <= 45 else 4))
    weight_delta = num_series(x["체중변화"], 0)
    weight_score = weight_delta.apply(lambda v: 7 if -3 <= v <= -1 else (2 if v == 0 else (-8 if abs(v) >= 5 else -2)))
    jockey_score = num_series(x["기수점수"], 65) * 0.25
    pop_score = (10 - num_series(x["인기"], 7).clip(1, 10)) * 1.2
    env_bonus = 2 if env.get("주로") == "양호" else -1

    x["점수"] = recent_score + rating_score + win_score + place_score + value_score + weight_score + jockey_score + pop_score + env_bonus
    x["위험"] = odds.apply(lambda v: "중" if v <= 25 else "높음")
    x["근거"] = x.apply(lambda r: f"레이팅 {int(r['레이팅'])} / 최근 {int(r['최근순위'])}위 / 배당 {round(float(r['예상배당']),1)}", axis=1)
    x = x.sort_values("점수", ascending=False).reset_index(drop=True)

    nums = x["마번"].astype(int).tolist()
    scores = x["점수"].astype(float).tolist()
    volatility = 5.5 + (1.5 if env.get("주로") in ["다습", "포화"] else 0)
    if risk_mode == "안전형":
        volatility *= 0.88
    elif risk_mode == "공격형":
        volatility *= 1.15

    random.seed(42)
    counts: Dict[Tuple[str, str, str], int] = {}
    sim_count = max(300, int(sim_count))
    for _ in range(sim_count):
        noisy = [(n, s + random.gauss(0, volatility)) for n, s in zip(nums, scores)]
        top3 = tuple(str(n) for n, _ in sorted(noisy, key=lambda a: a[1], reverse=True)[:3])
        if len(top3) == 3:
            counts[top3] = counts.get(top3, 0) + 1

    combos = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:15]
    if combos:
        top_combo = combos[0][0]
        combo_txt = " - ".join(top_combo)
        confidence = min(94, max(35, int(combos[0][1] / sim_count * 100 + 50)))
    else:
        combo_txt = "-"
        confidence = 0

    defense = "-"
    if len(x) >= 4:
        defense = f"{int(x.iloc[0]['마번'])} - {int(x.iloc[1]['마번'])} - {int(x.iloc[3]['마번'])}"

    if len(x) >= 2:
        bok = f"{int(x.iloc[0]['마번'])} - {int(x.iloc[1]['마번'])}"
    else:
        bok = "-"

    avg_odds = float(num_series(x.head(3)["예상배당"], 10).mean()) if len(x) else 0
    decision = "소액 공격" if confidence >= 75 else ("소액 가능" if confidence >= 62 else "관망")
    amount = 1000 if decision != "관망" else 0

    result = {
        "판정": decision,
        "복승": bok,
        "공격삼쌍승": combo_txt,
        "방어삼복승": defense,
        "예상배당": round(avg_odds, 1),
        "신뢰도": confidence,
        "추천금액": amount,
        "근거": " · ".join([f"{int(r['마번'])}번 {r.get('마명','')} 점수상위" for _, r in x.head(3).iterrows()]),
    }
    combo_rows = [{"조합": " - ".join(k), "반복횟수": v, "비율": round(v / sim_count * 100, 1)} for k, v in combos]
    return x, result, combo_rows

# -----------------------------------------------------------------------------
# Hub / sheets helpers
# -----------------------------------------------------------------------------
def load_local_hub() -> pd.DataFrame:
    if LOCAL_HUB_FILE.exists():
        try:
            return pd.read_csv(LOCAL_HUB_FILE)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def append_csv(path: Path, row: Dict[str, Any]) -> int:
    old = pd.DataFrame()
    if path.exists():
        try:
            old = pd.read_csv(path)
        except Exception:
            old = pd.DataFrame()
    new = pd.concat([old, pd.DataFrame([row])], ignore_index=True)
    new.to_csv(path, index=False, encoding="utf-8-sig")
    return len(new)


def append_local_hub(row: Dict[str, Any]) -> int:
    return append_csv(LOCAL_HUB_FILE, row)


def sheets_secret_get(names: List[str], default: Any = "") -> Any:
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
    sheet_id = sheets_secret_get(["SHEET_ID", "sheet_id"], "")
    if not sheet_id:
        return None, None, "SHEET_ID 없음"
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        raw = sheets_secret_get(["SERVICE_ACCOUNT_JSON", "service_account_json"], "")
        info = None
        if raw:
            info = json.loads(raw) if isinstance(raw, str) else dict(raw)
        elif "google_sheets" in st.secrets and "service_account" in st.secrets["google_sheets"]:
            info = dict(st.secrets["google_sheets"]["service_account"])
        if not info:
            return None, None, "SERVICE_ACCOUNT_JSON 없음"
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(info, scopes=scopes)
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(str(sheet_id))
        return sh, sheet_id, "OK"
    except Exception as e:
        return None, sheet_id, str(e)[:180]


def hub_append_sheet(tab_name: str, row: Dict[str, Any]) -> Tuple[bool, str]:
    sh, sheet_id, msg = get_gsheet_client()
    if sh is None:
        return False, msg
    try:
        try:
            ws = sh.worksheet(tab_name)
        except Exception:
            ws = sh.add_worksheet(title=tab_name, rows=1000, cols=40)
        existing = ws.get_all_values()
        if not existing:
            headers = list(row.keys())
            ws.append_row(headers)
        else:
            headers = existing[0]
            for k in row.keys():
                if k not in headers:
                    headers.append(k)
            if headers != existing[0]:
                ws.update("1:1", [headers])
        ws.append_row([str(row.get(h, "")) for h in headers])
        return True, "OK"
    except Exception as e:
        return False, str(e)[:180]


def hub_read_sheet(tab_name: str, limit: int = 100) -> pd.DataFrame:
    sh, sheet_id, msg = get_gsheet_client()
    if sh is None:
        return pd.DataFrame()
    try:
        ws = sh.worksheet(tab_name)
        rows = ws.get_all_records()
        df = pd.DataFrame(rows)
        if limit:
            return df.tail(limit)
        return df
    except Exception:
        return pd.DataFrame()

# -----------------------------------------------------------------------------
# Manual purchase helper: no auto-buy
# -----------------------------------------------------------------------------
def maru_clean_combo_text(combo: Any) -> str:
    try:
        text = str(combo or "-").replace("번", "").replace(" ", "")
        text = text.replace(">", "-").replace("/", "-").replace(",", "-")
        parts = [p for p in text.split("-") if p.strip()]
        nums = []
        for p in parts:
            m = re.search(r"\d+", str(p))
            if m:
                nums.append(str(int(m.group(0))))
        return " - ".join(nums) if nums else str(combo or "-")
    except Exception:
        return str(combo or "-")


def maru_purchase_line(rc_date: str, meet: str, race_no: int, bet_type: str, combo: Any, amount: int) -> str:
    try:
        amount_txt = f"{int(amount):,}원"
    except Exception:
        amount_txt = str(amount or "")
    return f"{rc_date} / {meet} {int(race_no)}R / {bet_type} / {maru_clean_combo_text(combo)} / {amount_txt}"


def render_manual_purchase_box(rc_date: str, meet: str, race_no: int, result: Dict[str, Any]) -> None:
    attack_combo = maru_clean_combo_text(result.get("공격삼쌍승", "-"))
    defend_combo = maru_clean_combo_text(result.get("방어삼복승", "-"))
    bok_combo = maru_clean_combo_text(result.get("복승", "-"))
    try:
        default_amount = int(result.get("추천금액", 1000) or 1000)
        if default_amount <= 0:
            default_amount = 1000
    except Exception:
        default_amount = 1000

    st.markdown(
        """
<div class="manual-box">
  <div class="manual-title">⚡ 10초 수동구매 모드</div>
  <div class="manual-note">추천조합을 크게 확인하고, 공식 마권구매 페이지에서 직접 입력·확정하는 방식입니다.</div>
</div>
""",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        bet_pick = st.selectbox(
            "구매 방식 선택",
            ["복승 추천", "삼쌍승 공격", "삼복승 방어", "단승/연승 수동"],
            index=0,
            key=f"maru_bet_pick_{meet}_{race_no}",
        )
    with c2:
        amount = st.number_input(
            "수동 입력 금액",
            min_value=1000,
            max_value=100000,
            value=min(max(default_amount, 1000), 100000),
            step=1000,
            key=f"maru_amount_{meet}_{race_no}",
        )

    if "삼복승" in bet_pick:
        default_combo, bet_type = defend_combo, "삼복승"
    elif "삼쌍승" in bet_pick:
        default_combo, bet_type = attack_combo, "삼쌍승"
    elif "단승" in bet_pick:
        default_combo = attack_combo.split(" - ")[0] if attack_combo and attack_combo != "-" else ""
        bet_type = "단승/연승"
    else:
        default_combo, bet_type = bok_combo, "복승"

    combo_input = st.text_input(
        "공식 구매페이지에 수동 입력할 마번",
        value=default_combo,
        key=f"maru_combo_input_{meet}_{race_no}_{bet_type}",
    )
    line = maru_purchase_line(rc_date, meet, race_no, bet_type, combo_input, amount)
    st.markdown(f"<div class='bigline'>{line}</div>", unsafe_allow_html=True)
    st.code(line, language="text")

    b1, b2 = st.columns(2)
    with b1:
        st.link_button("↗ 공식 마권구매 페이지 열기", kra_buy_url(meet), use_container_width=True)
    with b2:
        st.button("📋 위 조합 보고 직접 입력", use_container_width=True)
    st.caption("※ 자동구매·자동결제 아님. 공식 화면에서 경마장/경주번호/승식/마번/금액을 직접 확인 후 구매 확정하세요.")

# -----------------------------------------------------------------------------
# Schedule / bigdata helpers
# -----------------------------------------------------------------------------
def extract_race_schedule(data: Dict[str, pd.DataFrame], rc_date: str, meet: str) -> pd.DataFrame:
    race_df = data.get("race_url", pd.DataFrame())
    if race_df is None or race_df.empty:
        rows = []
        start = datetime.strptime(rc_date, "%Y%m%d").replace(tzinfo=KST, hour=10, minute=30)
        for i in range(1, 12):
            rows.append({"날짜": rc_date, "경마장": meet, "경주": i, "발주시각": (start + timedelta(minutes=35 * (i - 1))).strftime("%H:%M"), "상태": "샘플"})
        return pd.DataFrame(rows)
    d = race_df.copy()
    rc_col = find_col(d, ["rcNo", "raceNo", "경주번호"])
    time_col = find_col(d, ["rcTime", "raceTime", "발주시각", "time"])
    rows = []
    for _, r in d.iterrows():
        rows.append({
            "날짜": rc_date,
            "경마장": meet,
            "경주": r.get(rc_col, "") if rc_col else "",
            "발주시각": r.get(time_col, "") if time_col else "",
            "상태": "실시간",
        })
    return pd.DataFrame(rows)


def maybe_auto_hub(rc_date: str, meet: str, race_no: int, result: Dict[str, Any], live_rows: int, enabled: bool) -> None:
    if not enabled:
        return
    key = f"{rc_date}_{meet}_{race_no}"
    state = load_json_file(AUTO_RUN_STATE_FILE, {})
    today_state = state.get(rc_date, {})
    # avoid duplicate autosave per race
    if today_state.get(key):
        return
    if int(result.get("신뢰도", 0)) >= 70 and result.get("판정") != "관망":
        row = {
            "저장시각": now_str(),
            "날짜": rc_date,
            "경마장": meet,
            "경주번호": race_no,
            "공격삼쌍승": result.get("공격삼쌍승", ""),
            "방어삼복승": result.get("방어삼복승", ""),
            "복승": result.get("복승", ""),
            "예상배당": result.get("예상배당", ""),
            "신뢰도": result.get("신뢰도", ""),
            "추천금액": result.get("추천금액", ""),
            "판정": result.get("판정", ""),
            "실시간행수": live_rows,
            "자동저장": "Y",
        }
        append_local_hub(row)
        try:
            append_csv(BIGDATA_FILE, row)
        except Exception:
            pass
        today_state[key] = now_str()
        state[rc_date] = today_state
        save_json_file(AUTO_RUN_STATE_FILE, state)

# -----------------------------------------------------------------------------
# Render UI
# -----------------------------------------------------------------------------
def render_focus_dashboard(rc_date: str, meet: str, race_no: int, score_df: pd.DataFrame, result: Dict[str, Any], env: Dict[str, Any], live_rows: int, status: pd.DataFrame, combos: List[Dict[str, Any]]) -> None:
    st.markdown("### 🔥 지금 놓치면 아까운 추천")
    top_combo = result.get("복승", result.get("공격삼쌍승", "-"))
    st.markdown(
        f"""
<div class="focus-card">
  <div class="focus-badge">{meet} {race_no}R · {result.get('판정','대기')}</div>
  <div class="reco-meta">복승 우선 / 삼쌍승 공격은 아래에서 확인</div>
  <div class="focus-combo">{maru_clean_combo_text(top_combo)}</div>
  <div class="metric-wrap">
    <div class="metric-box"><div class="m-title">신뢰도</div><div class="m-value-green">{result.get('신뢰도',0)}%</div></div>
    <div class="metric-box"><div class="m-title">예상배당</div><div class="m-value-orange">{result.get('예상배당',0)}배</div></div>
    <div class="metric-box"><div class="m-title">실시간행</div><div class="m-value-blue">{live_rows}</div></div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.write("")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("날씨", env.get("날씨", "-"))
    c2.metric("주로", env.get("주로", "-"))
    c3.metric("바람", f"{env.get('바람', 0)}")
    c4.metric("추천금액", f"{int(result.get('추천금액', 0)):,}원")

    st.markdown(f"**근거:** {result.get('근거','')}")
    if live_rows == 0:
        st.warning("실시간 API 데이터 0건입니다. 앱은 멈추지 않고 샘플/최근 캐시 보정 분석으로 계속 표시합니다.")
    else:
        st.success(f"실시간 API 데이터 {live_rows}행 반영")

    render_manual_purchase_box(rc_date, meet, race_no, result)

    with st.expander("상세 데이터 크게 보기", expanded=False):
        show_cols = [c for c in ["마번", "마명", "점수", "최근순위", "레이팅", "예상배당", "체중변화", "기수점수", "인기", "위험", "근거"] if c in score_df.columns]
        st.dataframe(score_df[show_cols] if show_cols else score_df, use_container_width=True, height=380)
        st.markdown("#### 시뮬레이션 조합")
        st.dataframe(pd.DataFrame(combos), use_container_width=True, height=260)

    with st.expander("API 상태 요약", expanded=False):
        if isinstance(status, pd.DataFrame) and not status.empty:
            keep_cols = [c for c in ["API", "행수", "상태"] if c in status.columns]
            st.dataframe(status[keep_cols].head(30) if keep_cols else status.head(30), use_container_width=True, height=320)
        else:
            st.info("아직 API 호출 전입니다.")


def render() -> None:
    css()
    st.markdown(
        """
<div class="hero">
<h2>MARU KRA 실전 대시보드</h2>
<div class="muted">실시간 19API · API ON/OFF · 실패방어 · 허브저장 · 10초 수동구매 모드</div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.caption("자동구매/자동결제 없음. 공식 구매 페이지로 이동 후 사용자가 직접 입력·확정합니다.")

    with st.sidebar:
        st.title("🐎 MARU KRA")
        st.success("덮어쓰기용 ALL-IN-ONE app.py")
        st.info(f"현재 한국시간: {now_kst().strftime('%Y-%m-%d %H:%M:%S')} KST")

        current_key = get_api_key()
        key_input = st.text_input("공공데이터 API Key", value=current_key, type="password", placeholder="공공데이터 일반 인증키 입력")
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
        meet = st.selectbox("경마장", ["서울", "부산경남", "제주"], index=0)
        race_no = st.number_input("경주번호", min_value=1, max_value=20, value=1, step=1)
        sim_count = st.slider("시뮬레이션", 300, 5000, 1200, step=100)
        risk_mode = st.selectbox("전략", ["균형형", "안전형", "공격형"], index=0)
        auto_refresh = st.selectbox("자동 새로고침", [0, 30, 60, 120, 300], index=1)
        auto_schedule_enabled = st.checkbox("자동 허브 스케줄 실행", value=True)
        st.caption("신뢰도 높은 추천은 로컬 허브에 자동 기록됩니다. 구매는 직접 판단하세요.")
        render_api_onoff_panel()
        st.divider()

        selected = [k for k, _ in API_LABELS if st.session_state.get(f"api_on_{k}", default_onoff_state().get(k, True))]
        with st.expander("API URL 확인/복사용", expanded=False):
            for k, label in API_LABELS:
                st.caption(f"{label}: {get_url(k)}")
        st.link_button("KRA 공식 바로가기", kra_buy_url(meet), use_container_width=True)

    rc_date = str(target_date).replace("-", "").strip() or today_kst()
    race_no_int = int(race_no)

    # Initial / refresh fetch
    if "live_data" not in st.session_state:
        st.session_state["live_data"] = {}
        st.session_state["api_status"] = pd.DataFrame()
        st.session_state["last_fetch_key"] = ""

    fetch_key = f"{rc_date}_{meet}_{race_no_int}_{','.join(selected)}_{st.session_state.get('api_master_on', True)}"

    tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔥 실전 대시보드", "🏇 실시간 분석", "📦 허브", "🔌 API 진단", "📊 시간표/빅데이터", "📘 Secrets"])

    with tab1:
        st.markdown("### 실시간 KRA 분석")
        col_a, col_b, col_c = st.columns([1, 1, 1])
        with col_a:
            run = st.button("실시간 데이터 불러오기", type="primary", use_container_width=True)
        with col_b:
            run_sim = st.button("불러오기 + 시뮬레이션", use_container_width=True)
        with col_c:
            clear_cache = st.button("화면 캐시 초기화", use_container_width=True)
        if clear_cache:
            st.session_state["live_data"] = {}
            st.session_state["api_status"] = pd.DataFrame()
            st.session_state["last_fetch_key"] = ""
            st.rerun()

        if run or run_sim or not st.session_state["live_data"] or st.session_state.get("last_fetch_key") != fetch_key:
            data, status = fetch_all_live(rc_date, meet, race_no_int, selected)
            st.session_state["live_data"] = data
            st.session_state["api_status"] = status
            st.session_state["last_fetch_key"] = fetch_key

        data = st.session_state["live_data"]
        status = st.session_state["api_status"]
        env = fetch_weather(meet)
        base = build_base_horses(data, rc_date, meet, race_no_int)
        horses = merge_score_features(base, data, rc_date, meet, race_no_int)
        score_df, result, combos = score_and_recommend(horses, env, sim_count, risk_mode)
        live_rows = sum(len(v) for v in data.values()) if data else 0
        render_focus_dashboard(rc_date, meet, race_no_int, score_df, result, env, live_rows, status, combos)

        if st.button("현재 분석 허브 저장", type="primary", use_container_width=True):
            row = {
                "저장시각": now_str(),
                "날짜": rc_date,
                "경마장": meet,
                "경주번호": race_no_int,
                "복승": result.get("복승", ""),
                "공격삼쌍승": result.get("공격삼쌍승", ""),
                "방어삼복승": result.get("방어삼복승", ""),
                "예상배당": result.get("예상배당", 0),
                "신뢰도": result.get("신뢰도", 0),
                "추천금액": result.get("추천금액", 0),
                "판정": result.get("판정", ""),
                "날씨": env.get("날씨", ""),
                "주로": env.get("주로", ""),
                "강수": env.get("강수", ""),
                "바람": env.get("바람", ""),
                "실시간행수": live_rows,
                "근거": result.get("근거", ""),
                "결과상태": "대기",
                "성공실패": "",
                "실제결과": "",
                "복기메모": "",
            }
            n = append_local_hub(row)
            append_csv(BIGDATA_FILE, row)
            ok, msg = hub_append_sheet("recommendations", row)
            try:
                hub_append_sheet("bigdata_result_log", row)
            except Exception:
                pass
            if ok:
                st.success(f"허브 저장 완료: Google Sheet + 로컬 {n}건 + 빅데이터")
            else:
                st.info(f"로컬 허브 저장 완료 {n}건 + 빅데이터 / Google Sheet: {msg}")

        maybe_auto_hub(rc_date, meet, race_no_int, result, live_rows, auto_schedule_enabled)

    # For dashboard tab, reuse same session state or compute fallback quickly.
    with tab0:
        data = st.session_state.get("live_data", {})
        status = st.session_state.get("api_status", pd.DataFrame())
        env = fetch_weather(meet)
        base = build_base_horses(data, rc_date, meet, race_no_int)
        horses = merge_score_features(base, data, rc_date, meet, race_no_int)
        score_df, result, combos = score_and_recommend(horses, env, sim_count, risk_mode)
        live_rows = sum(len(v) for v in data.values()) if data else 0
        render_focus_dashboard(rc_date, meet, race_no_int, score_df, result, env, live_rows, status, combos)

    with tab2:
        st.markdown("### 허브 저장/불러오기")
        sheet_df = hub_read_sheet("recommendations", 100)
        if not sheet_df.empty:
            st.success(f"Google Sheet 허브 {len(sheet_df)}건 불러옴")
            st.dataframe(sheet_df, use_container_width=True, height=420)
        else:
            st.info("Google Sheet 허브가 없거나 비어 있습니다. 로컬 허브를 표시합니다.")
            st.dataframe(load_local_hub().tail(100), use_container_width=True, height=420)
        with st.expander("로컬 파일 위치", expanded=False):
            st.code(str(LOCAL_HUB_FILE), language="text")
            st.code(str(BIGDATA_FILE), language="text")

    with tab3:
        st.markdown("### API 진단")
        status = st.session_state.get("api_status", pd.DataFrame())
        if isinstance(status, pd.DataFrame) and not status.empty:
            st.dataframe(status, use_container_width=True, height=420)
        else:
            st.write("아직 API 호출 전입니다.")
        st.markdown("#### 19개 API URL")
        rows = []
        switches = get_api_switches()
        for k, label in API_LABELS:
            rows.append({"ON": switches.get(k, True), "API": label, "key": k, "URL": get_url(k)})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, height=420)

    with tab4:
        st.markdown("### 경주 시간표 / 빅데이터 복기")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("오늘 시간표 지금 수집/허브저장", use_container_width=True):
                data_s, status_s = fetch_all_live(rc_date, meet, race_no_int, ["race_url"])
                schedule_df = extract_race_schedule(data_s, rc_date, meet)
                schedule_df.to_csv(SCHEDULE_HUB_FILE, index=False, encoding="utf-8-sig")
                st.success(f"시간표 저장 완료: {len(schedule_df)}건")
                st.dataframe(schedule_df, use_container_width=True)
        with c2:
            st.caption("빅데이터 복기 파일은 허브 저장 때 자동 누적됩니다.")
            if BIGDATA_FILE.exists():
                try:
                    st.dataframe(pd.read_csv(BIGDATA_FILE).tail(100), use_container_width=True, height=360)
                except Exception:
                    st.warning("빅데이터 파일을 읽지 못했습니다.")
            else:
                st.info("아직 빅데이터 저장 기록이 없습니다.")
        if SCHEDULE_HUB_FILE.exists():
            with st.expander("저장된 시간표 보기", expanded=False):
                try:
                    st.dataframe(pd.read_csv(SCHEDULE_HUB_FILE).tail(100), use_container_width=True)
                except Exception:
                    st.info("시간표 파일 없음")

    with tab5:
        st.markdown("### Secrets / 배포 체크")
        st.info("Streamlit Cloud에서는 Secrets에 API_KEY, SHEET_ID, SERVICE_ACCOUNT_JSON을 넣으면 됩니다. 로컬에서는 왼쪽 API Key 저장만 해도 됩니다.")
        st.code(
            """
[maru]
API_KEY = "공공데이터_일반_인증키"

[google_sheets]
SHEET_ID = "구글시트_ID"
SERVICE_ACCOUNT_JSON = "{...서비스계정 JSON...}"
""".strip(),
            language="toml",
        )
        st.warning("마권 구매는 반드시 공식 페이지에서 직접 확인 후 수동으로만 진행하세요. 이 앱은 자동구매/자동결제를 하지 않습니다.")

    if auto_refresh and int(auto_refresh) > 0:
        try:
            time.sleep(int(auto_refresh))
            st.rerun()
        except Exception:
            pass


if __name__ == "__main__":
    render()
