# MARU KRA HUB STRONG ALERT ENGINE

허브 실시간 저장 + 강력추천 문자/Webhook/화면알림 버전입니다.

## 핵심 기능

- 경주시간표 기준 출발 30분 전 자동 분석
- API 19개 실시간 자동 수집
- Google Sheets 허브 실시간 저장
- 강력추천 조건 발생 시 화면 경고음/진동
- 강력추천 조건 발생 시 Webhook 문자 연동
- Telegram 알림 연동 가능
- 중복 알림 방지
- 허브/알림 탭 추가

## 허브 저장 탭

Google Sheets에 아래 탭을 자동 생성합니다.

- realtime_status
- recommendations
- alerts
- api_status
- score_snapshots

## 강력추천 조건

기본값:

- 판정: 소액 공격 / 강력추천 / 소액 가능
- 신뢰도 72% 이상
- 추천금액 1,000원 이상
- 공격삼쌍승 조합 존재

사이드바에서 신뢰도 기준을 조정할 수 있습니다.

## Streamlit Secrets 예시

```toml
[google_sheets]
SHEET_ID = "구글시트_ID"
SERVICE_ACCOUNT_JSON = '''
{
  "type": "service_account",
  "project_id": "...",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "서비스계정@프로젝트.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "..."
}
'''

[alerts]
ALERT_WEBHOOK_URL = "문자/알림 서비스 Webhook URL"
TELEGRAM_BOT_TOKEN = "텔레그램봇토큰"
TELEGRAM_CHAT_ID = "채팅ID"
```

## 문자 알림 방식

앱에서 직접 휴대폰 SMS를 보내는 게 아니라,
ALERT_WEBHOOK_URL에 연결된 문자/알림 서비스로 메시지를 전달합니다.

## GitHub 업로드

압축 해제 후 아래 2개만 업로드하세요.

- app.py
- requirements.txt
