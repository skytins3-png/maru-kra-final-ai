\
    @echo off
    chcp 65001 > nul
    title MARU KRA GitHub 저장소 처음 받기

    echo.
    echo GitHub 저장소 주소를 입력하세요.
    echo 예: https://github.com/skytins3-png/maru-kra-final-ai.git
    echo.
    set /p REPO_URL=GitHub 저장소 주소: 

    if "%REPO_URL%"=="" (
        echo 저장소 주소가 비어 있습니다.
        pause
        exit /b 1
    )

    cd /d %USERPROFILE%\Desktop
    git clone %REPO_URL%

    echo.
    echo 완료. 바탕화면에 저장소 폴더가 만들어졌습니다.
    echo 그 폴더 안에 수정 파일들을 넣고 업로드_자동.bat 를 실행하세요.
    pause
