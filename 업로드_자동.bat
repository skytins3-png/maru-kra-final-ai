\
    @echo off
    chcp 65001 > nul
    title MARU KRA GitHub 자동 업로드

    echo.
    echo ==========================================
    echo   MARU KRA GitHub 자동 업로드
    echo ==========================================
    echo.

    where git > nul 2> nul
    if errorlevel 1 (
        echo [오류] Git 이 설치되어 있지 않습니다.
        echo Git 다운로드: https://git-scm.com/download/win
        echo 설치 후 다시 실행하세요.
        pause
        exit /b 1
    )

    if not exist ".git" (
        echo [오류] 현재 폴더가 GitHub 저장소 폴더가 아닙니다.
        echo.
        echo 사용법:
        echo 1. 이 파일과 app.py, requirements.txt, README.md 를
        echo    GitHub 저장소 폴더 maru-kra-final-ai 안에 넣으세요.
        echo 2. 그 폴더에서 업로드_자동.bat 를 더블클릭하세요.
        echo.
        pause
        exit /b 1
    )

    echo [1/5] 현재 폴더 확인
    cd

    echo.
    echo [2/5] Git 상태 확인
    git status

    echo.
    echo [3/5] 변경 파일 추가
    git add app.py requirements.txt README.md .github/workflows/maru_auto_wakeup.yml

    echo.
    echo [4/5] 커밋 생성
    set MSG=MARU KRA auto update %date% %time%
    git commit -m "%MSG%"
    if errorlevel 1 (
        echo.
        echo [안내] 커밋할 변경사항이 없거나 커밋이 실패했습니다.
        echo 그래도 push를 시도합니다.
    )

    echo.
    echo [5/5] GitHub로 업로드
    git push origin main
    if errorlevel 1 (
        echo.
        echo [오류] push 실패.
        echo GitHub 로그인이 필요하거나 브랜치 이름이 main이 아닐 수 있습니다.
        echo 브랜치가 master이면 아래 명령을 직접 실행하세요:
        echo git push origin master
        echo.
        pause
        exit /b 1
    )

    echo.
    echo ==========================================
    echo 완료! GitHub 업로드 성공.
    echo Streamlit Cloud가 자동 재배포합니다.
    echo 앱에서 Reboot app 또는 Ctrl+F5 하면 더 빠릅니다.
    echo ==========================================
    echo.
    pause
