@echo off
chcp 65001 >nul
title MARU KRA FINAL TOTAL AI 실행
cd /d "%~dp0"
echo ========================================
echo MARU KRA FINAL TOTAL AI 실행
echo ========================================
echo 브라우저가 안 열리면 http://localhost:8501 입력
echo 핸드폰에서 보려면 같은 와이파이에서 Network URL 입력
python.exe -m streamlit run app.py --server.address 0.0.0.0
pause
