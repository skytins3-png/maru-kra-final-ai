# MARU KRA NO REINPUT API ENGINE

API 주소를 다시 입력하지 않도록 기본 URL을 앱에 내장한 버전입니다.

## 업로드
- app.py
- requirements.txt
- pages/hub.py

기존 pages/hub.py는 반드시 덮어쓰기 하세요.

## Streamlit Secrets 최소 설정

```toml
[maru]
API_KEY = "공공데이터_API_KEY"
```

URL은 앱 기본값이 자동 입력됩니다.
