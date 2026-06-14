# MARU KRA 자동 API 연결판

이 버전은 공공데이터 API Key와 API URL을 화면에서 다시 입력하지 않도록 정리한 버전입니다.

## 업로드 파일
- app.py
- requirements.txt

## 적용 방법
1. GitHub 저장소에서 기존 app.py, requirements.txt를 이 파일로 덮어쓰기
2. Commit changes
3. Streamlit 앱 Reboot

## API Key 적용 방식
앱 화면에서 키를 입력하지 않습니다.
아래 순서로 자동 불러옵니다.

1. Streamlit Secrets
2. 기존 저장 설정 파일: maru_kra_data/api_settings.json
3. 기존 저장 설정 파일: maru_settings.json

Streamlit Secrets 예시:

```toml
[maru]
API_KEY = "공공데이터_API_KEY"
```

또는 최상단에:

```toml
API_KEY = "공공데이터_API_KEY"
```

## 실시간 API URL
KRA API URL 19개는 앱 기본값으로 내장되어 있습니다.
필요하면 Streamlit Secrets에서 덮어쓸 수 있습니다.

## 중요
- 자동구매 기능 없음
- 마번 자동선택 없음
- 금액 자동입력 없음
- KRA 공식 화면으로 이동 후 직접 확인하고 수동구매하는 구조
