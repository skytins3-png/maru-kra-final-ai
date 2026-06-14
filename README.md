# MARU KRA NO REINPUT REALTIME 19API HUB

## 이번 수정 핵심
- 사용자가 올린 `MARU_KRA_NO_REINPUT_API_ENGINE(1).zip`의 실제 19개 API URL을 유지했습니다.
- 이전처럼 가짜/더미 URL로 바꾸지 않았습니다.
- 앱 화면에서 API Key/18개 URL을 다시 입력하지 않습니다.
- API Key는 Streamlit Secrets에서 자동 로드합니다.
- 실시간 API 호출 → 분석 → 허브 저장/불러오기 흐름으로 구성했습니다.
- API가 500/0건이어도 앱이 멈추지 않고 진단 화면에 표시합니다.

## 업로드
1. ZIP 압축 풀기
2. GitHub 저장소에 app.py, requirements.txt, README.md 업로드해서 덮어쓰기
3. Commit changes
4. Streamlit Cloud Reboot

## Secrets
Streamlit Cloud → Manage app → Settings → Secrets:

[maru]
API_KEY = "공공데이터_일반인증키"

선택 Google Sheet 허브:

[google_sheets]
SHEET_ID = "구글시트_ID"
SERVICE_ACCOUNT_JSON = "서비스계정_JSON_전체"
