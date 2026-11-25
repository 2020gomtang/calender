@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 캘린더를 시작합니다...
python server.py
pause
