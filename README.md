# MARU KRA AUTO URL COMPLETE ENGINE

기본 API 주소만 넣어도 앱이 자동으로 요청주소를 완성하는 버전입니다.

예:
https://apis.data.go.kr/B551015/API186_1

자동으로 붙는 값:
- serviceKey
- pageNo=1
- numOfRows=100
- resultType=json
- rcDate=오늘날짜
- meet=경마장코드

그래도 API마다 필수 파라미터가 다를 수 있으니, 특정 API가 계속 HTTP 500이면 공공데이터 상세페이지의 미리보기 URL을 사용하세요.

GitHub에는 app.py, requirements.txt 두 개만 올리면 됩니다.
