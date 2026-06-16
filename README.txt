MARU KRA MOBILE IMAGE UI FULL PROGRAM

이번 버전은 PC 기능은 그대로 유지하고, 모바일 화면만 사용자가 보낸 이미지 스타일에 맞춰 수정한 전체 통합본입니다.

모바일 화면:
- 검정/골드 프리미엄 UI
- MARU KRA 실시간 분석 상단바
- 지금 놓치면 아까운 추천 카드
- 복승 3-7 / 삼쌍승 3-7-10 표시
- 예상배당 / 신뢰도 / 위험도 표시
- 10초 수동구매 모드
- 복승 1만원 + 삼쌍승 1천원 구매 확인
- 공식 구매페이지 입력값 요약
- 추천 조합 복사
- 공식 마권구매 열기
- 다음 추천 보기

PC 화면:
- 기존 전체 대시보드 유지
- 19개 API ON/OFF
- 아침 1회 / 30분 / 5분 자동 수집
- 자동 허브
- AI 학습상태
- 빅데이터 손익계산
- 전략별 ROI
- 전체 분석/관리/통계 기능 유지

모바일 접속 주소:
https://내앱주소.streamlit.app/?mode=mobile

PC 접속 주소:
https://내앱주소.streamlit.app

자동구매/자동결제는 없습니다.
추천 확인 후 공식 페이지에서 사용자가 직접 입력하고 최종 확정합니다.

실행:
streamlit run app.py


[모바일 자동 전환 수정]
- 휴대폰(Android/iPhone)에서 접속하면 ?mode=mobile 이 없어도 자동으로 모바일 10초 구매 전용 화면이 열립니다.
- PC에서 모바일 화면 테스트: https://앱주소.streamlit.app/?mode=mobile
- 휴대폰에서 PC 전체 관리 화면 보기: https://앱주소.streamlit.app/?mode=pc
- 모바일 전용 주소가 안 먹는 PWA/홈화면 환경에서도 User-Agent 자동감지로 모바일 화면을 우선 표시합니다.
