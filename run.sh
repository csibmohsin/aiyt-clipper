#!/usr/bin/env bash
set -e

echo "================================================================="
echo "  AI Clipper for Instagram & Youtube Shorts (AIYT Clipper)"
echo "  \"Autonomous AI Video Clipper for Shorts, Reels & TikTok\""
echo "  Developed by Mohsin Khawaja (@csib.mohsin)"
echo "================================================================="
echo ""

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 was not found in your system PATH!"
    echo "Please install Python 3.10 or higher."
    exit 1
fi

# 2. Check FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "[WARNING] ffmpeg command not found in PATH."
    echo "Please install FFmpeg using your package manager:"
    echo "  Ubuntu/Debian: sudo apt update && sudo apt install -y ffmpeg"
    echo "  macOS (Homebrew): brew install ffmpeg"
    echo ""
fi

# 3. Check and install Python dependencies
if ! python3 -c "import fastapi, uvicorn, faster_whisper, cv2, yt_dlp" &> /dev/null; then
    echo "[*] Installing required Python dependencies..."
    python3 -m pip install -r requirements.txt
    echo "[*] Dependencies installed successfully."
    echo ""
fi

# 4. Launch Web Dashboard
echo "[*] Launching AIYT Clipper Web Dashboard at http://127.0.0.1:8000 ..."
python3 app.py

