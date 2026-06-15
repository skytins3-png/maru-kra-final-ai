# -*- coding: utf-8 -*-
"""
MARU KRA FINAL ALL-IN-ONE APP - STABLE BET INTEGRATED
- 덮어쓰기용 단일 app.py
- 기존 핵심 기능 유지형: 19개 KRA/기상 API URL, API별 ON/OFF, 전체 실시간 ON/OFF
- HTTP 500/무응답/0건이어도 앱 중단 없이 최근 캐시/샘플로 계속 분석
- 실시간 분석, 허브 저장, API 진단, 시간표/빅데이터, 10초 수동구매 모드 포함
- 추가 통합: 마권 승식 설명 + 3만원 안정 분할 + 예상 배당/환급/손익 계산
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
from typing import Dict, List, Tuple, Any, Optional

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
# 19 default API URLs
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

KRA_BUY_URLS = {
    "서울": "https://m.kra.co.kr",
    "부산경남": "https://m.kra.co.kr",
    "제주": "https://m.kra.co.kr",
}

# -----------------------------------------------------------------------------
# Helpers
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
        s = s.replace(key, key[:5] + "****" + key[-4:] if len(key) > 10 else "****")
    return s


def safe_int(x: Any, default: int = 0) -> int:
    try:
        return int(float(str(x).replace(",", "")))
    except Exception:
        return default


def safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(str(x).replace(",", ""))
    except Exception:
        return default

# -----------------------------------------------------------------------------
# CSS
# -----------------------------------------------------------------------------
def css() -> None:
    st.markdown(
        """
<style>
.main .block-container {padding-top: 0.7rem; max-width: 1180px;}
.hero {background:linear-gradient(135deg,#031c49,#042a67,#001738); color:#fff; border-radius:30px; padding:28px 28px; box-shadow:0 10px 30px rgba(0,0,0,.18);}
.hero h2 {font-size:3.0rem; line-height:1.05; margin:0; color:#fff; font-weight:1000; letter-spacing:-1px;}
.hero .muted {color:#d6ddf2; font-size:1.15rem; margin-top:8px; font-weight:800;}
.focus-card {background:#fff; border:5px solid #12a038; border-radius:34px; padding:28px 26px 24px 26px; box-shadow:0 8px 28px rgba(0,0,0,.08);}
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
.betting-card {background:#ffffff;border:3px solid #0ea5e9;border-radius:26px;padding:18px 18px;margin:12px 0;box-shadow:0 6px 20px rgba(0,0,0,.06);}
.betting-title {font-size:1.45rem;font-weight:1000;color:#075985;margin-bottom:8px;}
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
# API ON/OFF
# -----------------------------------------------------------------------------
def default_onoff_state() -> Dict[str, bool]:
    return {k: (k in CORE_DEFAULT_API_KEYS) for k, _ in API_LABELS}


def get_api_switches() -> Dict[str, bool]:
    defaults = default_onoff_state()
    return {k: bool(st.session_state.get(f"api_on_{k}", defaults.get(k, True))) for k, _ in API_LABELS}


def render_api_onoff_panel() -> None:
    with st.sidebar.expander("🔌 실시간 API ON/OFF", expanded=False):
        st.toggle("전체 실시간 API 호출", value=st.session_state.get("api_master_on", True), key="api_master_on", help="끄면 API를 부르지 않고 캐시/샘플로 화면만 확인합니다.")
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
        "{serviceKey}": key, "{SERVICE_KEY}": key, "{api_key}": key, "{API_KEY}": key,
        "{today}": rc_date, "{ymd}": rc_date, "{rcDate}": rc_date, "{raceDate}": rc_date,
        "{raceNo}": str(race_no), "{rcNo}": str(race_no), "{meet}": meet, "{track_place}": meet,
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
            ["response", "body", "items", "item"], ["response", "body", "item"],
            ["body", "items", "item"], ["items", "item"], ["data"], ["result"], ["list"],
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
    last_msg, last_url = "", ""
    for req_url in request_variants(url, rc_date, meet, race_no):
        last_url = req_url
        try:
            r = requests.get(req_url, timeout=12)
            if r.status_code != 200:
                last_msg = f"HTTP {r.status_code}"
                continue
            txt = r.text.strip()
            err_words = [
                "SERVICE_KEY_IS_NOT_REGISTERED", "INVALID_REQUEST_PARAMETER", "SERVICE_ACCESS_DENIED",
                "LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR", "NO_OPENAPI_SERVICE_ERROR",
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
        time.sleep(0.03)
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


def find_col(df: pd.DataFrame, names: List[str]) -> Optional[str]:
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


def horse_no_col(df: pd.DataFrame) -> Optional[str]:
    return find_col(df, ["chulNo", "출전번호", "출전마번", "마번", "horseNo", "hrNo", "no"])


def horse_name_col(df: pd.DataFrame) -> Optional[str]:
    return find_col(df, ["hrName", "horseName", "마명", "경주마명", "name"])


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
    env = {"날씨": "기본", "강수": 0.0, "바람": 2.0, "주로": "표준", "기온": 20.0}
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation,wind_speed_10m&timezone=Asia%2FSeoul"
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            cur = r.json().get("current", {})
            rain = float(cur.get("precipitation", 0) or 0)
            wind = float(cur.get("wind_speed_10m", 0) or 0)
            temp = float(cur.get("temperature_2m", 20) or 20)
            env.update({"강수": rain, "바람": wind, "기온": temp})
            env["날씨"] = "비" if rain > 0 else ("강풍" if wind >= 8 else "맑음/흐림")
            env["주로"] = "불량/습" if rain > 1 else ("건조" if temp >= 27 and rain == 0 else "표준")
    except Exception:
        pass
    return env


def score_and_recommend(horses: pd.DataFrame, env: Dict[str, Any], sim_count: int, risk_mode: str) -> Tuple[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]:
    df = horses.copy()
    # Normalize and score; this is decision-support only, not guaranteed prediction.
    for c in ["레이팅", "최근순위", "승률", "복승률", "예상배당", "체중변화", "기수점수", "인기"]:
        df[c] = pd.to_numeric(df.get(c, 0), errors="coerce").fillna(0)
    rating_score = df["레이팅"].clip(0, 120) / 120 * 25
    recent_score = (10 - df["최근순위"].clip(1, 10)) / 9 * 20
    win_score = df["승률"].clip(0, 50) / 50 * 15
    place_score = df["복승률"].clip(0, 80) / 80 * 15
    jockey_score = df["기수점수"].clip(0, 100) / 100 * 12
    body_penalty = df["체중변화"].abs().clip(0, 10) * 0.8
    popularity_bonus = (12 - df["인기"].clip(1, 12)) / 11 * 5
    odds = df["예상배당"].replace(0, 12).clip(1, 80)
    value_bonus = odds.apply(lambda x: 8 if 6 <= x <= 25 else (3 if 25 < x <= 50 else 0))
    env_adj = 0
    if env.get("주로") in ["불량/습", "건조"]:
        env_adj = random.uniform(-1.5, 1.5)
    df["점수"] = (rating_score + recent_score + win_score + place_score + jockey_score + popularity_bonus + value_bonus - body_penalty + env_adj).round(2)
    df["위험"] = (df["체중변화"].abs() * 2 + df["최근순위"].clip(1, 10) + df["인기"].clip(1, 12) / 2).round(1)
    df["근거"] = df.apply(lambda r: f"레이팅 {int(r['레이팅'])} · 최근 {int(r['최근순위'])}위권 · 체중 {int(r['체중변화']):+d}kg · 인기 {int(r['인기'])}", axis=1)
    df = df.sort_values(["점수", "예상배당"], ascending=[False, False]).reset_index(drop=True)

    nums = df["마번"].astype(int).tolist()
    if len(nums) < 3:
        nums = nums + [n for n in range(1, 13) if n not in nums][:3-len(nums)]
    axis = nums[0]
    mate = nums[1]
    sub = nums[2]
    hole = nums[3] if len(nums) > 3 else sub

    # Monte Carlo-ish combo list based on score weights.
    weights = df["점수"].clip(lower=1).tolist()
    combos: List[Dict[str, Any]] = []
    rng_count = max(200, int(sim_count))
    for _ in range(rng_count):
        picked = random.choices(nums, weights=weights, k=min(3, len(nums)))
        # enforce unique top3
        uniq = []
        for p in picked:
            if p not in uniq:
                uniq.append(p)
        for p in nums:
            if len(uniq) >= 3:
                break
            if p not in uniq:
                uniq.append(p)
        c = uniq[:3]
        combos.append({"삼쌍승": f"{c[0]}→{c[1]}→{c[2]}", "삼복승": "-".join(map(str, sorted(c))), "축": c[0]})
    combo_df = pd.DataFrame(combos)
    top_exact = combo_df["삼쌍승"].value_counts().head(1)
    top_trio = combo_df["삼복승"].value_counts().head(1)
    exact = str(top_exact.index[0]) if not top_exact.empty else f"{axis}→{mate}→{sub}"
    trio = str(top_trio.index[0]) if not top_trio.empty else "-".join(map(str, sorted([axis, mate, sub])))

    avg_score = float(df["점수"].head(3).mean()) if not df.empty else 0
    confidence = min(97, max(45, int(avg_score)))
    est_odds = max(2.0, round(float(df["예상배당"].head(3).mean()), 1))
    if risk_mode == "안전형":
        reco_amount = 10000
        title = "안전 방어 중심"
    elif risk_mode == "공격형":
        reco_amount = 30000
        title = "고배당 소액도전 포함"
    else:
        reco_amount = 20000
        title = "균형형"
    result = {
        "축마": int(axis), "상대마": int(mate), "보조마": int(sub), "구멍마": int(hole),
        "공격삼쌍승": exact, "방어삼복승": trio, "추천금액": reco_amount,
        "판정": title, "예상배당": est_odds, "신뢰도": confidence,
        "근거": f"상위 점수 {axis}-{mate}-{sub}, 주로 {env.get('주로')}, 날씨 {env.get('날씨')} 반영",
    }
    return df, result, combos

# -----------------------------------------------------------------------------
# Hub / local save
# -----------------------------------------------------------------------------
def load_csv_safe(path: Path) -> pd.DataFrame:
    try:
        if path.exists():
            return pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        try:
            return pd.read_csv(path)
        except Exception:
            pass
    return pd.DataFrame()


def append_csv(path: Path, row: Dict[str, Any]) -> bool:
    try:
        df = pd.DataFrame([row])
        old = load_csv_safe(path)
        out = pd.concat([old, df], ignore_index=True) if not old.empty else df
        out.to_csv(path, index=False, encoding="utf-8-sig")
        return True
    except Exception:
        return False


def load_local_hub() -> pd.DataFrame:
    return load_csv_safe(LOCAL_HUB_FILE)


def load_bigdata() -> pd.DataFrame:
    return load_csv_safe(BIGDATA_FILE)


def save_hub_row(row: Dict[str, Any]) -> bool:
    ok1 = append_csv(LOCAL_HUB_FILE, row)
    ok2 = append_csv(BIGDATA_FILE, {**row, "결과상태": "대기", "성공실패": "미확인"})
    return ok1 and ok2

# -----------------------------------------------------------------------------
# Stable betting module
# -----------------------------------------------------------------------------
BET_TYPE_INFO = pd.DataFrame([
    ["단승", "1등 할 말 1마리", "필요", "이 말이 우승한다"],
    ["연승", "1~3등 안에 들 말 1마리", "상관없음", "우승까지는 몰라도 3착 안에는 온다"],
    ["복승", "1등·2등 말 2마리", "상관없음", "두 마리가 1·2등 안에 들어온다"],
    ["쌍승", "1등·2등 말 2마리", "필요", "1착과 2착 순서까지 맞힌다"],
    ["복연승", "1~3등 안에 들 말 2마리", "상관없음", "두 마리가 둘 다 3착 안에 들어온다"],
    ["삼복승", "1·2·3등 말 3마리", "상관없음", "세 마리가 모두 3착 안에 들어온다"],
    ["삼쌍승", "1·2·3등 말 3마리", "필요", "1착·2착·3착 순서까지 정확히 맞힌다"],
], columns=["승식", "맞히는 방식", "순서", "해석"])


def parse_exact_combo(exact: str, fallback: List[int]) -> List[int]:
    nums = [safe_int(x) for x in re.findall(r"\d+", str(exact or ""))]
    nums = [n for n in nums if n > 0]
    for n in fallback:
        if n not in nums:
            nums.append(n)
    return nums[:4]


def stable_plan_from_result(result: Dict[str, Any], budget: int = 30000, preset: str = "안정형") -> pd.DataFrame:
    axis = safe_int(result.get("축마", 7), 7)
    mate = safe_int(result.get("상대마", 3), 3)
    sub = safe_int(result.get("보조마", 10), 10)
    hole = safe_int(result.get("구멍마", 5), 5)
    if preset == "보수형":
        rows = [
            ["연승", f"{axis}", 15000, 1.5, "축마가 3착 안에 들어오면 방어"],
            ["복연승", f"{axis}-{mate}", 10000, 2.0, "축마+상대마가 둘 다 3착 안"],
            ["복승", f"{axis}-{mate}", 3000, 5.0, "두 마리가 1·2착이면 수익"],
            ["삼복승", f"{axis}-{mate}-{sub}", 2000, 12.0, "세 마리가 모두 3착 안"],
        ]
    elif preset == "수익형":
        rows = [
            ["연승", f"{axis}", 7000, 1.5, "기본 방어"],
            ["복연승", f"{axis}-{mate}", 6000, 2.0, "본전 방어"],
            ["복승", f"{axis}-{mate}", 7000, 5.0, "본 수익"],
            ["삼복승", f"{axis}-{mate}-{sub}", 6000, 12.0, "중배당"],
            ["쌍승", f"{axis}→{mate}", 2000, 9.0, "순서 도전"],
            ["삼쌍승", f"{axis}→{mate}→{sub}", 2000, 45.0, "고배당 도전"],
        ]
    else:
        rows = [
            ["연승", f"{axis}", 10000, 1.5, "축마가 3착 안에 들어오면 방어"],
            ["복연승", f"{axis}-{mate}", 8000, 2.0, "축마+상대마가 둘 다 3착 안"],
            ["복연승", f"{axis}-{sub}", 5000, 2.8, "상대마가 바뀌어도 방어"],
            ["복승", f"{axis}-{mate}", 4000, 5.0, "두 마리가 1·2착이면 수익"],
            ["삼복승", f"{axis}-{mate}-{sub}", 2000, 12.0, "세 마리가 모두 3착 안"],
            ["삼쌍승", f"{axis}→{mate}→{sub}", 1000, 45.0, "순서까지 맞으면 고배당"],
        ]
    df = pd.DataFrame(rows, columns=["승식", "조합", "구매금액", "예상배당", "목적"])
    base_sum = int(df["구매금액"].sum())
    if base_sum > 0 and budget != base_sum:
        ratio = budget / base_sum
        df["구매금액"] = (df["구매금액"] * ratio / 1000).round().astype(int) * 1000
        # adjust rounding drift
        diff = int(budget - df["구매금액"].sum())
        if len(df) and diff != 0:
            df.loc[0, "구매금액"] = max(1000, int(df.loc[0, "구매금액"] + diff))
    df["예상환급"] = (df["구매금액"] * df["예상배당"]).round().astype(int)
    return df


def calc_case_rows(plan: pd.DataFrame) -> pd.DataFrame:
    def total_for(types: List[str], combo_contains: Optional[str] = None) -> int:
        d = plan[plan["승식"].isin(types)].copy()
        if combo_contains:
            d = d[d["조합"].astype(str).str.contains(combo_contains, regex=False)]
        return int(d["예상환급"].sum()) if not d.empty else 0

    total_bet = int(plan["구매금액"].sum()) if not plan.empty else 0
    cases = []
    # generic cases matching default logic
    t1 = total_for(["연승"])
    cases.append(["축마만 3착 안", "연승", t1, t1 - total_bet])
    t2 = total_for(["연승", "복연승"])
    cases.append(["축마+상대/보조마 3착 안", "연승 + 복연승", t2, t2 - total_bet])
    t3 = total_for(["연승", "복연승", "복승"])
    cases.append(["축마+상대마 1·2착", "연승 + 복연승 + 복승", t3, t3 - total_bet])
    t4 = total_for(["연승", "복연승", "복승", "삼복승"])
    cases.append(["세 마리 1~3착 안", "연승 + 복연승 + 복승 + 삼복승", t4, t4 - total_bet])
    t5 = int(plan["예상환급"].sum()) if not plan.empty else 0
    cases.append(["순서까지 삼쌍 적중", "전체 대부분 적중", t5, t5 - total_bet])
    return pd.DataFrame(cases, columns=["결과 상황", "적중 승식", "환급금", "순손익"])


def render_stable_bet_module(result: Dict[str, Any], meet: str) -> None:
    st.markdown("### 💰 3만원 안정 분할 & 예상 환급 계산")
    st.markdown(
        '<div class="betting-card"><div class="betting-title">핵심 원칙</div>'
        '한 방 몰빵보다 <b>연승·복연승으로 방어</b>하고, <b>복승·삼복승으로 수익</b>, '
        '<b>삼쌍승은 소액 도전</b>으로만 사용합니다. 수익 보장이 아니라 손실을 줄이고 오래 버티는 구조입니다.</div>',
        unsafe_allow_html=True,
    )
    with st.expander("📘 마권 승식 해석", expanded=False):
        st.dataframe(BET_TYPE_INFO, use_container_width=True, hide_index=True)
        st.caption("복=조합, 쌍=순서, 삼=3마리/3착까지 보는 방식으로 기억하면 쉽습니다.")

    c1, c2, c3, c4 = st.columns(4)
    default_axis = safe_int(result.get("축마", 7), 7)
    default_mate = safe_int(result.get("상대마", 3), 3)
    default_sub = safe_int(result.get("보조마", 10), 10)
    default_hole = safe_int(result.get("구멍마", 5), 5)
    with c1:
        axis = st.number_input("축마", min_value=1, max_value=20, value=default_axis, step=1)
    with c2:
        mate = st.number_input("상대마", min_value=1, max_value=20, value=default_mate, step=1)
    with c3:
        sub = st.number_input("보조마", min_value=1, max_value=20, value=default_sub, step=1)
    with c4:
        hole = st.number_input("구멍마", min_value=1, max_value=20, value=default_hole, step=1)

    tmp_result = {**result, "축마": axis, "상대마": mate, "보조마": sub, "구멍마": hole}
    b1, b2 = st.columns([1, 1])
    with b1:
        budget = st.number_input("총 구매 한도", min_value=1000, max_value=100000, value=30000, step=1000)
    with b2:
        preset = st.selectbox("분할 방식", ["안정형", "보수형", "수익형"], index=0)

    plan = stable_plan_from_result(tmp_result, int(budget), preset)
    st.markdown("#### ✅ 기본 추천 조합")
    edited = st.data_editor(
        plan,
        use_container_width=True,
        hide_index=True,
        column_config={
            "구매금액": st.column_config.NumberColumn("구매금액", min_value=0, step=1000, format="%d원"),
            "예상배당": st.column_config.NumberColumn("예상배당", min_value=1.0, step=0.1, format="%.1f배"),
            "예상환급": st.column_config.NumberColumn("예상환급", format="%d원", disabled=True),
        },
        disabled=["승식", "조합", "목적", "예상환급"],
        key="stable_bet_editor",
    )
    edited["구매금액"] = pd.to_numeric(edited["구매금액"], errors="coerce").fillna(0).astype(int)
    edited["예상배당"] = pd.to_numeric(edited["예상배당"], errors="coerce").fillna(1.0)
    edited["예상환급"] = (edited["구매금액"] * edited["예상배당"]).round().astype(int)

    total_bet = int(edited["구매금액"].sum())
    max_return = int(edited["예상환급"].sum())
    max_profit = max_return - total_bet
    m1, m2, m3 = st.columns(3)
    m1.metric("총 구매금액", f"{total_bet:,}원")
    m2.metric("최대 예상환급", f"{max_return:,}원")
    m3.metric("최대 예상손익", f"{max_profit:,}원")

    st.markdown("#### 📊 결과별 예상")
    case_df = calc_case_rows(edited)
    st.dataframe(case_df, use_container_width=True, hide_index=True)

    st.markdown("#### 한눈에 보기")
    if not case_df.empty:
        p = {r["결과 상황"]: r for _, r in case_df.iterrows()}
        st.markdown(
            f"""
<div class="manual-box">
<div class="manual-title">3만원 안정 분할 예상</div>
<div class="manual-note">최소 방어: <b>{safe_int(p.get('축마만 3착 안', {}).get('환급금', 0)):,}원</b></div>
<div class="manual-note">본전권: <b>{safe_int(p.get('축마+상대/보조마 3착 안', {}).get('환급금', 0)):,}원</b></div>
<div class="manual-note">수익권: <b>{safe_int(p.get('축마+상대마 1·2착', {}).get('환급금', 0)):,}원</b></div>
<div class="manual-note">중배당권: <b>{safe_int(p.get('세 마리 1~3착 안', {}).get('환급금', 0)):,}원</b></div>
<div class="manual-note">고배당권: <b>{safe_int(p.get('순서까지 삼쌍 적중', {}).get('환급금', 0)):,}원</b></div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.info("배당 계산 공식: 환급금 = 구매금액 × 배당률. 환급금은 원금 포함 금액으로 보고, 순손익은 환급금 - 총 구매금액입니다.")
    st.warning("실제 배당은 경주 직전까지 변동됩니다. 이 계산은 현재 배당 기준 예상치이며, 수익을 보장하지 않습니다.")
    st.link_button("↗ KRA 공식 마권구매 홈페이지 바로가기", kra_buy_url(meet), use_container_width=True)
    st.caption("※ 자동구매/자동결제 아님 · 공식 페이지 이동만 제공 · 사용자가 직접 입력/확정")

# -----------------------------------------------------------------------------
# UI render
# -----------------------------------------------------------------------------
def render_live_panel(rc_date: str, meet: str, race_no: int, selected: List[str], sim_count: int, risk_mode: str) -> Tuple[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]], Dict[str, pd.DataFrame], pd.DataFrame, Dict[str, Any]]:
    st.markdown("### 실시간 KRA 분석")
    if "live_data" not in st.session_state:
        st.session_state["live_data"] = {}
        st.session_state["api_status"] = pd.DataFrame()

    col_a, col_b = st.columns([1, 1])
    with col_a:
        run = st.button("실시간 데이터 새로고침", type="primary")
    with col_b:
        run_sim = st.button("불러오기 + 시뮬레이션")

    if run or run_sim or not st.session_state["live_data"]:
        data, status = fetch_all_live(rc_date, meet, int(race_no), selected)
        st.session_state["live_data"] = data
        st.session_state["api_status"] = status

    data = st.session_state.get("live_data", {})
    status = st.session_state.get("api_status", pd.DataFrame())
    env = fetch_weather(meet)
    base = build_base_horses(data, rc_date, meet, int(race_no))
    horses = merge_score_features(base, data, rc_date, meet, int(race_no))
    score_df, result, combos = score_and_recommend(horses, env, sim_count, risk_mode)

    live_rows = sum(len(v) for v in data.values()) if data else 0
    if live_rows == 0:
        st.markdown('<div class="info-box-warn">⚠ 실시간 API 데이터 0건입니다. 현재 화면은 샘플/최근 캐시 보정 분석입니다. API Key/승인/상세 URL을 확인하세요.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="info-box-ok">✅ 실시간 API 데이터 {live_rows:,}행 반영</div>', unsafe_allow_html=True)

    left, right = st.columns([1.1, 1])
    with left:
        st.markdown(f"""
<div class="focus-card">
<div class="focus-badge">놓치면 아까운 조합</div>
<div class="focus-combo">{result.get('공격삼쌍승','-')}</div>
<div class="reco-meta">{meet} {int(race_no)}R · {rc_date} · {env.get('날씨')}/{env.get('주로')}</div>
<div class="metric-wrap">
<div class="metric-box"><div class="m-title">신뢰도</div><div class="m-value-green">{int(result.get('신뢰도',0))}</div></div>
<div class="metric-box"><div class="m-title">예상배당</div><div class="m-value-orange">{result.get('예상배당',0)}배</div></div>
<div class="metric-box"><div class="m-title">추천금액</div><div class="m-value-blue">{int(result.get('추천금액',0)):,}원</div></div>
</div>
<hr>
<b>방어 삼복승:</b> {result.get('방어삼복승','-')}<br>
<b>축/상대/보조/구멍:</b> {result.get('축마')}-{result.get('상대마')}-{result.get('보조마')}-{result.get('구멍마')}<br>
<b>근거:</b> {result.get('근거','')}
</div>
""", unsafe_allow_html=True)
        st.caption("경마 결과는 보장되지 않습니다. 실구매는 본인 판단과 책임, 소액 원칙으로만 진행하세요.")
        st.link_button("↗ KRA 공식 마권구매 홈페이지 바로가기", kra_buy_url(meet), use_container_width=True)
        st.caption("※ 자동구매 아님 · KRA 공식 화면으로 이동 · 로그인/구매는 본인 직접 진행")
    with right:
        st.markdown("#### 🧾 10초 수동구매 체크")
        st.markdown(f'<div class="bigline">축 {result.get("축마")} / 상대 {result.get("상대마")} / 보조 {result.get("보조마")}</div>', unsafe_allow_html=True)
        st.markdown("- 자동구매/자동결제는 하지 않습니다.\n- 공식 화면으로 이동 후 직접 입력/확정합니다.\n- 배당은 경주 직전까지 변동됩니다.")
        if st.button("현재 분석 허브 저장", type="primary"):
            row = {
                "저장시각": now_str(), "날짜": rc_date, "경마장": meet, "경주번호": int(race_no),
                "축마": result.get("축마"), "상대마": result.get("상대마"), "보조마": result.get("보조마"), "구멍마": result.get("구멍마"),
                "공격삼쌍승": result.get("공격삼쌍승"), "방어삼복승": result.get("방어삼복승"),
                "예상배당": result.get("예상배당"), "신뢰도": result.get("신뢰도"),
                "추천금액": result.get("추천금액"), "근거": result.get("근거"), "실시간행수": live_rows,
            }
            ok = save_hub_row(row)
            if ok:
                st.success("로컬 허브/빅데이터 로그 저장 완료")
            else:
                st.error("저장 실패: 폴더 권한 또는 파일 열림 상태를 확인하세요.")

    with st.expander("상세 데이터", expanded=False):
        st.markdown("#### TOP 말 점수")
        show_cols = [c for c in ["마번", "마명", "점수", "최근순위", "레이팅", "체중변화", "기수점수", "인기", "예상배당", "위험", "근거"] if c in score_df.columns]
        st.dataframe(score_df[show_cols].head(12) if show_cols else score_df.head(12), use_container_width=True, height=330)
        st.markdown("#### 최근 시뮬레이션 조합")
        st.dataframe(pd.DataFrame(combos).head(30), use_container_width=True, height=260)
    return score_df, result, combos, data, status, env


def render_api_hub_panel(status: pd.DataFrame, data: Dict[str, pd.DataFrame]) -> None:
    st.markdown("### API 상태 / 허브 저장")
    with st.expander("API 상태 요약", expanded=True):
        if isinstance(status, pd.DataFrame) and not status.empty:
            keep_cols = [c for c in ["API", "행수", "상태", "URL"] if c in status.columns]
            st.dataframe(status[keep_cols] if keep_cols else status, use_container_width=True, height=360)
        else:
            st.info("아직 API 호출 전입니다.")
    with st.expander("허브 저장 현황", expanded=True):
        local_hub_df = load_local_hub()
        big_df = load_bigdata()
        h1, h2, h3 = st.columns(3)
        h1.metric("허브 저장", f"{len(local_hub_df):,}건")
        h2.metric("빅데이터 로그", f"{len(big_df):,}건")
        h3.metric("현재 데이터", f"{sum(len(v) for v in data.values()) if data else 0:,}행")
        if not local_hub_df.empty:
            show_cols = [c for c in ["저장시각", "경마장", "경주번호", "공격삼쌍승", "방어삼복승", "예상배당", "신뢰도", "추천금액"] if c in local_hub_df.columns]
            st.dataframe(local_hub_df[show_cols].tail(30) if show_cols else local_hub_df.tail(30), use_container_width=True, height=330)
        else:
            st.info("허브 저장 데이터가 아직 없습니다.")
    with st.expander("API URL 확인/복사용", expanded=False):
        for k, label in API_LABELS:
            st.caption(f"{label}: {get_url(k)}")


def render_help_panel() -> None:
    st.markdown("### 사용법 / 안전 안내")
    st.markdown(
        """
1. 사이드바에서 **공공데이터 API Key**를 저장합니다.  
2. 경마장, 날짜, 경주번호를 선택합니다.  
3. 현장에서 HTTP 500이 나는 API는 **API ON/OFF**에서 꺼도 앱은 계속 작동합니다.  
4. 추천 결과는 참고용입니다. 실제 구매는 공식 KRA 화면에서 직접 입력·확정합니다.  
5. **3만원 안정 분할**은 손실을 줄이는 구조일 뿐 수익 보장이 아닙니다.

**자동구매/자동결제 기능은 없습니다.** 이 앱은 분석, 기록, 공식 페이지 이동만 제공합니다.
"""
    )


def render() -> None:
    css()
    st.markdown(
        """
<div class="hero">
<h2>MARU KRA 실전 대시보드</h2>
<div class="muted">실시간 19API · API ON/OFF · 실패방어 · 허브저장 · 10초 수동구매 · 3만원 안정분할/배당계산 통합</div>
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

        rc_date = st.text_input("분석 날짜", value=today_kst())
        meet = st.selectbox("경마장", ["서울", "부산경남", "제주"], index=0)
        race_no = st.number_input("경주번호", min_value=1, max_value=20, value=1, step=1)
        sim_count = st.slider("시뮬레이션", 300, 5000, 1200, step=100)
        risk_mode = st.selectbox("전략", ["균형형", "안전형", "공격형"], index=0)
        auto_refresh = st.selectbox("자동 새로고침", [0, 30, 60, 120, 300], index=1)
        render_api_onoff_panel()
        switches = get_api_switches()
        selected = [k for k, _ in API_LABELS if switches.get(k, False)]
        st.caption(f"실시간 호출 대상: {len(selected)}/19개")

    tab1, tab2, tab3, tab4 = st.tabs(["🏇 실시간 분석", "💰 3만원 분할/배당", "🔌 API/허브", "📘 도움말"])
    with tab1:
        score_df, result, combos, data, status, env = render_live_panel(rc_date, meet, int(race_no), selected, int(sim_count), risk_mode)
    with tab2:
        # Use last/live result if available; otherwise calculate sample instantly.
        if "live_data" in st.session_state:
            data2 = st.session_state.get("live_data", {})
        else:
            data2 = {}
        env2 = fetch_weather(meet)
        base2 = build_base_horses(data2, rc_date, meet, int(race_no))
        horses2 = merge_score_features(base2, data2, rc_date, meet, int(race_no))
        _, result2, _ = score_and_recommend(horses2, env2, int(sim_count), risk_mode)
        render_stable_bet_module(result2, meet)
    with tab3:
        status2 = st.session_state.get("api_status", pd.DataFrame())
        data3 = st.session_state.get("live_data", {})
        render_api_hub_panel(status2, data3)
    with tab4:
        render_help_panel()

    if int(auto_refresh or 0) > 0:
        st.caption(f"자동 새로고침 설정: {int(auto_refresh)}초")
        try:
            time.sleep(0.1)
            st.autorefresh(interval=int(auto_refresh) * 1000, key="maru_auto_refresh")  # available in some Streamlit builds
        except Exception:
            pass


if __name__ == "__main__":
    render()
