@echo off
title Scanner Control Launcher
color 0A

echo =====================================================
echo      Scanner Control Launcher - Auto Setup and Start
echo =====================================================
echo.

:: 1. Check if Python is installed
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is NOT installed on this system!
    echo Please install Python from: https://www.python.org/downloads/
    pause
    exit
)

:: 2. Move to folder where this BAT is located
cd /d "%~dp0"

:: 3. Ensure required Python packages are installed
echo.
echo Checking required Python packages...
echo.

python -c "import requests" 2>NUL
if %errorlevel% neq 0 (
    echo Installing Requests...
    pip install requests
)

python -c "import pystray" 2>NUL
if %errorlevel% neq 0 (
    echo Installing pystray...
    pip install pystray
)

echo.
echo All required packages are installed.
echo.

:RUN_SCANNER
echo Starting start_scanner.py ...
echo (Do NOT close this window or the scanner will stop.)
echo.

:: 4. Run the scanner script
python start_scanner.py
if %errorlevel% neq 0 (
    echo.
    echo =====================================================
    echo Scanner crashed! Restarting in 5 seconds...
    echo =====================================================
    timeout /t 5 /nobreak >nul
    goto RUN_SCANNER
)

:: If script exits normally, just close the window
exit
