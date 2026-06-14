형님 수정 순서

1. GitHub에서 app.py를 다운로드하거나, 컴퓨터의 kra_horse_dashboard 폴더를 엽니다.
2. 이 압축 안의 fix_saved_count_error.py 파일을 app.py와 같은 폴더에 넣습니다.
3. CMD/터미널에서 아래 명령 실행:

   python fix_saved_count_error.py

4. app_fixed.py가 만들어지면 그 파일 내용을 app.py에 덮어씁니다.
5. GitHub에 app.py로 커밋하면 Streamlit Cloud가 자동 재배포합니다.

이번 패치 내용:
- saved_count 기본값 0 보강
- observation_records가 있으면 저장 건수를 자동 계산
- 화면 출력 중 saved_count 미정의로 앱이 터지는 문제 방어

주의:
- 이 패치는 NameError: saved_count 오류를 막는 긴급복구용입니다.
- 이후 Google Sheet 주소/API 주소 연결 문제는 별도로 잡아야 합니다.
