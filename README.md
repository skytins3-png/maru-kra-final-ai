# MARU KRA SECRETS AUTOLOAD ENGINE

Streamlit Secrets에서 API Key와 API URL을 자동으로 불러오는 버전입니다.

## 장점
- app.py를 새로 배포해도 Secrets 값은 유지됩니다.
- API Key와 URL을 다시 입력하지 않아도 됩니다.
- 기본 API 주소만 넣어도 자동완성됩니다.
- 앱 내부 저장도 가능하지만, 최우선은 Secrets입니다.

## GitHub 업로드
압축 해제 후 아래 2개만 업로드하세요.

- app.py
- requirements.txt

README.md는 선택입니다.

## Streamlit Secrets 예시

Streamlit Cloud > App settings > Secrets 에 아래처럼 넣으세요.

```toml
[maru]
API_KEY = "형님_API_KEY"

RACE_URL = "https://apis.data.go.kr/B551015/API186_1"
ENTRY_URL = "https://apis.data.go.kr/B551015/API23_1"
HORSE_URL = "https://apis.data.go.kr/B551015/API310"
BODY_URL = "https://apis.data.go.kr/B551015/API25_1"
GEAR_URL = "https://apis.data.go.kr/B551015/API24_1"
RATING_URL = "https://apis.data.go.kr/B551015/API..."
ODDS_URL = "https://apis.data.go.kr/B551015/API..."
TODAY_ODDS_URL = "https://apis.data.go.kr/B551015/API..."
RESULT_DETAIL_URL = "https://apis.data.go.kr/B551015/API..."
RACE_RECORD_URL = "https://apis.data.go.kr/B551015/API..."
START_EXAM_URL = "https://apis.data.go.kr/B551015/API..."
JUDGE_URL = "https://apis.data.go.kr/B551015/API..."
JOCKEY_CHANGE_URL = "https://apis.data.go.kr/B551015/API..."
WEATHER_ALERT_URL = "https://apis.data.go.kr/..."
CORNER_PACE_URL = "https://apis.data.go.kr/B551015/API..."
POPULARITY_URL = "https://apis.data.go.kr/B551015/API..."
FIRST_ODDS_URL = "https://apis.data.go.kr/B551015/API..."
SECOND_ODDS_URL = "https://apis.data.go.kr/B551015/API..."
THIRD_ODDS_URL = "https://apis.data.go.kr/B551015/API..."
KRA_URL = "https://m.kra.co.kr/main.do"
```

## 주의
수익 보장 앱이 아닙니다. 자동구매 기능도 없습니다.
분석, 기록, 손실제한, 공식 KRA 이동 기능입니다.
