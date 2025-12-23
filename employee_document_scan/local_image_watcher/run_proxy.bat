@echo off
title Employee Document Watcher
color 0A

echo =====================================================
echo      Employee Document Watcher - Auto Setup and Start
echo =====================================================
echo.

:: 1. Check if Python is installed
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is NOT installed on this system!
    echo Please install Python from: https://www.python.org/downloads/
    echo After installation, run this file again.
    pause
    exit
)

:: 2. Move to folder where this BAT is located
cd /d "%~dp0"

echo.
echo Checking required Python packages...
echo.

:: 3. Install requests if missing
python -c "import requests" 2>NUL
if %errorlevel% neq 0 (
    echo Installing Requests...
    pip install requests
)

echo.
echo All required packages are installed.
echo.

echo Starting watcher.py ...
echo (Do NOT close this window or the watcher will stop.)
echo.

:: 4. Run the watcher
python local_image_watcher.py

echo.
echo =====================================================
echo The Employee Document Watcher has stopped or crashed.
echo Close this window or press any key to restart later.
echo =====================================================
pause

