# MARU KRA CHULNO ONLY SCORE ENGINE

말별 점수표와 추천 조합을 chulNo 기준으로만 제한한 버전입니다.

## 수정 내용

- 말별 점수표를 body / gear / today_odds의 chulNo로만 생성
- entry enNo 사용 금지
- horse hrNo 사용 금지
- age, chaksun, prize, rating 숫자 마번 사용 금지
- 현재 경주 chulNo 3두 미만이면 관망
- 1~14번 밖 조합은 시뮬레이션/추천에서 제거
- 관망이면 조합 표시를 '-'로 처리
- 잘못된 조합은 저장/허브 동기화 차단

## GitHub 업로드

압축 해제 후 아래 2개만 덮어쓰기 업로드하세요.

- app.py
- requirements.txt
