@echo off
title Scanner Control Launcher
color 0A

echo =====================================================
echo      Scanner Control Launcher - Auto Setup and Start
echo =====================================================
echo.

:: Move to folder where this BAT file is located
cd /d "%~dp0"

:: Find real Python executable
set "PYTHON_EXE="

where py >nul 2>&1
if %errorlevel% equ 0 (
    py -3 -c "import sys; print(sys.executable)" > "%temp%\scanner_python_path.txt" 2>nul
    set /p PYTHON_EXE=<"%temp%\scanner_python_path.txt"
)

if "%PYTHON_EXE%"=="" (
    where python > "%temp%\scanner_python_path.txt" 2>nul
    if %errorlevel% equ 0 (
        set /p PYTHON_EXE=<"%temp%\scanner_python_path.txt"
    )
)

if "%PYTHON_EXE%"=="" (
    echo Python is NOT installed or not found properly!
    echo Please install Python from:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo Using Python:
echo %PYTHON_EXE%
echo.

"%PYTHON_EXE%" --version
echo.

:: Upgrade pip
echo Checking pip...
"%PYTHON_EXE%" -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo pip is not available. Please reinstall Python and select "Add Python to PATH".
    pause
    exit /b 1
)

:: Install required Python packages
echo Checking required Python packages...
echo.

"%PYTHON_EXE%" -c "import requests" 2>nul
if %errorlevel% neq 0 (
    echo Installing requests...
    "%PYTHON_EXE%" -m pip install requests
)

"%PYTHON_EXE%" -c "import pystray" 2>nul
if %errorlevel% neq 0 (
    echo Installing pystray...
    "%PYTHON_EXE%" -m pip install pystray
)

"%PYTHON_EXE%" -c "from PIL import Image" 2>nul
if %errorlevel% neq 0 (
    echo Installing Pillow...
    "%PYTHON_EXE%" -m pip install Pillow
)

echo.
echo All required packages are installed.
echo.

:RUN_SCANNER
echo Starting start_scanner.py ...
echo Do NOT close this window or the scanner will stop.
echo.

"%PYTHON_EXE%" start_scanner.py

echo.
echo =====================================================
echo Scanner stopped or crashed! Restarting in 5 seconds...
echo =====================================================
timeout /t 5 /nobreak >nul
goto RUN_SCANNER