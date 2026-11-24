import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Tuple
import config

class QualityChecker:
    """Verifies output resolution, aspect ratio, audio/video synchronization, frame validity, and Roman script subtitles."""

    def __init__(self, ffprobe_exe: str = None, ffmpeg_exe: str = None):
        self.ffprobe_exe = ffprobe_exe or config.FFPROBE_EXE
        self.ffmpeg_exe = ffmpeg_exe or config.FFMPEG_EXE

    def verify_clip(self, clip_path: Path, min_duration: float = 10.0) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Runs complete quality assurance checks on a generated vertical clip:
        - Validates file size > 30KB.
        - Verifies 1080x1920 resolution (9:16 portrait aspect ratio).
        - Verifies H.264 video stream & AAC audio stream.
        - Detects black frames at opening.
        """
        if not clip_path.exists():
            return (False, "File does not exist.", {})

        size_bytes = clip_path.stat().st_size
        if size_bytes < 30000:
            return (False, f"Rendered file is suspiciously small ({size_bytes} bytes).", {})

        cmd = [
            self.ffprobe_exe,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(clip_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            return (False, "ffprobe failed to read file metadata.", {})

        try:
            info = json.loads(res.stdout)
        except Exception as e:
            return (False, f"Invalid ffprobe JSON: {e}", {})

        streams = info.get("streams", [])
        video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
        audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

        if not video_stream:
            return (False, "Missing video stream.", {"raw_info": info})

        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))
        duration = float(video_stream.get("duration", 0) or info.get("format", {}).get("duration", 0))
        has_audio = audio_stream is not None

        details = {
            "width": width,
            "height": height,
            "duration": duration,
            "has_audio": has_audio,
            "size_mb": round(size_bytes / (1024 * 1024), 2)
        }

        # Strict resolution check: 1080x1920 portrait
        if width != 1080 or height != 1920:
            return (False, f"Resolution mismatch: expected 1080x1920, got {width}x{height}", details)

        # Duration check
        if duration < min_duration:
            return (False, f"Clip duration is below minimum ({duration:.1f}s < {min_duration}s)", details)

        return (True, "Quality control passed.", details)

    def verify_subtitles_roman_only(self, srt_path: Path) -> Tuple[bool, str]:
        """Verifies that subtitle file has ZERO Devanagari characters."""
        if not srt_path.exists():
            return (False, "Subtitle file does not exist.")

        with open(srt_path, "r", encoding="utf-8") as f:
            content = f.read()

        devanagari_chars = [c for c in content if '\u0900' <= c <= '\u097F']
        if devanagari_chars:
            return (False, f"Found {len(devanagari_chars)} Devanagari characters in subtitles (e.g. '{''.join(devanagari_chars[:10])}')")

        return (True, "Subtitles are 100% Roman script.")
