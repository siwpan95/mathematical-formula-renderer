@echo off
chcp 65001 >nul
cd /d "%~dp0"
"C:\Users\13122\.workbuddy\binaries\python\versions\3.13.12\python.exe" main.py %*
pause
