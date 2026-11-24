@echo off
setlocal enabledelayedexpansion
title AI Clipper for Instagram & Youtube Shorts (AIYT Clipper) — By Mohsin Khawaja

echo =================================================================
echo   AI Clipper for Instagram ^& Youtube Shorts (AIYT Clipper)
echo   "Autonomous AI Video Clipper for Shorts, Reels ^& TikTok"
echo   Developed by Mohsin Khawaja (@csib.mohsin)
echo =================================================================
echo.

:: 1. Check for Python
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found in your system PATH!
    echo Please install Python 3.10 or higher from:
    echo   https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: 2. Check for FFmpeg
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo [WARNING] FFmpeg was not detected in standard system PATH.
    echo Searching candidate Windows locations...
    python -c "import config; exit(0 if config.FFMPEG_EXE and 'ffmpeg' in config.FFMPEG_EXE.lower() else 1)" >nul 2>&1
    if errorlevel 1 (
        echo [NOTICE] FFmpeg is required for video rendering.
        echo To install FFmpeg automatically on Windows, run in PowerShell:
        echo   winget install Gyan.FFmpeg
        echo.
    ) else (
        echo [*] FFmpeg auto-detected from local package path!
    )
)

:: 3. Check and install Python dependencies
python -c "import fastapi, uvicorn, faster_whisper, cv2, yt_dlp" >nul 2>&1
if errorlevel 1 (
    echo [*] Checking and installing required Python packages...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install packages from requirements.txt.
        echo Please ensure you have an active internet connection.
        pause
        exit /b 1
    )
    echo [*] Dependencies verified and ready.
    echo.
)

:: 4. Start AIYT Clipper Web Dashboard
echo [*] Starting AIYT Clipper Web Dashboard at http://127.0.0.1:8000 ...
python app.py
if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with an error code.
    pause
)

