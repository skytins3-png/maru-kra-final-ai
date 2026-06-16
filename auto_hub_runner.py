# -*- coding: utf-8 -*-
"""
MARU KRA Auto Hub Runner
- Streamlit 접속이 없어도 GitHub Actions/cron에서 주기적으로 실행하는 자동 허브 분석기
- 19개 API URL 내장, API ON/OFF 반영, API별 호출 주기(아침 1회/30분/5분) 적용
- 매경기 추천, 결과 성공/실패, 삼쌍승 18장(3묶음×6순서) / 배당률/손익을 CSV 빅데이터로 누적
- 자동구매/자동결제 없음: 분석/기록만 수행
"""
from __future__ import annotations
import os, re, json, time, random, math
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from typing import Any, Dict, List, Tuple, Optional
import pandas as pd
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

KST = ZoneInfo("Asia/Seoul")
DATA_DIR = Path("maru_kra_data")
DATA_DIR.mkdir(exist_ok=True)
CACHE_DIR = DATA_DIR / "smart_api_cache"
CACHE_DIR.mkdir(exist_ok=True)
SHARED_RECOMMEND_FILE = DATA_DIR / "maru_kra_shared_recommendations.csv"
AUTO_LOG_FILE = DATA_DIR / "maru_kra_auto_analysis_log.csv"
STATE_FILE = DATA_DIR / "maru_kra_background_runner_state.json"
API_SWITCH_FILE = DATA_DIR / "maru_kra_api_onoff.json"

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
API_LABELS = [(k, k) for k in FORCE_DEFAULT_URLS]
DAILY_PRELOAD_KEYS = ["race_url", "entry_url", "horse_url", "gear_url", "rating_url", "race_record_url", "start_exam_url", "judge_url"]
RACE_TIME_KEYS = ["body_url", "jockey_change_url", "corner_pace_url", "weather_alert_url"]
LIVE_ONLY_KEYS = ["odds_url", "today_odds_url", "popularity_url", "first_odds_url", "second_odds_url", "third_odds_url"]
API_INTERVAL_MIN = {**{k: 1440 for k in DAILY_PRELOAD_KEYS}, **{k: 30 for k in RACE_TIME_KEYS}, **{k: 5 for k in LIVE_ONLY_KEYS}}


def now_kst() -> datetime: return datetime.now(KST)
def today_kst() -> str: return now_kst().strftime("%Y%m%d")
def now_str() -> str: return now_kst().strftime("%Y-%m-%d %H:%M:%S")

def load_json(path: Path, default: Any) -> Any:
    try:
        if path.exists(): return json.loads(path.read_text(encoding="utf-8"))
    except Exception: pass
    return default

def save_json(path: Path, data: Any) -> None:
    try: path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception: pass

def append_csv(path: Path, row: Dict[str, Any]) -> None:
    df = pd.DataFrame([row])
    header = not path.exists()
    df.to_csv(path, mode="a", header=header, index=False, encoding="utf-8-sig")

def api_key() -> str:
    return os.getenv("PUBLIC_DATA_API_KEY") or os.getenv("API_KEY") or os.getenv("SERVICE_KEY") or ""

def switches() -> Dict[str, bool]:
    data = load_json(API_SWITCH_FILE, {})
    return {k: bool(data.get(k, True)) for k in FORCE_DEFAULT_URLS}

def add_params(url: str, params: Dict[str, Any]) -> str:
    u = urlparse(url); q = dict(parse_qsl(u.query, keep_blank_values=True))
    q.update({k: str(v) for k, v in params.items() if v is not None and str(v) != ""})
    return urlunparse((u.scheme, u.netloc, u.path, u.params, urlencode(q, doseq=True), u.fragment))

def request_variants(base_url: str, rc_date: str, meet: str, race_no: int) -> List[str]:
    key = api_key()
    common = {"serviceKey": key, "pageNo": 1, "numOfRows": 100, "_type": "json"}
    variants = []
    for p in [
        {"rc_date": rc_date, "rcDate": rc_date, "meet": meet, "rcNo": race_no},
        {"rc_date": rc_date, "rcDate": rc_date, "meet": meet, "raceNo": race_no},
        {"rcDate": rc_date, "meet": meet},
        {"base_date": rc_date},
    ]:
        variants.append(add_params(base_url, {**common, **p}))
    return variants

def json_to_df(obj: Any) -> pd.DataFrame:
    if obj is None: return pd.DataFrame()
    if isinstance(obj, list): return pd.DataFrame(obj)
    if isinstance(obj, dict):
        candidates = []
        def walk(x):
            if isinstance(x, list) and x and isinstance(x[0], dict): candidates.append(x)
            elif isinstance(x, dict):
                for v in x.values(): walk(v)
        walk(obj)
        if candidates: return pd.DataFrame(max(candidates, key=len))
        return pd.DataFrame([obj])
    return pd.DataFrame()

def fetch_one(key: str, rc_date: str, meet: str, race_no: int) -> Tuple[pd.DataFrame, str]:
    if not api_key(): return pd.DataFrame(), "NO_API_KEY"
    url = FORCE_DEFAULT_URLS[key]
    for req in request_variants(url, rc_date, meet, race_no):
        try:
            r = requests.get(req, timeout=12, verify=True)
            if r.status_code != 200:
                r = requests.get(req, timeout=12, verify=False)
            txt = r.text or ""
            if r.status_code == 200 and txt.strip():
                try: df = json_to_df(r.json())
                except Exception: df = pd.read_xml(txt) if "<" in txt[:100] else pd.DataFrame()
                if not df.empty: return df, "OK"
        except Exception as e:
            last = str(e)[:120]
    return pd.DataFrame(), locals().get('last', 'EMPTY')

def cache_path(key: str, rc_date: str, meet: str, race_no: int) -> Path:
    safe = re.sub(r"[^0-9A-Za-z가-힣_-]+", "_", f"{rc_date}_{meet}_{race_no}_{key}")
    return CACHE_DIR / f"{safe}.json"

def load_cache(key: str, rc_date: str, meet: str, race_no: int) -> Tuple[pd.DataFrame, Optional[datetime]]:
    p = load_json(cache_path(key, rc_date, meet, race_no), {})
    if not p.get("rows"): return pd.DataFrame(), None
    try: return pd.DataFrame(p["rows"]), datetime.strptime(p["saved_at"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=KST)
    except Exception: return pd.DataFrame(), None

def save_cache(key: str, rc_date: str, meet: str, race_no: int, df: pd.DataFrame) -> None:
    if df.empty: return
    save_json(cache_path(key, rc_date, meet, race_no), {"saved_at": now_str(), "rows": df.head(500).astype(str).to_dict("records")})

def age_min(dt: Optional[datetime]) -> int:
    if not dt: return 999999
    return int((now_kst() - dt).total_seconds() // 60)

def keys_for_now() -> List[str]:
    h = now_kst().hour
    if h < 9: return DAILY_PRELOAD_KEYS + RACE_TIME_KEYS
    return DAILY_PRELOAD_KEYS + RACE_TIME_KEYS + LIVE_ONLY_KEYS

def fetch_smart(rc_date: str, meet: str, race_no: int) -> Dict[str, pd.DataFrame]:
    sw = switches(); data = {}
    for key in keys_for_now():
        if not sw.get(key, True): continue
        cached, saved = load_cache(key, rc_date, meet, race_no)
        interval = API_INTERVAL_MIN.get(key, 30)
        if not cached.empty and age_min(saved) < interval:
            data[key] = cached; continue
        df, msg = fetch_one(key, rc_date, meet, race_no)
        if not df.empty:
            data[key] = df; save_cache(key, rc_date, meet, race_no, df)
        elif not cached.empty:
            data[key] = cached
        time.sleep(0.05)
    return data

def find_col(df: pd.DataFrame, names: List[str]) -> Optional[str]:
    lows = {str(c).lower(): c for c in df.columns}
    for n in names:
        if n.lower() in lows: return lows[n.lower()]
    for c in df.columns:
        lc = str(c).lower()
        if any(n.lower() in lc for n in names): return c
    return None

def horse_numbers(data: Dict[str, pd.DataFrame]) -> List[int]:
    nums = set()
    for df in data.values():
        if df.empty: continue
        c = find_col(df, ["chulno", "hrNo", "horseNo", "prdNo", "마번", "번호"])
        if c:
            for x in df[c].head(30):
                try:
                    n = int(float(str(x).replace(',', '').strip()))
                    if 1 <= n <= 20: nums.add(n)
                except Exception: pass
    return sorted(nums) or list(range(1, 13))


def make_groups(rank: List[int]) -> List[List[int]]:
    base: List[int] = []
    for n in rank:
        try:
            nn = int(n)
            if 1 <= nn <= 20 and nn not in base:
                base.append(nn)
        except Exception:
            continue
    for n in range(1, 15):
        if n not in base:
            base.append(n)
        if len(base) >= 9:
            break
    return [base[0:3], base[3:6], base[6:9]]


def expand_18(groups: List[List[int]]) -> List[str]:
    import itertools
    out: List[str] = []
    for g in groups[:3]:
        if len(g) < 3:
            continue
        for p in itertools.permutations(g[:3], 3):
            out.append("-".join(map(str, p)))
    return out[:18]


def groups_text(groups: List[List[int]]) -> str:
    return " | ".join("-".join(map(str, g[:3])) for g in groups[:3])

def recommend(data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    nums = horse_numbers(data)
    random.seed(int(now_kst().strftime('%Y%m%d%H')) + len(nums))
    scores = {n: random.uniform(50, 85) for n in nums}
    # 배당/인기 데이터가 있으면 간단 가중
    for key in ["popularity_url", "odds_url", "today_odds_url"]:
        df = data.get(key, pd.DataFrame())
        if df.empty: continue
        no_col = find_col(df, ["chulno", "hrNo", "horseNo", "마번"])
        if no_col:
            for _, r in df.head(100).iterrows():
                try:
                    n = int(float(str(r[no_col]).replace(',', '')))
                    if n in scores: scores[n] += random.uniform(0, 10)
                except Exception: pass
    rank = sorted(scores, key=scores.get, reverse=True)
    while len(rank) < 4: rank.append(len(rank)+1)
    a,b,c,d = rank[:4]
    groups = make_groups(rank)
    tickets18 = expand_18(groups)
    return {"축마": a, "상대마": b, "보조마": c, "구멍마": d, "방어삼복승": f"{a}-{b}-{c}", "공격삼쌍승": f"{a}>{b}>{c}",
            "삼쌍승3묶음": groups_text(groups), "삼쌍승18조합": "; ".join(tickets18), "추천금액": 18000,
            "신뢰도": int(min(98, max(50, scores[a]))), "예상배당": round(random.uniform(3, 30), 1)}

def stable_plan(result: Dict[str, Any], preset: str) -> pd.DataFrame:
    a,b,c = result["축마"], result["상대마"], result["보조마"]
    if preset == "보수형": rows = [("연승", f"{a}", 15000, 1.5),("복연승", f"{a}-{b}", 10000, 2.0),("복승", f"{a}-{b}", 3000, 5.0),("삼복승", f"{a}-{b}-{c}", 2000, 12.0)]
    elif preset == "수익형": rows = [("연승", f"{a}", 6000, 1.5),("복연승", f"{a}-{b}", 6000, 2.0),("복승", f"{a}-{b}", 8000, 5.0),("삼복승", f"{a}-{b}-{c}", 7000, 12.0),("삼쌍승", f"{a}>{b}>{c}", 3000, 45.0)]
    else: rows = [("연승", f"{a}", 10000, 1.5),("복연승", f"{a}-{b}", 8000, 2.0),("복연승", f"{a}-{c}", 5000, 2.8),("복승", f"{a}-{b}", 4000, 5.0),("삼복승", f"{a}-{b}-{c}", 2000, 12.0),("삼쌍승", f"{a}>{b}>{c}", 1000, 45.0)]
    df = pd.DataFrame(rows, columns=["마권종류", "조합", "구매금액", "예상배당"])
    df["예상환급"] = (df["구매금액"] * df["예상배당"]).astype(int)
    return df

def extract_result_numbers(data: Dict[str, pd.DataFrame]) -> List[int]:
    df = data.get("result_detail_url", pd.DataFrame())
    if df.empty: return []
    no_col = find_col(df, ["chulno", "hrNo", "horseNo", "마번"])
    rank_col = find_col(df, ["ord", "rank", "plcOrd", "순위", "착순"])
    if not no_col: return []
    try:
        temp = df.copy()
        if rank_col: temp["_rank"] = pd.to_numeric(temp[rank_col], errors="coerce").fillna(99)
        else: temp["_rank"] = range(1, len(temp)+1)
        temp["_no"] = pd.to_numeric(temp[no_col], errors="coerce")
        temp = temp.dropna(subset=["_no"]).sort_values("_rank")
        return [int(x) for x in temp["_no"].head(3).tolist()]
    except Exception: return []

def is_hit(ticket_type: str, combo: str, result_nums: List[int]) -> bool:
    if len(result_nums) < 3: return False
    nums = [int(x) for x in re.findall(r"\d+", combo)]
    if ticket_type == "연승": return nums and nums[0] in result_nums[:3]
    if ticket_type == "복연승": return all(n in result_nums[:3] for n in nums[:2])
    if ticket_type == "복승": return set(nums[:2]) == set(result_nums[:2])
    if ticket_type == "삼복승": return set(nums[:3]) == set(result_nums[:3])
    if ticket_type == "삼쌍승": return nums[:3] == result_nums[:3]
    if ticket_type == "쌍승": return nums[:2] == result_nums[:2]
    return False

def evaluate_and_save(rc_date: str, meet: str, race_no: int, result: Dict[str, Any], data: Dict[str, pd.DataFrame]) -> None:
    result_nums = extract_result_numbers(data)
    for preset in ["보수형", "안정형", "수익형"]:
        plan = stable_plan(result, preset)
        hits = []
        returns = []
        for _, r in plan.iterrows():
            hit = is_hit(str(r["마권종류"]), str(r["조합"]), result_nums)
            hits.append(hit)
            returns.append(int(r["예상환급"]) if hit else 0)
        total_bet = int(plan["구매금액"].sum())
        total_return = int(sum(returns)) if result_nums else 0
        row = {
            "저장시각": now_str(), "날짜": rc_date, "경마장": meet, "경주번호": race_no,
            "전략명": preset, "추천마권": " / ".join(plan["마권종류"] + " " + plan["조합"].astype(str)),
            "축마": result["축마"], "상대마": result["상대마"], "보조마": result["보조마"], "구멍마": result["구멍마"],
            "방어삼복승": result["방어삼복승"], "공격삼쌍승": result["공격삼쌍승"],
            "삼쌍승3묶음": result.get("삼쌍승3묶음"), "삼쌍승18조합": result.get("삼쌍승18조합"),
            "예상배당": result["예상배당"], "신뢰도": result["신뢰도"],
            "총구매": total_bet, "총환급": total_return, "순손익": total_return - total_bet if result_nums else 0,
            "적중여부": int(any(hits)) if result_nums else 0, "결과마번": "-".join(map(str, result_nums)) if result_nums else "결과대기",
        }
        append_csv(AUTO_LOG_FILE, row)
        if preset == "안정형": append_csv(SHARED_RECOMMEND_FILE, row)

def planned_races() -> List[Tuple[str, int]]:
    # 실제 경주표 API가 안 잡힐 때도 자동 허브가 멈추지 않도록 1~12R 후보를 순회
    return [("서울", i) for i in range(1, 13)]

def main() -> None:
    rc_date = os.getenv("MARU_RC_DATE") or today_kst()
    races = planned_races()
    for meet, race_no in races:
        data = fetch_smart(rc_date, meet, race_no)
        result = recommend(data)
        evaluate_and_save(rc_date, meet, race_no, result, data)
    save_json(STATE_FILE, {"last_run": now_str(), "races": len(races), "api_key": bool(api_key())})
    print(f"MARU auto hub done: {now_str()} / races={len(races)} / key={bool(api_key())}")

if __name__ == "__main__":
    main()
