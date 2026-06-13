
import streamlit as st
import pandas as pd
import requests, json, random
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from collections import Counter

st.set_page_config(page_title="MARU KRA MULTI API", page_icon="🐎", layout="centered")

DATA_DIR = Path("maru_kra_data")
DATA_DIR.mkdir(exist_ok=True)
SETTINGS_FILE = DATA_DIR / "api_settings.json"
RECO_FILE = DATA_DIR / "recommendation_bigdata_log.csv"
RESULT_FILE = DATA_DIR / "race_result_records.csv"
COMPARE_FILE = DATA_DIR / "prediction_result_compare_log.csv"
WEIGHT_FILE = DATA_DIR / "learning_weights.json"

DEFAULT_SETTINGS = {
    "api_key":"", "save_api_key":False,
    "race_url":"", "entry_url":"", "horse_url":"", "body_url":"", "gear_url":"",
    "rating_url":"", "odds_url":"", "today_odds_url":"", "result_detail_url":"",
    "race_record_url":"", "start_exam_url":"", "judge_url":"", "jockey_change_url":"", "weather_alert_url":"", "corner_pace_url":"",
    "kra_url":"https://m.kra.co.kr/main.do", "track_place":"서울",
    "bankroll":100000, "unit_bet":1000, "daily_loss_limit":30000,
    "profit_unlock":200000, "daily_budget":30000, "daily_entries_limit":3
}
DEFAULT_WEIGHTS = {
    "recent":2.2, "win_rate":0.45, "place_rate":0.30, "rating":0.55,
    "rating_delta":1.8, "odds_value":1.0, "environment":1.0,
    "weight_penalty":1.4, "risk_penalty":1.0
}

def load_json(path, default):
    if path.exists():
        try:
            x = json.loads(path.read_text(encoding="utf-8"))
            d = dict(default); d.update(x); return d
        except Exception:
            pass
    return dict(default)

def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def read_table(path):
    if path.exists():
        try: return pd.read_csv(path)
        except Exception: return pd.DataFrame()
    return pd.DataFrame()

def append_table(path, row):
    df = read_table(path)
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return df

def today():
    return datetime.now().strftime("%Y-%m-%d")

settings = load_json(SETTINGS_FILE, DEFAULT_SETTINGS)
weights = load_json(WEIGHT_FILE, DEFAULT_WEIGHTS)
save_json(WEIGHT_FILE, weights)

# ---------------- UI sidebar ----------------
st.sidebar.title("MARU KRA 저장형")
st.sidebar.caption("URL 입력 후 저장하면 새로고침해도 유지됩니다.")

api_key = st.sidebar.text_input("공공데이터 API Key", value=settings["api_key"] if settings.get("save_api_key") else "", type="password")
save_api_key = st.sidebar.checkbox("API Key도 저장", value=bool(settings.get("save_api_key", False)))

race_url = st.sidebar.text_area("1. 경주정보 API URL", value=settings.get("race_url",""), height=52)
entry_url = st.sidebar.text_area("2. 출전 등록말 API URL", value=settings.get("entry_url",""), height=52)
horse_url = st.sidebar.text_area("3. 경주마 상세정보 API URL", value=settings.get("horse_url",""), height=52)
body_url = st.sidebar.text_area("4. 출전마 체중 API URL", value=settings.get("body_url",""), height=52)
gear_url = st.sidebar.text_area("5. 장구/폐출혈 API URL", value=settings.get("gear_url",""), height=52)
rating_url = st.sidebar.text_area("6. 레이팅 API URL", value=settings.get("rating_url",""), height=52)
odds_url = st.sidebar.text_area("7. 매출/확정배당률 API URL", value=settings.get("odds_url",""), height=52)
today_odds_url = st.sidebar.text_area("8. 시행당일 확정배당률 API URL", value=settings.get("today_odds_url",""), height=52)
result_detail_url = st.sidebar.text_area("9. AI기반 경주결과상세 API URL", value=settings.get("result_detail_url",""), height=52)
race_record_url = st.sidebar.text_area("10. 경주기록/요약성적표 API URL", value=settings.get("race_record_url",""), height=52)
start_exam_url = st.sidebar.text_area("11. 출발심사 결과 API URL", value=settings.get("start_exam_url",""), height=52)
judge_url = st.sidebar.text_area("12. 경주심판 정보 API URL", value=settings.get("judge_url",""), height=52)
jockey_change_url = st.sidebar.text_area("13. 기수변경 API URL", value=settings.get("jockey_change_url",""), height=52)
weather_alert_url = st.sidebar.text_area("14. 기상특보 API URL", value=settings.get("weather_alert_url",""), height=52)
corner_pace_url = st.sidebar.text_area("15. 코너별 통과순위/주로빠르기 API URL", value=settings.get("corner_pace_url",""), height=52)

st.sidebar.markdown("---")
places = ["서울","부산경남","제주"]
track_place = st.sidebar.selectbox("경마장", places, index=places.index(settings.get("track_place","서울")) if settings.get("track_place","서울") in places else 0)
auto_weather = st.sidebar.checkbox("날씨/바람 자동수집", True)
manual_weather = st.sidebar.selectbox("날씨 보정", ["자동","맑음","흐림","비","눈"])
manual_track = st.sidebar.selectbox("주로 보정", ["자동","건조","양호","다습","포화","불량"])
manual_sand = st.sidebar.selectbox("모래 보정", ["자동","가벼움","보통","무거움"])
manual_wind = st.sidebar.selectbox("바람 보정", ["자동","없음","뒷바람","맞바람","측풍"])
distance_type = st.sidebar.selectbox("거리 성향", ["단거리","중거리","장거리"], index=1)

st.sidebar.markdown("---")
sim_count = st.sidebar.selectbox("시뮬레이션 횟수", [100,300,500,1000], index=1)
risk_mode = st.sidebar.selectbox("위험 성향", ["안전형","균형형","공격형"])
bankroll = st.sidebar.number_input("운영잔고", min_value=0, max_value=10000000, value=int(settings["bankroll"]), step=10000)
unit_bet = st.sidebar.number_input("20만원 전 1회 기준금액", min_value=100, max_value=10000, value=int(settings["unit_bet"]), step=100)
daily_loss_limit = st.sidebar.number_input("하루 손실 투자금지", min_value=10000, max_value=300000, value=int(settings["daily_loss_limit"]), step=1000)
profit_unlock = st.sidebar.number_input("3만원 운영 허용 기준", min_value=50000, max_value=1000000, value=int(settings["profit_unlock"]), step=10000)
daily_budget = st.sidebar.number_input("허용 후 하루 투자한도", min_value=10000, max_value=100000, value=int(settings["daily_budget"]), step=1000)
daily_entries_limit = st.sidebar.number_input("하루 최대 진입", min_value=1, max_value=10, value=int(settings["daily_entries_limit"]))
auto_save_reco = st.sidebar.checkbox("추천 자동저장", True)
use_sample = st.sidebar.checkbox("데이터 없으면 샘플 사용", True)
kra_url = st.sidebar.text_input("KRA 공식 바로가기", value=settings["kra_url"])

if st.sidebar.button("API 설정 저장", use_container_width=True):
    save_json(SETTINGS_FILE, {
        "api_key": api_key if save_api_key else "", "save_api_key": save_api_key,
        "race_url":race_url, "entry_url":entry_url, "horse_url":horse_url, "body_url":body_url,
        "gear_url":gear_url, "rating_url":rating_url, "odds_url":odds_url, "today_odds_url":today_odds_url,
        "result_detail_url":result_detail_url, "race_record_url":race_record_url,
        "start_exam_url":start_exam_url, "judge_url":judge_url, "jockey_change_url":jockey_change_url, "weather_alert_url":weather_alert_url, "corner_pace_url":corner_pace_url,
        "kra_url":kra_url, "track_place":track_place, "bankroll":bankroll, "unit_bet":unit_bet,
        "daily_loss_limit":daily_loss_limit, "profit_unlock":profit_unlock, "daily_budget":daily_budget,
        "daily_entries_limit":daily_entries_limit
    })
    st.sidebar.success("저장 완료")

if st.sidebar.button("API 설정 초기화", use_container_width=True):
    if SETTINGS_FILE.exists(): SETTINGS_FILE.unlink()
    st.sidebar.warning("초기화 완료. 새로고침하세요.")

# ---------------- style ----------------
st.markdown("""
<style>
.block-container{max-width:780px;padding-top:1rem}
.logo{font-size:35px;font-weight:1000;color:#0f172a}.ai{font-size:16px;background:#2563eb;color:white;border-radius:8px;padding:4px 8px}.sub{font-size:17px;color:#0f766e;font-weight:900}
.status{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:12px 0}.stat{background:#f8fafc;border:1px solid #e2e8f0;border-radius:14px;padding:10px;text-align:center}.stat b{color:#0f766e}
.main{background:radial-gradient(circle at 78% 8%,#0f766e,#064e3b 40%,#022c22);color:white;border-radius:28px;padding:26px;margin:18px 0;box-shadow:0 12px 30px rgba(2,44,34,.22)}
.badge{display:inline-block;background:#16a34a;color:white;padding:9px 16px;border-radius:12px;font-size:20px;font-weight:1000}.wait{background:#64748b}.stop{background:#dc2626}.time{float:right;font-size:18px;font-weight:900}.race{font-size:22px;margin-top:25px;color:#ecfdf5}.combo{font-size:42px;font-weight:1000;margin-top:14px}.odds{font-size:34px;color:#facc15;font-weight:1000;text-align:right}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.mini{background:white;border:1px solid #e5e7eb;border-radius:18px;padding:14px 7px;text-align:center;box-shadow:0 4px 14px rgba(15,23,42,.08)}.mini .label{font-size:14px;font-weight:900}.mini .value{font-size:22px;color:#047857;font-weight:1000}
.box{background:white;border:1px solid #e5e7eb;border-radius:20px;padding:17px;margin:13px 0;box-shadow:0 4px 14px rgba(15,23,42,.06)}
.env{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.env div{background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:9px;text-align:center}
.stButton>button{background:#0b5cff;color:white;font-size:19px;font-weight:1000;border-radius:18px;height:58px}.note{text-align:center;color:#64748b;font-size:14px}
@media(max-width:700px){.combo{font-size:32px}.odds{font-size:28px}.mini .value{font-size:19px}.env{font-size:12px}}
</style>
""", unsafe_allow_html=True)

# ---------------- data fetch ----------------
def repl(url):
    return url.replace("{serviceKey}", api_key.strip()).replace("{today}", datetime.now().strftime("%Y%m%d"))


def build_api_url(url):
    """
    기본 API 주소만 넣어도 자동으로 공공데이터 요청주소를 완성합니다.
    예: https://apis.data.go.kr/B551015/API186_1
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

    # 자주 필요한 날짜값 자동 추가
    if all(x not in low for x in ["rcdate=", "racedate=", "meetdate=", "stndate=", "date=", "ymd="]):
        extras.append("rcDate=" + ymd)

    # 자주 필요한 경마장값 자동 추가
    if "meet=" not in low and "meetcd=" not in low and "rcourse=" not in low:
        try:
            meet_map = {"서울":"1", "제주":"2", "부산경남":"3"}
            extras.append("meet=" + meet_map.get(track_place, "1"))
        except Exception:
            extras.append("meet=1")

    if extras:
        url = url + sep + "&".join(extras)

    return url

def replace_url(url):
    return build_api_url(url)

def json_to_df(x):
    if isinstance(x, dict):
        for path in [["response","body","items","item"],["response","body","item"],["items","item"],["data"],["result"]]:
            cur=x; ok=True
            for p in path:
                if isinstance(cur,dict) and p in cur: cur=cur[p]
                else: ok=False; break
            if ok: x=cur; break
    if isinstance(x, dict): x=[x]
    return pd.json_normalize(x)

def xml_to_df(txt):
    root = ET.fromstring(txt)
    rows=[]
    for item in root.findall(".//item"):
        rows.append({c.tag:c.text for c in item})
    return pd.DataFrame(rows)

def fetch(url):
    if not url.strip(): return pd.DataFrame(), ""
    if "{serviceKey}" in url and not api_key.strip(): return pd.DataFrame(), "API Key 미입력"
    try:
        r=requests.get(repl(url),timeout=15)
        if r.status_code!=200: return pd.DataFrame(), f"HTTP {r.status_code}"
        txt=r.text.strip()
        if txt.startswith("{") or txt.startswith("[") or "json" in r.headers.get("content-type",""):
            return json_to_df(r.json()), ""
        return xml_to_df(txt), ""
    except Exception as e:
        return pd.DataFrame(), str(e)

def env_now():
    env={"weather":"맑음","track":"양호","sand":"보통","wind":"없음","source":"기본","precip":0,"wind_speed":0}
    if auto_weather:
        coords={"서울":(37.4438,127.0165),"부산경남":(35.1545,128.8782),"제주":(33.4097,126.3934)}
        lat,lon=coords[track_place]
        try:
            u=f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation,weather_code,wind_speed_10m&timezone=Asia%2FSeoul"
            cur=requests.get(u,timeout=8).json().get("current",{})
            p=float(cur.get("precipitation",0) or 0); ws=float(cur.get("wind_speed_10m",0) or 0); code=int(cur.get("weather_code",0) or 0)
            weather="비" if p>=0.3 or code in [51,53,55,61,63,65,80,81,82,95,96,99] else ("흐림" if code in [1,2,3,45,48] else "맑음")
            if code in [71,73,75,77,85,86]: weather="눈"
            wind="없음" if ws<2 else ("측풍" if ws<5 else "맞바람")
            track,sand=("포화","무거움") if weather in ["비","눈"] and p>=3 else (("다습","무거움") if weather in ["비","눈"] and p>=1 else (("다습","보통") if weather in ["비","눈"] else ("양호","보통")))
            env={"weather":weather,"track":track,"sand":sand,"wind":wind,"source":"자동수집","precip":p,"wind_speed":ws}
        except Exception as e:
            env["source"]="자동실패"
    if manual_weather!="자동": env["weather"]=manual_weather
    if manual_track!="자동": env["track"]=manual_track
    if manual_sand!="자동": env["sand"]=manual_sand
    if manual_wind!="자동": env["wind"]=manual_wind
    return env

def sample_all():
    race=pd.DataFrame([{"경마장":track_place,"경주번호":"6","출발시간":"16:05"}])
    horse=pd.DataFrame([
        {"마번":5,"마명":"마루스피드","최근순위":2,"승률":18,"복승률":42,"부담중량":55,"예상배당":9.2,"레이팅":78,"레이팅변화":4,"선행력":82,"추입력":70,"파워":78,"순발력":84,"습주로":72,"모래적응":80},
        {"마번":11,"마명":"그린파워","최근순위":3,"승률":15,"복승률":38,"부담중량":54.5,"예상배당":7.8,"레이팅":75,"레이팅변화":2,"선행력":75,"추입력":78,"파워":82,"순발력":77,"습주로":80,"모래적응":83},
        {"마번":2,"마명":"블루런","최근순위":4,"승률":12,"복승률":35,"부담중량":53,"예상배당":12.5,"레이팅":72,"레이팅변화":3,"선행력":70,"추입력":83,"파워":76,"순발력":79,"습주로":84,"모래적응":75},
        {"마번":7,"마명":"라스트킹","최근순위":5,"승률":10,"복승률":30,"부담중량":55.5,"예상배당":15.4,"레이팅":70,"레이팅변화":-1,"선행력":68,"추입력":72,"파워":85,"순발력":69,"습주로":86,"모래적응":88},
        {"마번":3,"마명":"해피로드","최근순위":6,"승률":8,"복승률":25,"부담중량":56,"예상배당":22,"레이팅":66,"레이팅변화":1,"선행력":65,"추입력":74,"파워":70,"순발력":73,"습주로":68,"모래적응":71}
    ])
    risk=pd.DataFrame([{"마번":5,"출발위험":0,"주행위험":1},{"마번":11,"출발위험":1,"주행위험":0},{"마번":2,"출발위험":0,"주행위험":0},{"마번":7,"출발위험":1,"주행위험":1},{"마번":3,"출발위험":2,"주행위험":1}])
    return race,horse,risk

def no_col(df):
    for c in ["마번","horseNo","hrNo","번호","chulNo","출전번호"]:
        if c in df.columns: return c
    return None

def normalize(df):
    if df.empty: return df
    d=df.copy()
    c=no_col(d)
    if c: d["마번"]=pd.to_numeric(d[c],errors="coerce").fillna(0).astype(int)
    return d

def merge(base, df):
    if df.empty: return base
    d=normalize(df)
    if "마번" not in d.columns or "마번" not in base.columns: return base
    return base.merge(d,on="마번",how="left",suffixes=("","_x"))

def load_all():
    env=env_now()
    urls=[
        ("race",race_url),("entry",entry_url),("horse",horse_url),("body",body_url),("gear",gear_url),
        ("rating",rating_url),("odds",odds_url),("today_odds",today_odds_url),("result_detail",result_detail_url),
        ("race_record",race_record_url),("start_exam",start_exam_url),("judge",judge_url),("jockey_change",jockey_change_url),("weather_alert",weather_alert_url),("corner_pace",corner_pace_url)
    ]
    data={}; errs=[]
    for name,url in urls:
        df,err=fetch(url)
        data[name]=df
        if err: errs.append(f"{name}:{err}")
    if use_sample and data["entry"].empty and data["horse"].empty:
        race,horse,risk=sample_all()
        data["race"]=race; data["entry"]=horse; data["horse"]=horse; data["start_exam"]=risk
    return data, env, errs

def budget_status():
    df=read_table(RESULT_FILE)
    if df.empty: return dict(today_bet=0,today_profit=0,total_profit=0,entries=0,locked=False,reason="정상")
    if "저장시각" in df.columns: df["날짜"]=pd.to_datetime(df["저장시각"],errors="coerce").dt.strftime("%Y-%m-%d")
    else: df["날짜"]=""
    for c in ["투입금","환급금"]:
        if c not in df.columns: df[c]=0
        df[c]=pd.to_numeric(df[c],errors="coerce").fillna(0)
    t=df[df["날짜"]==today()]
    tb=float(t["투입금"].sum()); tr=float(t["환급금"].sum()); tp=tr-tb
    total=float(df["환급금"].sum()-df["투입금"].sum())
    entries=int((t["투입금"]>0).sum())
    locked=False; reason="정상"
    if tp <= -float(daily_loss_limit): locked=True; reason=f"하루 손실 {int(daily_loss_limit):,}원 도달"
    elif entries>=int(daily_entries_limit): locked=True; reason=f"하루 {int(daily_entries_limit)}회 완료"
    elif tb>=float(daily_budget): locked=True; reason=f"하루 {int(daily_budget):,}원 한도 도달"
    return dict(today_bet=tb,today_profit=tp,total_profit=total,entries=entries,locked=locked,reason=reason)

def num(df,names,default):
    for c in names:
        if c in df.columns: return pd.to_numeric(df[c],errors="coerce").fillna(default)
    return pd.Series([default]*len(df),index=df.index)

def env_bonus(row,env):
    front=float(row.get("선행력",70)); late=float(row.get("추입력",70)); power=float(row.get("파워",70)); speed=float(row.get("순발력",70)); wet=float(row.get("습주로",70)); sandfit=float(row.get("모래적응",70))
    b=0
    if env["weather"] in ["비","눈"] or env["track"] in ["다습","포화","불량"]: b+=(wet-70)*.13+(power-70)*.08
    else: b+=(speed-70)*.10+(front-70)*.06
    if env["sand"]=="무거움": b+=(sandfit-70)*.12+(power-70)*.08
    if env["wind"]=="맞바람": b+=(late-70)*.07-(front-75)*.04
    if distance_type=="단거리": b+=(speed-70)*.09+(front-70)*.08
    elif distance_type=="장거리": b+=(power-70)*.08+(late-70)*.07
    return round(b,1)

def analyze(data, env):
    base=normalize(data.get("entry",pd.DataFrame()))
    if base.empty: base=normalize(data.get("horse",pd.DataFrame()))
    if base.empty: return pd.DataFrame(),{},[]
    for k in ["horse","body","gear","rating","odds","today_odds","start_exam","judge","jockey_change","corner_pace"]:
        base=merge(base,data.get(k,pd.DataFrame()))
    if "마번" not in base.columns: base["마번"]=range(1,len(base)+1)
    h=base.copy()
    recent=num(h,["최근순위","최근성적","rank","ord","착순"],5)
    win=num(h,["승률","winRate"],10); place=num(h,["복승률","placeRate"],25)
    rating=num(h,["레이팅","rating","rt"],65); delta=num(h,["레이팅변화","ratingDelta"],0)
    weight=num(h,["부담중량","weight","wgBudam"],55); odds=num(h,["예상배당","배당","odds","winOdds","단승배당","확정배당률"],12)
    srisk=num(h,["출발위험","startRisk"],0); rrisk=num(h,["주행위험","runRisk"],0)
    corner_rank=num(h,["코너순위","cornerRank","passRank","통과순위","코너통과순위"],5)
    pace_fast=num(h,["주로빠르기","trackSpeed","paceSpeed","빠르기"],0)
    late_gain=num(h,["4코너상승","cornerGain","추입상승","순위상승"],0)
    h["환경보정"]=h.apply(lambda r: env_bonus(r,env),axis=1)
    h["코너보정"]=(10-corner_rank.clip(1,10))*0.9 + late_gain.clip(-5,5)*1.2 + pace_fast.clip(-5,5)*0.7
    h["최종점수"]=(10-recent.clip(1,10))*weights["recent"]+win.clip(0,50)*weights["win_rate"]+place.clip(0,80)*weights["place_rate"]+(rating.clip(40,100)-40)*weights["rating"]+delta.clip(-10,10)*weights["rating_delta"]+odds.clip(1,100).apply(lambda x:12 if 6<=x<=25 else (7 if 25<x<=45 else 2))*weights["odds_value"]+h["환경보정"]*weights["environment"]+h["코너보정"]-(weight-54).clip(lower=0)*weights["weight_penalty"]-(srisk*2+rrisk*1.5)*weights["risk_penalty"]
    nums=h["마번"].tolist(); scores=h["최종점수"].tolist()
    weather_alert_df = data.get("weather_alert", pd.DataFrame())
    alert_risk = 0
    if not weather_alert_df.empty:
        alert_text = " ".join(weather_alert_df.astype(str).head(20).values.flatten().tolist())
        if any(x in alert_text for x in ["강풍","호우","대설","폭염","한파","주의보","경보"]):
            alert_risk = 1
    vol=5.5 + (1.8 if env["weather"] in ["비","눈"] else 0) + (.8 if env["wind"] in ["맞바람","측풍"] else 0) + (1.2 if alert_risk else 0)
    if risk_mode=="안전형": vol*=.9
    if risk_mode=="공격형": vol*=1.15
    random.seed(42); cnt=Counter()
    for _ in range(sim_count):
        noisy=[(n,s+random.gauss(0,vol)) for n,s in zip(nums,scores)]
        top=tuple(str(x[0]) for x in sorted(noisy,key=lambda x:x[1],reverse=True)[:3])
        cnt[top]+=1
    combos=cnt.most_common(10); top=combos[0][0]
    conf=min(95,max(35,round(combos[0][1]/sim_count*100+48)))
    decision="소액 공격" if conf>=75 else ("소액 가능" if conf>=62 else "관망")
    b=budget_status(); rem=max(0,float(daily_budget)-b["today_bet"]); unlocked=b["total_profit"]>=profit_unlock or bankroll>=profit_unlock
    if b["locked"] or rem<=0: decision="투자금지"; amount=0
    elif decision=="관망": amount=0
    else: amount=int(min(10000 if unlocked else unit_bet, rem))
    race=data.get("race",pd.DataFrame()).iloc[0].to_dict() if not data.get("race",pd.DataFrame()).empty else {}
    result={"경마장":race.get("경마장",track_place),"경주번호":race.get("경주번호","-"),"출발시간":race.get("출발시간","-"),"판정":decision,"공격삼쌍승":" - ".join(top),"방어삼복승":" / ".join(top),"보조삼쌍승":" - ".join(combos[1][0]) if len(combos)>1 else " - ".join(top),"놓치기아까운1":" - ".join(combos[2][0]) if len(combos)>2 else "","놓치기아까운2":" - ".join(combos[3][0]) if len(combos)>3 else "","예상배당":round(float(odds.head(3).sum()*0.9),1) if len(odds)>=3 else 46.8,"신뢰도":conf,"추천금액":amount,"오늘투입":int(b["today_bet"]),"오늘손익":int(b["today_profit"]),"누적손익":int(b["total_profit"]),"오늘진입":int(b["entries"]),"자금상태":b["reason"],"기상특보위험":alert_risk}
    combo_rows=[{"조합":" - ".join(k),"반복횟수":v,"비율":round(v/sim_count*100,1)} for k,v in combos]
    return h.sort_values("최종점수",ascending=False),result,combo_rows

# ---------------- Run ----------------
if "data" not in st.session_state:
    st.session_state.data, st.session_state.env, st.session_state.errs = load_all()

st.markdown('<div class="logo">MARU KRA <span class="ai">AI</span></div><div class="sub">MULTI API PERSIST LEARNING ENGINE</div>', unsafe_allow_html=True)
c1,c2,c3=st.columns(3)
if c1.button("API 저장", use_container_width=True):
    save_json(SETTINGS_FILE, {"api_key":api_key if save_api_key else "", "save_api_key":save_api_key, "race_url":race_url, "entry_url":entry_url, "horse_url":horse_url, "body_url":body_url, "gear_url":gear_url, "rating_url":rating_url, "odds_url":odds_url, "today_odds_url":today_odds_url, "result_detail_url":result_detail_url, "race_record_url":race_record_url, "start_exam_url":start_exam_url, "judge_url":judge_url, "jockey_change_url":jockey_change_url, "weather_alert_url":weather_alert_url, "corner_pace_url":corner_pace_url, "kra_url":kra_url, "track_place":track_place, "bankroll":bankroll, "unit_bet":unit_bet, "daily_loss_limit":daily_loss_limit, "profit_unlock":profit_unlock, "daily_budget":daily_budget, "daily_entries_limit":daily_entries_limit})
    st.success("API 설정 저장 완료")
if c2.button("데이터 불러오기", use_container_width=True):
    st.session_state.data, st.session_state.env, st.session_state.errs = load_all(); st.rerun()
if c3.button("시뮬레이션", use_container_width=True):
    st.session_state.data, st.session_state.env, st.session_state.errs = load_all(); st.rerun()

data=st.session_state.data; env=st.session_state.env
score_df,result,combos=analyze(data,env)
if auto_save_reco and result:
    row={"저장시각":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"날짜":today(),**result,"날씨":env["weather"],"주로":env["track"],"모래":env["sand"],"바람":env["wind"]}
    append_table(RECO_FILE,row)

rows=sum(len(v) for v in data.values())
reco=read_table(RECO_FILE); comp=read_table(COMPARE_FILE)
st.markdown(f'<div class="status"><div class="stat">연결 데이터<br><b>{rows}</b></div><div class="stat">추천 저장<br><b>{len(reco)}</b></div><div class="stat">비교 저장<br><b>{len(comp)}</b></div></div>', unsafe_allow_html=True)
if st.session_state.errs: st.warning(" / ".join(st.session_state.errs[:3]))

badge="badge stop" if result.get("판정")=="투자금지" else ("badge wait" if result.get("판정")=="관망" else "badge")
st.markdown(f"""<div class="main"><div style="font-size:22px;font-weight:1000;margin-bottom:23px;">다중 API · 저장형 · 매경주 학습</div><span class="{badge}">{result.get('판정','대기')}</span><span class="time">{sim_count}회</span><div class="race">{result.get('경마장','-')} {result.get('경주번호','-')}R · 출발 {result.get('출발시간','-')}</div><div style="margin-top:18px;color:#d1fae5;font-size:18px;">공격 삼쌍승</div><div class="combo">{result.get('공격삼쌍승','-')}</div><div class="odds">{result.get('예상배당','-')}배</div></div>""", unsafe_allow_html=True)

st.markdown(f"""<div class="grid"><div class="mini"><div class="label">신뢰도</div><div class="value">{result.get('신뢰도',0)}%</div></div><div class="mini"><div class="label">추천금액</div><div class="value">{result.get('추천금액',0):,}원</div></div><div class="mini"><div class="label">오늘진입</div><div class="value">{result.get('오늘진입',0)} / {int(daily_entries_limit)}</div></div></div>""", unsafe_allow_html=True)

st.markdown(f"""<div class="box"><b style="font-size:21px;">자금 잠금 규칙</b><br><br>오늘 투입: <b>{result.get('오늘투입',0):,}원 / {int(daily_budget):,}원</b><br>오늘 손익: <b>{result.get('오늘손익',0):,}원</b><br>누적 손익: <b>{result.get('누적손익',0):,}원</b><br>기상특보 위험: <b>{result.get('기상특보위험',0)}</b><br>상태: <b>{result.get('자금상태','-')}</b><br><span class="note">하루 손실 -{int(daily_loss_limit):,}원 도달 시 투자금지 · API URL 저장 유지</span></div>""", unsafe_allow_html=True)

st.markdown(f"""<div class="box"><b style="font-size:21px;">조합 배분</b><br><br>방어 삼복승: <b>{result.get('방어삼복승','-')}</b><br>주력 삼쌍승: <b>{result.get('공격삼쌍승','-')}</b><br>보조 삼쌍승: <b>{result.get('보조삼쌍승','-')}</b><br>놓치기 아까운 삼쌍승: <b>{result.get('놓치기아까운1','')}</b> / <b>{result.get('놓치기아까운2','')}</b></div>""", unsafe_allow_html=True)

st.markdown(f"""<div class="box"><b style="font-size:21px;">자동 환경 반영</b><br><br><div class="env"><div>날씨<br><b>{env.get('weather','-')}</b></div><div>주로<br><b>{env.get('track','-')}</b></div><div>모래<br><b>{env.get('sand','-')}</b></div><div>바람<br><b>{env.get('wind','-')}</b></div><div>강수<br><b>{env.get('precip','-')}mm</b></div><div>출처<br><b>{env.get('source','-')}</b></div></div></div>""", unsafe_allow_html=True)

st.link_button("KRA 공식 바로가기", kra_url, use_container_width=True)
st.markdown("<div class='note'>※ 자동구매 아님 · 공식 화면으로 이동 · 수익 보장 아님 · 손실 제한/기록학습 엔진</div>", unsafe_allow_html=True)

with st.expander("결과 입력 / 예상비교 / 자가학습", expanded=False):
    actual_combo=st.text_input("실제 삼쌍 1-2-3", placeholder="예: 5-11-2")
    actual_trio=st.text_input("실제 삼복 1~3착", placeholder="예: 5/11/2")
    bet_amount=st.number_input("투입금", min_value=0, value=int(result.get("추천금액",0)), step=100)
    return_amount=st.number_input("환급금", min_value=0, value=0, step=100)
    memo=st.text_input("메모")
    if st.button("결과 저장하고 AI 학습", use_container_width=True):
        roi=((return_amount-bet_amount)/bet_amount) if bet_amount>0 else 0
        pred=result.get("공격삼쌍승","").replace(" ","")
        a=actual_combo.replace(" ","")
        trio_hit=set(result.get("방어삼복승","").replace(" ","").split("/"))==set((actual_trio or actual_combo).replace(" ","").replace("-","/").split("/"))
        tri_hit=1 if pred==a else 0
        typ="삼쌍승 적중" if tri_hit else ("삼복승 방어" if trio_hit else ("부분환급" if return_amount>0 else "미적중"))
        rec={"저장시각":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"날짜":today(),**result,"투입금":bet_amount,"환급금":return_amount,"수익률":roi,"실제삼쌍":actual_combo,"실제삼복":actual_trio,"분석결과":typ,"메모":memo}
        append_table(RESULT_FILE,rec); append_table(COMPARE_FILE,rec)
        st.success("결과 저장 + 예상비교 완료")
        st.info(typ)

with st.expander("숨겨진 분석 / 저장 데이터", expanded=False):
    st.subheader("API 연결 데이터 행수")
    st.dataframe(pd.DataFrame([{"API":k,"행수":len(v)} for k,v in data.items()]), use_container_width=True)
    st.subheader("말별 점수표")
    st.dataframe(score_df, use_container_width=True)
    st.subheader("삼쌍승 시뮬레이션")
    st.dataframe(pd.DataFrame(combos), use_container_width=True)
    st.subheader("추천 빅데이터 로그")
    st.dataframe(read_table(RECO_FILE).tail(100), use_container_width=True)
    st.subheader("예상 vs 실제 비교 로그")
    st.dataframe(read_table(COMPARE_FILE).tail(100), use_container_width=True)
    st.subheader("저장된 API 설정")
    st.json(load_json(SETTINGS_FILE, DEFAULT_SETTINGS))
