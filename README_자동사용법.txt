MARU KRA 자동 업로드 + 자동 깨우기 키트

포함 기능
1. app.py / requirements.txt / README.md 자동 GitHub 업로드
2. GitHub Actions로 Streamlit 앱 자동 깨우기
   - 한국시간 09:00 1회
   - 한국시간 10:00~18:30 사이 30분마다
3. 기존 앱 기능 유지
   - 실시간 19API
   - API Key 저장
   - 한국시간 KST
   - 허브 저장/불러오기
   - 시간표/빅데이터/성공실패 복기

사용법 A: GitHub 저장소 폴더가 이미 컴퓨터에 있을 때
1. 이 ZIP을 압축 풉니다.
2. 압축 푼 안의 모든 파일을 GitHub 저장소 폴더 maru-kra-final-ai 안에 복사합니다.
   특히 app.py, requirements.txt, README.md, .github 폴더가 들어가야 합니다.
3. 업로드_자동.bat 를 더블클릭합니다.
4. 성공하면 GitHub에 자동 업로드되고 Streamlit Cloud가 자동 재배포합니다.

사용법 B: GitHub 저장소 폴더가 없을 때
1. 저장소_처음받기.bat 실행
2. GitHub 저장소 주소 입력
   예: https://github.com/skytins3-png/maru-kra-final-ai.git
3. 바탕화면에 저장소 폴더가 생기면, 그 안에 이 ZIP의 파일들을 복사
4. 업로드_자동.bat 실행

자동 깨우기 설정
GitHub 저장소에서:
Settings → Secrets and variables → Actions → New repository secret

이름:
STREAMLIT_APP_URL

값:
형의 Streamlit 앱 주소
예:
https://maru-kra-final-ai.streamlit.app

이걸 넣어야 .github/workflows/maru_auto_wakeup.yml 이 앱을 깨웁니다.

주의
- GitHub 업로드 자동화는 형 컴퓨터에서 업로드_자동.bat 실행할 때만 컴퓨터가 켜져 있으면 됩니다.
- Streamlit 앱 자동 깨우기는 GitHub 서버가 실행하므로 형 컴퓨터가 꺼져 있어도 됩니다.
- GitHub Actions 스케줄은 몇 분 늦게 실행될 수 있습니다.
- Streamlit 앱 자체의 30분 전 분석은 앱이 깨어나서 실행될 때 작동합니다.
