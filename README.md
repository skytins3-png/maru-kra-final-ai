# MARU KRA NO REINPUT API WEATHER FIX ENGINE

NameError: auto_weather 오류 수정 버전입니다.

## 수정 내용

- auto_weather 기본값 True 보강
- manual_weather / manual_track / manual_sand / manual_wind 기본값 보강
- 사이드바 환경/날씨 설정 복구
- fetch_env() 내부에서 환경 변수 안전 정의
- API URL 기본값 내장 유지
- API Key Secrets 자동 불러오기 유지
- app.py와 pages/hub.py 포함

## GitHub 업로드

압축 해제 후 아래 3개를 올리세요.

- app.py
- requirements.txt
- pages/hub.py

기존 pages/hub.py는 반드시 덮어쓰기 하세요.
