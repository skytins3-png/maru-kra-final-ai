@echo off
chcp 65001 >nul
title MARU KRA FINAL TOTAL AI 설치
cd /d "%~dp0"
echo ========================================
echo MARU KRA FINAL TOTAL AI 설치
echo ========================================
python.exe -m pip install --upgrade pip
python.exe -m pip install -r requirements.txt
echo.
echo 설치 완료. 아무 키나 누르세요.
pause >nul
