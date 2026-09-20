@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo TradeLogix Windows Installer Builder
echo ========================================

where py >nul 2>&1
if errorlevel 1 (
  echo Python launcher ^(py^) was not found.
  pause
  exit /b 1
)

where iscc >nul 2>&1
if errorlevel 1 (
  if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
  ) else if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
  ) else (
    echo Inno Setup 6 was not found. Install Inno Setup 6 first.
    echo https://jrsoftware.org/isinfo.php
    pause
    exit /b 1
  )
) else (
  set "ISCC=iscc"
)

echo [1/4] Installing Python dependencies...
py -m pip install -r requirements.txt
if errorlevel 1 goto :error
py -m pip install pyinstaller
if errorlevel 1 goto :error

echo [2/4] Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist installer rmdir /s /q installer
mkdir installer

echo [3/4] Building TradeLogix application...
pyinstaller --noconfirm --clean TradeLogix.spec
if errorlevel 1 goto :error

echo [4/4] Building Windows installer...
"%ISCC%" TradeLogix.iss
if errorlevel 1 goto :error

echo.
echo ========================================
echo BUILD COMPLETE
echo Installer: installer\TradeLogix-Setup-1.0.0.exe
echo ========================================
pause
exit /b 0

:error
echo.
echo BUILD FAILED.
pause
exit /b 1
