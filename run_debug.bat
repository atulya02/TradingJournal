@echo off
cd /d "%~dp0"
title Trading Journal V24 - Debug
python app.py
echo.
echo Exit code: %ERRORLEVEL%
pause
