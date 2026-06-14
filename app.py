
import json
import re
import time
import random
import hashlib
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components



def safe_autorefresh(interval_ms=60000, key="maru_realtime_refresh"):
    try:
        from streamlit_autorefresh import st_autorefresh
        return st_autorefresh(interval=interval_ms, key=key)
    except Exception:
        return 0

# =========================
# 기본 설정
# =========================
st.set_page_config(
    page_title="MARU KRA AI FINAL",
    page_icon="🐎",
    layout="wide",
    initial_sidebar_state="expanded",
)

KST = ZoneInfo("Asia/Seoul")
BASE_DIR = Path(".")
SETTINGS_FILE = BASE_DIR / "maru_kra_settings.json"
RECO_FILE = BASE_DIR / "maru_recommendations.csv"
COMPARE_FILE = BASE_DIR / "maru_compare.csv"

API_LIST = [
    ("race", "1. 경주정보 API URL"),
    ("entry", "2. 출전등록말 API URL"),
    ("horse", "3. 경주마정보 API URL"),
    ("body", "4. 출전마 체중 API URL"),
    ("gear", "5. 장구/폐출혈 API URL"),
    ("rating", "6. 레이팅 API URL"),
    ("odds", "7. 배당/매출 API URL"),
    ("today_odds", "8. 시행당일 배당 API URL"),
    ("result_detail", "9. AI 경주결과상세 API URL"),
    ("race_record", "10. 경주기록 API URL"),
    ("start_exam", "11. 출발심사 API URL"),
    ("judge", "12. 경주심판 API URL"),
    ("jockey_change", "13. 기수변경 API URL"),
    ("weather_alert", "14. 기상특보 API URL"),
    ("corner_pace", "15. 코너/주로빠르기 API URL"),
    ("popularity", "16. 인기투표 API URL"),
    ("first_odds", "17. 1착마 적중승식 API URL"),
    ("second_odds", "18. 2착마 적중승식 API URL"),
    ("third_odds", "19. 3착마 적중승식 API URL"),
]

CORE_APIS = ["race", "entry", "horse", "body", "gear", "rating", "odds", "today_odds"]
TRUSTED_CHULNO_APIS = ["body", "gear", "today_odds", "first_odds", "third_odds"]



# =========================
# 허브 / 알림 기능
# =========================
def get_secret_value(*keys, default=""):
    try:
        if "maru" in st.secrets:
            for k in keys:
                if k in st.secrets["maru"]:
                    return st.secrets["maru"][k]
                if k.upper() in st.secrets["maru"]:
                    return st.secrets["maru"][k.upper()]
    except Exception:
        pass
    try:
        if "google_sheets" in st.secrets:
            for k in keys:
                if k in st.secrets["google_sheets"]:
                    return st.secrets["google_sheets"][k]
                if k.upper() in st.secrets["google_sheets"]:
                    return st.secrets["google_sheets"][k.upper()]
    except Exception:
        pass
    try:
        if "alerts" in st.secrets:
            for k in keys:
                if k in st.secrets["alerts"]:
                    return st.secrets["alerts"][k]
                if k.upper() in st.secrets["alerts"]:
                    return st.secrets["alerts"][k.upper()]
    except Exception:
        pass
    try:
        for k in keys:
            if k in st.secrets:
                return st.secrets[k]
            if k.upper() in st.secrets:
                return st.secrets[k.upper()]
    except Exception:
        pass
    return default


def sheets_enabled():
    return bool(get_secret_value("SHEET_ID", "sheet_id", default=""))


def get_gsheet_client():
    if not sheets_enabled():
        return None, "Google Sheets 미설정"
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        raw = get_secret_value("SERVICE_ACCOUNT_JSON", "service_account_json", default="")
        info = None
        if raw:
            info = json.loads(raw) if isinstance(raw, str) else dict(raw)
        else:
            try:
                if "google_sheets" in st.secrets and "service_account" in st.secrets["google_sheets"]:
                    info = dict(st.secrets["google_sheets"]["service_account"])
            except Exception:
                info = None

        if not info:
            return None, "서비스계정 정보 없음"

        creds = Credentials.from_service_account_info(info, scopes=scopes)
        return gspread.authorize(creds), ""
    except Exception as e:
        return None, "Google Sheets 연결 실패: " + str(e)


def get_sheet_workbook():
    client, err = get_gsheet_client()
    if client is None:
        return None, err
    try:
        sheet_id = str(get_secret_value("SHEET_ID", "sheet_id", default="")).strip()
        return client.open_by_key(sheet_id), ""
    except Exception as e:
        return None, "시트 열기 실패: " + str(e)


def hub_headers(title):
    if title == "realtime_status":
        return ["저장시각","날짜","경마장","경주번호","출발시간","연결API","총행수","판정","추천","신뢰도","추천금액","상태"]
    if title == "recommendations":
        return ["저장시각","날짜","경마장","경주번호","출발시간","판정","공격삼쌍승","방어삼복승","보조삼쌍승","예상배당","신뢰도","추천금액","자금상태"]
    if title == "alerts":
        return ["저장시각","날짜","경마장","경주번호","출발시간","알림종류","추천","신뢰도","추천금액","전송상태","메시지"]
    if title == "api_status":
        return ["저장시각","날짜","경마장","경주번호","API","상태","행수","마번후보"]
    if title == "score_snapshots":
        return ["저장시각","날짜","경마장","경주번호","마번","마명","종합점수","기대지수","근거"]
    return ["저장시각","내용"]


def get_or_create_ws(wb, title, headers):
    try:
        ws = wb.worksheet(title)
    except Exception:
        ws = wb.add_worksheet(title=title, rows=3000, cols=max(30, len(headers)+5))
        ws.append_row(headers)
        return ws

    try:
        first = ws.row_values(1)
        if not first:
            ws.append_row(headers)
    except Exception:
        pass
    return ws


def hub_append(title, row):
    if not sheets_enabled():
        return False, "Google Sheets 미설정"
    wb, err = get_sheet_workbook()
    if wb is None:
        return False, err
    try:
        headers = hub_headers(title)
        ws = get_or_create_ws(wb, title, headers)
        current_headers = ws.row_values(1) or headers

        changed = False
        for k in row.keys():
            if k not in current_headers:
                current_headers.append(k)
                changed = True
        if changed:
            ws.update("1:1", [current_headers])

        ws.append_row([row.get(h, "") for h in current_headers], value_input_option="USER_ENTERED")
        return True, ""
    except Exception as e:
        return False, "허브 저장 실패: " + str(e)


def hub_read(title, limit=100):
    if not sheets_enabled():
        return pd.DataFrame()
    wb, err = get_sheet_workbook()
    if wb is None:
        return pd.DataFrame()
    try:
        ws = get_or_create_ws(wb, title, hub_headers(title))
        df = pd.DataFrame(ws.get_all_records())
        return df.tail(limit) if not df.empty else df
    except Exception:
        return pd.DataFrame()


def strong_recommendation(result, min_conf=72, min_amount=1000):
    if not result:
        return False
    try:
        return (
            str(result.get("판정", "")) in ["소액 공격", "강력추천", "소액 가능"]
            and int(result.get("신뢰도", 0)) >= int(min_conf)
            and int(result.get("추천금액", 0)) >= int(min_amount)
            and str(result.get("공격삼쌍승", "-")) != "-"
        )
    except Exception:
        return False


def alert_message(track_place, rc_no, start_time, result):
    return (
        f"🐎 MARU KRA 강력추천\\n"
        f"{track_place} {rc_no}R 출발 {start_time}\\n"
        f"추천: {result.get('공격삼쌍승','-')}\\n"
        f"방어: {result.get('방어삼복승','-')}\\n"
        f"신뢰도: {result.get('신뢰도',0)}%\\n"
        f"추천금액: {result.get('추천금액',0):,}원\\n"
        f"자동구매 아님 · 수동 확인"
    )


def trigger_screen_alarm(message, enabled=True):
    if not enabled:
        return
    safe_msg = str(message).replace("`", "").replace("\\", "\\\\").replace("\n", "\\n")
    components.html(
        f"""
<script>
try {{
  if (navigator.vibrate) {{
    navigator.vibrate([700, 250, 700, 250, 1000]);
  }}
  const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  function beep(freq, duration, delay) {{
    setTimeout(() => {{
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.frequency.value = freq;
      gain.gain.value = 0.12;
      osc.start();
      setTimeout(() => {{
        osc.stop();
      }}, duration);
    }}, delay);
  }}
  beep(880, 350, 0);
  beep(1100, 350, 450);
  beep(1320, 500, 900);
}} catch(e) {{}}
</script>
<div style="padding:18px;border-radius:14px;background:#fff3bf;border:2px solid #f08c00;color:#5f3b00;font-size:20px;font-weight:800;">
🚨 강력추천 알림 발생<br/>
{safe_msg}
</div>
""",
        height=170,
    )


def send_webhook_alert(message):
    webhook = str(get_secret_value("ALERT_WEBHOOK_URL", "alert_webhook_url", default="")).strip()
    if not webhook:
        return False, "ALERT_WEBHOOK_URL 미설정"
    try:
        r = requests.post(webhook, json={"text": message, "message": message}, timeout=8)
        if 200 <= r.status_code < 300:
            return True, f"Webhook 전송 완료 {r.status_code}"
        return False, f"Webhook HTTP {r.status_code}"
    except Exception as e:
        return False, "Webhook 전송 실패: " + str(e)


def send_telegram_alert(message):
    token = str(get_secret_value("TELEGRAM_BOT_TOKEN", "telegram_bot_token", default="")).strip()
    chat_id = str(get_secret_value("TELEGRAM_CHAT_ID", "telegram_chat_id", default="")).strip()
    if not token or not chat_id:
        return False, "Telegram 미설정"
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        r = requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=8)
        if 200 <= r.status_code < 300:
            return True, "Telegram 전송 완료"
        return False, f"Telegram HTTP {r.status_code}"
    except Exception as e:
        return False, "Telegram 전송 실패: " + str(e)


def maybe_send_strong_alert(track_place, rc_no, start_time, result, alert_enabled, screen_alarm=True, min_conf=72):
    if not strong_recommendation(result, min_conf=min_conf):
        return "조건 미달"

    msg = alert_message(track_place, rc_no, start_time, result)
    alert_key = hashlib.md5(f"{track_place}-{rc_no}-{start_time}-{result.get('공격삼쌍승')}-{result.get('신뢰도')}".encode("utf-8")).hexdigest()

    if st.session_state.get("last_alert_key") == alert_key:
        trigger_screen_alarm(msg, enabled=screen_alarm)
        return "이미 전송한 알림"

    trigger_screen_alarm(msg, enabled=screen_alarm)

    sent_status = []
    if alert_enabled:
        ok1, s1 = send_webhook_alert(msg)
        ok2, s2 = send_telegram_alert(msg)
        sent_status.extend([s1, s2])
    else:
        sent_status.append("문자/Webhook OFF")

    send_result = " / ".join(sent_status)
    try:
        hub_append("alerts", {
            "저장시각": now_kst_str(),
            "날짜": today_kst(),
            "경마장": track_place,
            "경주번호": rc_no,
            "출발시간": start_time,
            "알림종류": "강력추천",
            "추천": result.get("공격삼쌍승",""),
            "신뢰도": result.get("신뢰도",0),
            "추천금액": result.get("추천금액",0),
            "전송상태": send_result,
            "메시지": msg,
        })
    except Exception:
        pass
    st.session_state["last_alert_key"] = alert_key
    return send_result


def hub_sync_realtime(track_place, rc_no, start_time, data, score_df, result, connected_count, rows_total):
    now = now_kst_str()
    date = today_kst()

    hub_append("realtime_status", {
        "저장시각": now,
        "날짜": date,
        "경마장": track_place,
        "경주번호": rc_no,
        "출발시간": start_time,
        "연결API": connected_count,
        "총행수": rows_total,
        "판정": result.get("판정",""),
        "추천": result.get("공격삼쌍승",""),
        "신뢰도": result.get("신뢰도",0),
        "추천금액": result.get("추천금액",0),
        "상태": "SYNCED",
    })

    if result.get("추천금액", 0) > 0 and result.get("공격삼쌍승", "-") != "-":
        hub_append("recommendations", {
            "저장시각": now,
            "날짜": date,
            "경마장": track_place,
            "경주번호": rc_no,
            "출발시간": start_time,
            "판정": result.get("판정",""),
            "공격삼쌍승": result.get("공격삼쌍승",""),
            "방어삼복승": result.get("방어삼복승",""),
            "보조삼쌍승": result.get("보조삼쌍승",""),
            "예상배당": result.get("예상배당",0),
            "신뢰도": result.get("신뢰도",0),
            "추천금액": result.get("추천금액",0),
            "자금상태": result.get("자금상태",""),
        })

    try:
        if score_df is not None and not score_df.empty:
            for _, r in score_df.head(20).iterrows():
                hub_append("score_snapshots", {
                    "저장시각": now,
                    "날짜": date,
                    "경마장": track_place,
                    "경주번호": rc_no,
                    "마번": r.get("마번",""),
                    "마명": r.get("마명",""),
                    "종합점수": r.get("종합점수",""),
                    "기대지수": r.get("기대지수",""),
                    "근거": r.get("근거",""),
                })
    except Exception:
        pass

    try:
        for key, df in data.items():
            hub_append("api_status", {
                "저장시각": now,
                "날짜": date,
                "경마장": track_place,
                "경주번호": rc_no,
                "API": key,
                "상태": "연결됨" if df is not None and not df.empty else "없음",
                "행수": len(df) if df is not None else 0,
                "마번후보": chulno_col(df) if df is not None and not df.empty else "",
            })
    except Exception:
        pass

# =========================
# CSS
# =========================
st.markdown(
    """
<style>
.block-container {
    max-width: 1500px;
    padding-top: 1.0rem;
    padding-bottom: 2rem;
}
[data-testid="stSidebar"] {
    min-width: 330px;
}
.big-card {
    background: linear-gradient(135deg, #003f27 0%, #006b3d 55%, #00331f 100%);
    color: white;
    padding: 28px;
    border-radius: 18px;
    box-shadow: 0 8px 26px rgba(0,0,0,.16);
    min-height: 330px;
}
.big-card .small {
    font-size: 24px;
    font-weight: 700;
}
.big-card .combo {
    font-size: 86px;
    font-weight: 900;
    letter-spacing: 8px;
    margin-top: 20px;
}
.big-card .odds {
    font-size: 64px;
    font-weight: 900;
    color: #ffd43b;
    margin-top: 18px;
}
.metric-card {
    background: white;
    border: 1px solid #e7ece8;
    border-radius: 16px;
    padding: 22px;
    box-shadow: 0 4px 16px rgba(0,0,0,.06);
    min-height: 130px;
}
.metric-title {
    color: #1f6d49;
    font-weight: 800;
    font-size: 19px;
}
.metric-value {
    color: #006b3d;
    font-weight: 900;
    font-size: 44px;
    margin-top: 6px;
}
.section-card {
    background: white;
    border: 1px solid #e7ece8;
    border-radius: 16px;
    padding: 18px;
    box-shadow: 0 4px 16px rgba(0,0,0,.05);
}
.status-ok { color: #087f5b; font-weight: 800; }
.status-warn { color: #e67700; font-weight: 800; }
.status-bad { color: #c92a2a; font-weight: 800; }
</style>
""",
    unsafe_allow_html=True,
)


# =========================
# 유틸
# =========================
def now_kst():
    return datetime.now(KST)


def today_kst():
    return now_kst().strftime("%Y%m%d")


def now_kst_str():
    return now_kst().strftime("%Y-%m-%d %H:%M:%S")


def parse_start_time_value(x, base_date=None):
    """
    API 출발시간 값을 한국시간 datetime으로 변환.
    지원 예:
    - 1035
    - 10:35
    - 10시35분
    - 202606141035
    - 2026-06-14 10:35
    """
    base_date = str(base_date or today_kst()).replace("-", "")
    s = str(x or "").strip()
    if not s:
        return None

    digits = re.sub(r"[^0-9]", "", s)

    try:
        if len(digits) >= 12:
            # YYYYMMDDHHMM
            return datetime(
                int(digits[0:4]),
                int(digits[4:6]),
                int(digits[6:8]),
                int(digits[8:10]),
                int(digits[10:12]),
                tzinfo=KST,
            )
        if len(digits) == 8:
            # YYYYMMDD only: unusable for start time
            return None
        if len(digits) in [3, 4]:
            hh = int(digits[:-2])
            mm = int(digits[-2:])
            return datetime(
                int(base_date[0:4]),
                int(base_date[4:6]),
                int(base_date[6:8]),
                hh,
                mm,
                tzinfo=KST,
            )
    except Exception:
        return None

    return None


def find_race_time_columns(df):
    if df is None or df.empty:
        return None, None, None

    rc_candidates = ["rcNo", "raceNo", "경주번호"]
    time_candidates = ["rcTime", "raceTime", "chulTime", "startTime", "출발시간", "발주시각", "출주시각"]
    date_candidates = ["rcDate", "raceDate", "meetDate", "date", "ymd"]

    rc_col = find_col(df, rc_candidates)
    time_col = find_col(df, time_candidates)
    date_col = find_col(df, date_candidates)
    return rc_col, time_col, date_col


def build_race_schedule(race_df, target_date, track_place):
    """
    race API에서 경주번호/출발시간 표를 만듭니다.
    """
    if race_df is None or race_df.empty:
        return pd.DataFrame()

    df = race_df.copy()

    # 날짜/경마장 필터
    date_col = find_col(df, ["rcDate", "raceDate", "meetDate", "date", "ymd"])
    meet_col = find_col(df, ["meet", "meetCd", "rcourse", "경마장"])
    rc_col, time_col, _ = find_race_time_columns(df)

    try:
        if date_col:
            ds = df[date_col].astype(str).str.replace("-", "", regex=False).str.strip()
            df = df[ds == str(target_date).replace("-", "").strip()]
    except Exception:
        pass

    try:
        if meet_col:
            ms = df[meet_col].apply(normalize_meet_value)
            df = df[ms == normalize_meet_value(track_place)]
    except Exception:
        pass

    if not rc_col:
        return pd.DataFrame()

    # 시간 컬럼이 없으면 빈 시간표
    rows = []
    for _, r in df.iterrows():
        try:
            rc_no = int(pd.to_numeric(r.get(rc_col), errors="coerce"))
        except Exception:
            continue

        start_dt = None
        if time_col:
            start_dt = parse_start_time_value(r.get(time_col), target_date)

        rows.append({
            "경주번호": rc_no,
            "출발시각": start_dt.strftime("%H:%M") if start_dt else "-",
            "출발datetime": start_dt,
            "상태": "",
        })

    out = pd.DataFrame(rows).drop_duplicates(subset=["경주번호"]).sort_values("경주번호")
    return out


def choose_race_30min(schedule_df, manual_rc_no, minutes_before=30):
    """
    현재 한국시간 기준 출발 30분 전부터 출발 직전까지의 경주를 자동 선택.
    없으면 다음 경주를 대기 경주로 선택.
    """
    if schedule_df is None or schedule_df.empty:
        return int(manual_rc_no), "-", "시간표 없음: 수동 경주번호 사용", False, pd.DataFrame()

    now = now_kst()
    sched = schedule_df.copy()
    sched["분석시작"] = sched["출발datetime"].apply(lambda x: x.replace(tzinfo=KST) if x and getattr(x, "tzinfo", None) is None else x)
    sched["분석시작"] = sched["분석시작"].apply(lambda x: x - pd.Timedelta(minutes=int(minutes_before)) if pd.notna(x) and x is not None else None)

    active_rows = []
    next_rows = []

    for _, r in sched.iterrows():
        start_dt = r.get("출발datetime")
        analyze_from = r.get("분석시작")
        if start_dt is None or pd.isna(start_dt):
            continue

        if analyze_from <= now <= start_dt:
            active_rows.append(r)
        elif now < analyze_from:
            next_rows.append(r)

    if active_rows:
        chosen = sorted(active_rows, key=lambda x: x.get("출발datetime"))[0]
        rc = int(chosen["경주번호"])
        return rc, chosen["출발시각"], f"{rc}R 출발 {minutes_before}분 전 실시간 분석 중", True, sched

    if next_rows:
        chosen = sorted(next_rows, key=lambda x: x.get("출발datetime"))[0]
        rc = int(chosen["경주번호"])
        return rc, chosen["출발시각"], f"{rc}R 분석 대기: 출발 {minutes_before}분 전부터 자동 시작", False, sched

    return int(manual_rc_no), "-", "오늘 남은 자동 분석 대상 없음: 수동 경주번호 사용", False, sched


def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default


def save_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def secret_get(*keys, default=""):
    # 1) [maru] 안에서 찾기
    try:
        if "maru" in st.secrets:
            for k in keys:
                if k in st.secrets["maru"]:
                    return st.secrets["maru"][k]
                if k.upper() in st.secrets["maru"]:
                    return st.secrets["maru"][k.upper()]
    except Exception:
        pass

    # 2) 루트에서 찾기
    try:
        for k in keys:
            if k in st.secrets:
                return st.secrets[k]
            if k.upper() in st.secrets:
                return st.secrets[k.upper()]
    except Exception:
        pass

    return default


def mask_secret_url(url):
    s = str(url or "")
    s = re.sub(r"(serviceKey=)[^&]+", r"\1***", s, flags=re.I)
    return s


def append_query_param(url, key, value):
    if not url or not value:
        return url
    if re.search(rf"([?&]){re.escape(key)}=", url, flags=re.I):
        return url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}{key}={value}"


def build_api_url(raw_url, api_key):
    url = str(raw_url or "").strip()
    if not url:
        return ""

    # 사용자가 {serviceKey}를 넣은 경우 치환
    if "{serviceKey}" in url:
        url = url.replace("{serviceKey}", api_key)

    # serviceKey가 없으면 자동 추가
    if api_key and "serviceKey=" not in url and "servicekey=" not in url.lower():
        url = append_query_param(url, "serviceKey", api_key)

    # 공통 파라미터는 없을 때만 붙임
    url = append_query_param(url, "pageNo", "1")
    url = append_query_param(url, "numOfRows", "100")
    if "dataType=" not in url and "resultType=" not in url:
        url = append_query_param(url, "resultType", "json")
    return url


def normalize_json_to_df(obj):
    if obj is None:
        return pd.DataFrame()

    # 공공데이터포털 일반 구조: response > body > items > item
    candidates = []
    try:
        candidates.append(obj["response"]["body"]["items"]["item"])
    except Exception:
        pass
    try:
        candidates.append(obj["body"]["items"]["item"])
    except Exception:
        pass
    try:
        candidates.append(obj["items"]["item"])
    except Exception:
        pass
    try:
        candidates.append(obj["response"]["body"]["item"])
    except Exception:
        pass

    for item in candidates:
        if isinstance(item, list):
            return pd.DataFrame(item)
        if isinstance(item, dict):
            return pd.DataFrame([item])

    if isinstance(obj, list):
        return pd.DataFrame(obj)
    if isinstance(obj, dict):
        # dict 안에 list가 있으면 가장 큰 list 선택
        lists = []
        for v in obj.values():
            if isinstance(v, list):
                lists.append(v)
        if lists:
            lists.sort(key=len, reverse=True)
            return pd.DataFrame(lists[0])
        return pd.DataFrame([obj])

    return pd.DataFrame()


def fetch_api(name, raw_url, api_key, timeout=12):
    url = build_api_url(raw_url, api_key)
    if not url:
        return pd.DataFrame(), "URL 없음"

    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code != 200:
            return pd.DataFrame(), f"HTTP {r.status_code}"

        text = r.text.strip()
        if not text:
            return pd.DataFrame(), "빈 응답"

        # json 우선
        try:
            obj = r.json()
            return normalize_json_to_df(obj), ""
        except Exception:
            # XML/텍스트는 원문 일부를 행으로 표시
            return pd.DataFrame([{"raw": text[:500]}]), ""
    except Exception as e:
        return pd.DataFrame(), str(e)


def normalize_meet_value(x):
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


def current_filter(df, target_date, track_place, rc_no):
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
            dd = str(target_date).replace("-", "").strip()
            d = d[ds == dd]
    except Exception:
        pass

    try:
        if meet_col:
            ms = d[meet_col].apply(normalize_meet_value)
            d = d[ms == normalize_meet_value(track_place)]
    except Exception:
        pass

    try:
        if rc_col:
            rs = pd.to_numeric(d[rc_col], errors="coerce")
            d = d[rs == int(rc_no)]
    except Exception:
        pass

    # 필터 후 완전 비면 원본 유지. 단 추천 단계에서는 chulNo 기준으로 다시 방어.
    return d if not d.empty else original


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


def extract_chulno_base(data, target_date, track_place, rc_no):
    rows = {}
    evidence = {}

    for api_name in TRUSTED_CHULNO_APIS:
        df = data.get(api_name, pd.DataFrame())
        if df is None or df.empty:
            continue

        f = current_filter(df, target_date, track_place, rc_no)
        c = chulno_col(f)
        if not c:
            continue

        f = f.copy()
        f["_chulno"] = pd.to_numeric(f[c], errors="coerce")
        f = f[f["_chulno"].between(1, 14, inclusive="both")]

        for _, r in f.iterrows():
            n = int(r["_chulno"])
            name = f"{n}번"
            for nc in ["hrName", "마명", "horseName", "rcName"]:
                if nc in f.columns and pd.notna(r.get(nc, None)) and str(r.get(nc)).strip():
                    name = str(r.get(nc)).strip()
                    break
            rows[n] = name
            evidence.setdefault(n, set()).add(api_name)

    out = []
    for n in sorted(rows.keys()):
        ev = ",".join(sorted(evidence.get(n, [])))
        base = 50 + len(evidence.get(n, [])) * 7
        out.append({"마번": n, "마명": rows[n], "종합점수": base, "기대지수": round(base / 50, 2), "근거": ev})

    return pd.DataFrame(out)


def make_recommendation(score_df, env, sim_count):
    if score_df is None or score_df.empty or len(score_df) < 3:
        return {
            "판정": "관망",
            "경주번호": "-",
            "출발시간": "-",
            "공격삼쌍승": "-",
            "방어삼복승": "-",
            "보조삼쌍승": "-",
            "예상배당": 0,
            "신뢰도": 49,
            "추천금액": 0,
            "수익기대": "낮음",
            "적중기대": "보통-",
            "자금상태": "현재 경주 chulNo 부족 / 관망",
        }, pd.DataFrame()

    df = score_df.copy().sort_values("종합점수", ascending=False).reset_index(drop=True)

    # 환경 보정
    env_bonus = 0
    if env.get("weather") in ["맑음", "흐림"]:
        env_bonus += 2
    if env.get("track") == "양호":
        env_bonus += 3
    if env.get("sand") == "보통":
        env_bonus += 1
    if env.get("wind") == "없음":
        env_bonus += 1

    df["종합점수"] = df["종합점수"] + env_bonus
    df = df.sort_values("종합점수", ascending=False).reset_index(drop=True)

    top = df["마번"].astype(int).tolist()
    a, b, c = top[:3]

    # 시뮬레이션은 top 6 안에서만
    candidates = top[: min(6, len(top))]
    combo_count = {}
    weights = []
    for n in candidates:
        score = float(df.loc[df["마번"] == n, "종합점수"].iloc[0])
        weights.append(max(score, 1))

    for _ in range(int(sim_count)):
        # 중복 없이 3개 선택
        picked = random.choices(candidates, weights=weights, k=6)
        uniq = []
        for x in picked:
            if x not in uniq:
                uniq.append(x)
            if len(uniq) == 3:
                break
        if len(uniq) == 3:
            key = f"{uniq[0]} - {uniq[1]} - {uniq[2]}"
            combo_count[key] = combo_count.get(key, 0) + 1

    sim_rows = []
    for combo, cnt in sorted(combo_count.items(), key=lambda x: x[1], reverse=True)[:10]:
        sim_rows.append({
            "조합": combo,
            "반복횟수": cnt,
            "비율": round(cnt / max(int(sim_count), 1), 3),
            "예상배당": round(random.uniform(8, 55), 1),
        })

    sim_df = pd.DataFrame(sim_rows)
    attack = sim_df.iloc[0]["조합"] if not sim_df.empty else f"{a} - {b} - {c}"
    defense = f"{a} / {b} / {c}"
    sub = sim_df.iloc[1]["조합"] if len(sim_df) > 1 else "-"

    confidence = min(92, max(52, int(df["종합점수"].head(3).mean())))
    expected_odds = float(sim_df.iloc[0]["예상배당"]) if not sim_df.empty else round(random.uniform(10, 40), 1)

    # 자금 방어
    if confidence < 60:
        judge = "관망"
        amount = 0
    elif confidence < 72:
        judge = "소액 관찰"
        amount = 1000
    elif expected_odds >= 20:
        judge = "소액 공격"
        amount = 2000
    else:
        judge = "소액 가능"
        amount = 1000

    return {
        "판정": judge,
        "경주번호": int(st.session_state.get("target_rc_no", 1)),
        "출발시간": st.session_state.get("start_time", "-"),
        "공격삼쌍승": attack if amount > 0 else "-",
        "방어삼복승": defense if amount > 0 else "-",
        "보조삼쌍승": sub if amount > 0 else "-",
        "예상배당": expected_odds if amount > 0 else 0,
        "신뢰도": confidence,
        "추천금액": amount,
        "수익기대": "높음" if expected_odds >= 20 and amount > 0 else "보통",
        "적중기대": "보통+" if confidence >= 65 else "보통-",
        "자금상태": "손실방어 우선 / 자동구매 아님",
    }, sim_df


def safe_read_csv(path):
    if path.exists():
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def append_csv(path, row):
    old = safe_read_csv(path)
    new = pd.concat([old, pd.DataFrame([row])], ignore_index=True)
    new.to_csv(path, index=False, encoding="utf-8-sig")
    return new


# =========================
# 설정 로드
# =========================
settings = load_json(SETTINGS_FILE, {})

# =========================
# 사이드바
# =========================
st.sidebar.title("🐎 MARU KRA 메뉴")
st.sidebar.caption("최종 19 API 대시보드")

st.sidebar.subheader("기본 설정")
api_key = st.sidebar.text_input(
    "공공데이터 API Key",
    value=str(settings.get("api_key") or secret_get("api_key", "API_KEY", default="")),
    type="password",
)
target_date = st.sidebar.text_input("분석 날짜", value=str(settings.get("target_date") or today_kst()))
track_place = st.sidebar.selectbox(
    "경마장",
    ["서울", "부산경남", "제주"],
    index=["서울", "부산경남", "제주"].index(settings.get("track_place", "서울")) if settings.get("track_place", "서울") in ["서울", "부산경남", "제주"] else 0,
)
target_rc_no = st.sidebar.number_input("경주번호", min_value=1, max_value=20, value=int(settings.get("target_rc_no", 1) or 1), step=1)
start_time = st.sidebar.text_input("출발시간", value=str(settings.get("start_time", "-")))

st.session_state["target_rc_no"] = int(target_rc_no)
st.session_state["start_time"] = start_time

st.sidebar.divider()
st.sidebar.subheader("핵심 API 1~8")
api_urls = {}
for key, label in API_LIST[:8]:
    default_val = settings.get(f"{key}_url") or secret_get(f"{key}_url", f"{key.upper()}_URL", default="")
    api_urls[key] = st.sidebar.text_input(label, value=str(default_val), key=f"input_{key}")

with st.sidebar.expander("보조 API 9~19 숨김/펼침", expanded=False):
    for key, label in API_LIST[8:]:
        default_val = settings.get(f"{key}_url") or secret_get(f"{key}_url", f"{key.upper()}_URL", default="")
        api_urls[key] = st.text_input(label, value=str(default_val), key=f"input_{key}")

st.sidebar.divider()
st.sidebar.subheader("환경 요소")
weather = st.sidebar.selectbox("날씨", ["맑음", "흐림", "비", "눈", "안개"], index=0)
track = st.sidebar.selectbox("주로상태", ["양호", "보통", "불량"], index=0)
sand = st.sidebar.selectbox("모래 상태", ["보통", "건조", "젖음", "무거움"], index=0)
wind = st.sidebar.selectbox("바람", ["없음", "약함", "강함"], index=0)
distance_pref = st.sidebar.selectbox("거리 성향", ["단거리", "중거리", "장거리"], index=1)
sim_count = st.sidebar.number_input("시뮬레이션 횟수", min_value=20, max_value=1000, value=int(settings.get("sim_count", 100) or 100), step=20)

st.sidebar.divider()
use_sample = st.sidebar.checkbox("샘플 데이터 사용", value=False, help="실전에서는 OFF 권장")
auto_save = st.sidebar.checkbox("추천 자동 저장", value=True)

st.sidebar.divider()
st.sidebar.subheader("실시간 자동수집")
realtime_on = st.sidebar.checkbox("실시간 자동수집 ON", value=True)
refresh_sec = st.sidebar.selectbox("새로고침 간격", [15, 30, 60, 120, 300], index=1)
auto_fetch_on_load = st.sidebar.checkbox("앱 열면 바로 수집", value=True)

if realtime_on:
    safe_autorefresh(interval_ms=int(refresh_sec) * 1000, key="maru_realtime_auto_refresh")

st.sidebar.divider()
st.sidebar.subheader("경주시간표 자동분석")
schedule_auto_on = st.sidebar.checkbox("출발 30분 전 자동분석", value=True)
analysis_before_min = st.sidebar.selectbox("분석 시작 시점", [10, 20, 30, 40, 60], index=2)

st.sidebar.divider()
st.sidebar.subheader("허브 저장 / 강력알림")
hub_auto_save = st.sidebar.checkbox("허브 실시간 저장", value=True)
strong_alert_on = st.sidebar.checkbox("강력추천 문자/Webhook", value=True)
screen_alarm_on = st.sidebar.checkbox("화면 경고음/진동", value=True)
alert_min_conf = st.sidebar.slider("강력추천 신뢰도 기준", 60, 90, 72, 1)
st.sidebar.caption("문자 전송은 Secrets의 ALERT_WEBHOOK_URL 또는 Telegram 설정 필요")


save_payload = {
    "api_key": api_key,
    "target_date": target_date,
    "track_place": track_place,
    "target_rc_no": int(target_rc_no),
    "start_time": start_time,
    "sim_count": int(sim_count),
}
for key, _ in API_LIST:
    save_payload[f"{key}_url"] = api_urls.get(key, "")

if st.sidebar.button("💾 설정 저장", use_container_width=True):
    save_json(SETTINGS_FILE, save_payload)
    st.sidebar.success("저장 완료")

if st.sidebar.button("🧹 추천/비교 로그 초기화", use_container_width=True):
    for p in [RECO_FILE, COMPARE_FILE]:
        try:
            if p.exists():
                p.unlink()
        except Exception:
            pass
    st.sidebar.warning("로그 초기화 완료")


# =========================
# 헤더
# =========================
h1, h2, h3 = st.columns([1.4, 1, 1])
with h1:
    st.markdown("## 🐎 MARU KRA AI")
    st.caption("FINAL CLEAN 19 API DASHBOARD · API Key 숨김 · chulNo 전용 분석")
with h2:
    st.success(f"한국시간 {now_kst_str()}")
    st.caption(f"마지막 수집: {st.session_state.get('last_fetch_time', '아직 없음')} / 실시간: {'ON' if realtime_on else 'OFF'}")
with h3:
    if st.button("🔄 즉시 데이터 불러오기", use_container_width=True):
        st.session_state["run_fetch"] = True

if "run_fetch" not in st.session_state:
    st.session_state["run_fetch"] = bool(auto_fetch_on_load)

# 실시간 ON이면 매 새로고침마다 자동 수집
if realtime_on:
    st.session_state["run_fetch"] = True



# =========================
# 데이터 수집
# =========================
data = {}
errors = []
if not any(str(v).strip() for v in api_urls.values()):
    st.warning("입력된 API URL이 없습니다. 왼쪽 사이드바에 API 19개 주소를 입력하고 저장하세요.")

selected_rc_no = int(target_rc_no)
selected_start_time = start_time
schedule_message = "수동 경주번호 사용"
schedule_active = False
schedule_df = pd.DataFrame()

if st.session_state["run_fetch"]:
    with st.spinner("경주시간표 확인 및 API 19개 실시간 수집 중..."):
        # 1) race API는 원본으로 먼저 불러와 시간표 확인
        raw_race_df, race_err = fetch_api("race", api_urls.get("race", ""), api_key)
        if race_err:
            errors.append(f"race: {race_err}")

        if schedule_auto_on and not raw_race_df.empty:
            schedule_df = build_race_schedule(raw_race_df, target_date, track_place)
            selected_rc_no, selected_start_time, schedule_message, schedule_active, schedule_df = choose_race_30min(
                schedule_df, int(target_rc_no), int(analysis_before_min)
            )

        st.session_state["target_rc_no"] = int(selected_rc_no)
        st.session_state["start_time"] = selected_start_time

        # 2) 전체 API 수집 후 선택 경주번호 기준 필터
        for key, label in API_LIST:
            if key == "race" and not raw_race_df.empty:
                df, err = raw_race_df.copy(), ""
            else:
                df, err = fetch_api(key, api_urls.get(key, ""), api_key)

            if not df.empty:
                df = current_filter(df, target_date, track_place, int(selected_rc_no))
            data[key] = df
            if err:
                errors.append(f"{key}: {err}")

    st.session_state["last_fetch_time"] = now_kst_str()
else:
    data = {key: pd.DataFrame() for key, _ in API_LIST}
    selected_rc_no = int(target_rc_no)
    selected_start_time = start_time
    schedule_message = "데이터 수집 전"
    schedule_active = False
    schedule_df = pd.DataFrame()

if use_sample and all(df.empty for df in data.values()):
    # 테스트용 샘플
    sample = pd.DataFrame({
        "chulNo": [1,2,3,4,5,6,7,8,9,10,11],
        "hrName": ["스마트파워","강호리더","메가브레인","스피드헌터","골든에이스","블랙윈드","파워스톰","드래곤킹","레이싱퀸","로드챔프","청운호"],
        "rcDate": [target_date]*11,
        "meet": ["서울"]*11,
        "rcNo": [int(target_rc_no)]*11,
    })
    data["body"] = sample.copy()
    data["gear"] = sample.copy()
    data["today_odds"] = sample.copy()

env = {"weather": weather, "track": track, "sand": sand, "wind": wind, "distance": distance_pref}
score_df = extract_chulno_base(data, target_date, track_place, int(selected_rc_no))
result, sim_df = make_recommendation(score_df, env, int(sim_count))
alert_status = "대기"

rows_total = sum(len(df) for df in data.values() if df is not None)
connected_count = sum(1 for df in data.values() if df is not None and not df.empty)

if auto_save and result.get("추천금액", 0) > 0 and result.get("공격삼쌍승") != "-":
    append_csv(RECO_FILE, {
        "저장시각": now_kst_str(),
        "날짜": target_date,
        "경마장": track_place,
        "경주번호": int(selected_rc_no),
        **result,
    })


# =========================
# 대시보드 UI
# =========================
left, right = st.columns([1.1, 1.0])

with left:
    combo_display = result.get("공격삼쌍승", "-")
    odds_display = result.get("예상배당", 0)
    judge = result.get("판정", "관망")
    badge = "🎯 소액 공격" if result.get("추천금액", 0) > 0 else "🛡️ 관망"

    st.markdown(
        f"""
<div class="big-card">
  <div class="small">🎯 최종결과 <span style="float:right;background:#138a52;padding:8px 14px;border-radius:10px;">{badge}</span></div>
  <div style="font-size:25px;margin-top:20px;">{track_place} {int(selected_rc_no)}R · 출발 {selected_start_time}</div>
  <div class="combo">{combo_display}</div>
  <div class="odds">{odds_display}배</div>
</div>
""",
        unsafe_allow_html=True,
    )

with right:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="metric-card"><div class="metric-title">🛡️ 신뢰도</div><div class="metric-value">{result.get("신뢰도", 0)}%</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card"><div class="metric-title">📈 수익기대</div><div class="metric-value" style="font-size:38px;">{result.get("수익기대","-")}</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card"><div class="metric-title">🎯 적중기대</div><div class="metric-value" style="font-size:38px;color:#f76707;">{result.get("적중기대","-")}</div></div>""", unsafe_allow_html=True)

    st.markdown("### 🌿 환경 반영")
    e1, e2, e3 = st.columns(3)
    e1.metric("날씨", weather)
    e2.metric("주로", track)
    e3.metric("모래", sand)
    e4, e5, e6 = st.columns(3)
    e4.metric("바람", wind)
    e5.metric("거리", distance_pref)
    e6.metric("시뮬", f"{int(sim_count)}회")

st.divider()

a, b, c = st.columns([1, 1.2, 1.2])

with a:
    st.markdown("### 🛡️ 방어 조합")
    if result.get("추천금액", 0) > 0:
        st.write(f"1️⃣ 삼복승: **{result.get('방어삼복승','-')}**")
        st.write(f"2️⃣ 보조 삼쌍승: **{result.get('보조삼쌍승','-')}**")
    else:
        st.warning("현재 경주 chulNo 부족 또는 조건 미달 → 관망")
    st.markdown("### 💰 자금 잠금 규칙")
    st.write(f"오늘 추천금액: **{result.get('추천금액',0):,}원**")
    st.write(f"상태: **{result.get('자금상태','-')}**")
    st.caption("자동구매 아님 · 공식 화면으로 이동 후 수동 판단")

with b:
    st.markdown("### 📊 삼쌍승 시뮬레이션")
    st.dataframe(sim_df, use_container_width=True, height=260)

with c:
    st.markdown("### 🔌 API 연결 데이터 행수")
    api_status = []
    for key, label in API_LIST:
        df = data.get(key, pd.DataFrame())
        api_status.append({
            "API": key,
            "상태": "연결됨" if not df.empty else "없음",
            "행수": len(df),
            "마번후보": chulno_col(df) or "",
        })
    st.dataframe(pd.DataFrame(api_status), use_container_width=True, height=260)

st.divider()

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["경주시간표", "말별 점수표", "API 원본/진단", "과거 추천 로그", "URL 예시(Key 숨김)", "허브/알림"])

with tab1:
    st.caption("경주시간표 기준으로 출발 30분 전부터 자동 분석합니다.")
    if schedule_df is None or schedule_df.empty:
        st.info("경주시간표 데이터가 없습니다. race API URL 또는 시간 컬럼을 확인하세요.")
    else:
        show_schedule = schedule_df.copy()
        try:
            show_schedule["분석상태"] = show_schedule["경주번호"].apply(lambda x: "현재 분석 대상" if int(x) == int(selected_rc_no) else "")
        except Exception:
            pass
        st.dataframe(show_schedule.drop(columns=["출발datetime", "분석시작"], errors="ignore"), use_container_width=True, height=320)
    st.write(f"자동 선택: **{selected_rc_no}R** / 출발 **{selected_start_time}** / 상태: **{schedule_message}**")

with tab2:
    st.caption("점수표는 body / gear / today_odds / first_odds / third_odds의 chulNo만 사용합니다.")
    st.dataframe(score_df, use_container_width=True, height=430)

with tab3:
    diag_rows = []
    for key, _ in API_LIST:
        df = data.get(key, pd.DataFrame())
        diag_rows.append({
            "API": key,
            "행수": len(df),
            "컬럼수": len(df.columns) if not df.empty else 0,
            "컬럼목록": ", ".join(map(str, df.columns[:12])) if not df.empty else "",
        })
    st.dataframe(pd.DataFrame(diag_rows), use_container_width=True, height=360)
    if errors:
        with st.expander("보조 API 오류 보기", expanded=False):
            st.write(errors)

with tab4:
    reco_df = safe_read_csv(RECO_FILE)
    if reco_df.empty:
        st.info("과거 추천 로그가 없습니다.")
    else:
        st.dataframe(reco_df.tail(100), use_container_width=True, height=360)

with tab5:
    examples = []
    for key, label in API_LIST:
        examples.append({
            "API": key,
            "요청URL": mask_secret_url(build_api_url(api_urls.get(key, ""), api_key)),
        })
    st.dataframe(pd.DataFrame(examples), use_container_width=True, height=360)


with tab6:
    st.caption("Google Sheets 허브와 강력추천 알림 기록입니다.")
    if sheets_enabled():
        st.success("Google Sheets 허브 설정 감지")
    else:
        st.warning("Google Sheets 허브 미설정: Secrets에 SHEET_ID / SERVICE_ACCOUNT_JSON을 넣어야 저장됩니다.")

    htab1, htab2, htab3 = st.tabs(["실시간 상태", "강력알림 기록", "허브 추천"])
    with htab1:
        st.dataframe(hub_read("realtime_status", 100), use_container_width=True, height=300)
    with htab2:
        st.dataframe(hub_read("alerts", 100), use_container_width=True, height=300)
    with htab3:
        st.dataframe(hub_read("recommendations", 100), use_container_width=True, height=300)


st.caption("도박 수익 보장 아님 · 자동구매 아님 · 데이터 오류/지연 가능 · 최종 판단은 사용자 책임")
