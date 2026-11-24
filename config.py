import os
import sys
import json
import shutil
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "OUTPUT"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = BASE_DIR / "config.json"

# Candidate FFmpeg paths on Windows
FFMPEG_CANDIDATE_PATHS = [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages" / "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe" / "ffmpeg-9.0.2-full_build" / "bin",
    Path("C:/Program Files/ffmpeg/bin"),
    Path("C:/ffmpeg/bin"),
]

def locate_ffmpeg():
    """Locate ffmpeg and ffprobe executables."""
    ffmpeg_in_path = shutil.which("ffmpeg")
    if ffmpeg_in_path:
        return os.path.dirname(ffmpeg_in_path)

    for p in FFMPEG_CANDIDATE_PATHS:
        if p.exists() and (p / "ffmpeg.exe").exists():
            return str(p)

    winget_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
    if winget_dir.exists():
        for found in winget_dir.glob("**/ffmpeg.exe"):
            return str(found.parent)

    return ""

FFMPEG_BIN_DIR = locate_ffmpeg()
if FFMPEG_BIN_DIR and FFMPEG_BIN_DIR not in os.environ.get("PATH", ""):
    os.environ["PATH"] = FFMPEG_BIN_DIR + os.pathsep + os.environ.get("PATH", "")

FFMPEG_EXE = shutil.which("ffmpeg") or (os.path.join(FFMPEG_BIN_DIR, "ffmpeg.exe") if FFMPEG_BIN_DIR else "ffmpeg")
FFPROBE_EXE = shutil.which("ffprobe") or (os.path.join(FFMPEG_BIN_DIR, "ffprobe.exe") if FFMPEG_BIN_DIR else "ffprobe")

# Color mapping for ASS format (&HAABBGGRR)
HIGHLIGHT_COLORS = {
    "yellow": "&H0000FFFF",  # Vivid Yellow
    "green": "&H0000FF00",   # Neon Green
    "cyan": "&H00FFFF00",    # Sky Blue / Cyan
    "magenta": "&H00FF00FF"  # Hot Pink / Magenta
}

# Subtitle vertical margin mapping (from bottom of 1920 canvas)
SUBTITLE_POSITIONS = {
    "bottom_safe": 260,     # In bottom blurred bar (default, never covers faces)
    "above_facecam": 680,   # Directly above webcam reaction (mid screen)
    "center": 900           # Dramatic center screen pop
}

# Default settings
DEFAULT_CONFIG = {
    "gemini_api_key": os.environ.get("GEMINI_API_KEY", ""),
    "gemini_model": "gemini-3.8-flash",
    "crop_mode": "center_zoom",           # 'center_zoom', 'smart_crop', 'split_screen', 'blurred_bg', 'auto'
    "bg_blur_style": "cinematic",          # 'cinematic', 'heavy', 'subtle', 'black_bars'
    "enable_hook_title": True,             # Enable/Disable Top Hook Title
    "hook_title_style": "bold_headline",   # 'bold_headline', 'solid_yellow', 'solid_white'
    "hook_title_color": "yellow",          # 'yellow', 'cyan', 'magenta', 'white'
    "subtitle_position": "bottom_safe",    # 'bottom_safe', 'above_facecam', 'center'
    "caption_highlight": "yellow",         # 'yellow', 'green', 'cyan', 'magenta'
    "caption_font": "Arial Black",         # 'Arial Black', 'Impact', 'Arial'
    "default_min_duration": 30,
    "default_max_duration": 60,
    "absolute_min_duration": 15,
    "absolute_max_duration": 90,
    "target_clip_count": 5,
    "output_width": 1080,
    "output_height": 1920,
    "fps": 30,
    "caption_style": {
        "font_name": "Arial Black",
        "font_size": 50,
        "primary_color": "&H00FFFFFF",
        "highlight_color": "&H0000FFFF",
        "outline_color": "&H00000000",
        "outline_width": 4.0,
        "shadow_depth": 2.0,
        "margin_v": 260,
        "max_words_per_batch": 4
    }
}

def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                config = dict(DEFAULT_CONFIG)
                config.update(saved)
                return config
        except Exception as e:
            print(f"[Config] Error loading config: {e}")
    return dict(DEFAULT_CONFIG)

def save_config(new_config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(new_config, f, indent=2)
        return True
    except Exception as e:
        print(f"[Config] Error saving config: {e}")
        return False
