# MARU KRA REALTIME 19API HUB - KEY SAVE + KST

## 이번 수정
- 공공데이터 API Key 입력란 추가
- 화면 표시: `공공데이터 API Key: ************`
- `[API Key 저장]` 버튼 추가
- 저장한 키를 앱 내부 `maru_kra_data/maru_kra_local_settings.json`에 저장
- Streamlit Secrets에 키가 있으면 자동 불러오기
- 모든 시간 표시를 한국시간(KST) 기준으로 표시
- 원본 `MARU_KRA_NO_REINPUT_API_ENGINE(1).zip`의 19개 API URL 유지
- 실시간 API 호출 / API 진단 / 허브 저장 불러오기 유지

## 업로드
1. ZIP 압축 풀기
2. GitHub 저장소에 `app.py`, `requirements.txt`, `README.md` 업로드해서 덮어쓰기
3. Commit changes
4. Streamlit Cloud Reboot

## 참고
화면에서 키를 저장하면 같은 Streamlit 서버에서는 유지됩니다.
Streamlit Cloud가 재배포/재시작되면 내부 파일 저장이 초기화될 수 있으니, 가장 안정적인 방식은 Secrets에도 함께 저장하는 것입니다.

Secrets 예시:

[maru]
API_KEY = "공공데이터_일반인증키"
