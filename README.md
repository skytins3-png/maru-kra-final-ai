# MARU KRA KST TIME FIXED ENGINE

한국 시간 기준으로 날짜가 잡히도록 수정한 버전입니다.

## 수정 내용

- Streamlit Cloud 서버시간 대신 Asia/Seoul 기준 사용
- today()를 한국시간 기준 YYYYMMDD로 고정
- 분석 날짜 기본값을 한국 날짜로 표시
- 저장시각도 한국시간으로 저장
- 허브/로그 날짜도 한국시간 기준으로 기록
- chulNo 전용 점수표 로직 유지
- 1~14번 외 조합 차단 유지

## GitHub 업로드

압축 해제 후 아래 2개만 덮어쓰기 업로드하세요.

- app.py
- requirements.txt
