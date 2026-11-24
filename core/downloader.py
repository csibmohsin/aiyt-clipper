import os
import re
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import yt_dlp
import config

class Downloader:
    """Handles downloading YouTube videos, audio, and extracting metadata with yt-dlp."""

    def __init__(self, ffmpeg_bin_dir: Optional[str] = None):
        self.ffmpeg_bin_dir = ffmpeg_bin_dir or config.FFMPEG_BIN_DIR

    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """Extract the YouTube video ID from various URL formats."""
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'youtu\.be\/([0-9A-Za-z_-]{11})',
            r'youtube\.com\/embed\/([0-9A-Za-z_-]{11})',
            r'youtube\.com\/shorts\/([0-9A-Za-z_-]{11})',
            r'youtube\.com\/live\/([0-9A-Za-z_-]{11})'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def get_video_info(self, url: str) -> Dict[str, Any]:
        """Fetch video metadata without downloading video stream."""
        opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "js_runtimes": {"node": {}},
            "remote_components": ["ejs:github"],
        }
        if self.ffmpeg_bin_dir:
            opts["ffmpeg_location"] = self.ffmpeg_bin_dir

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_id = info.get("id") or self.extract_video_id(url)
            return {
                "id": video_id,
                "url": url,
                "title": info.get("title", "Untitled Video"),
                "uploader": info.get("uploader", "Unknown Creator"),
                "duration": info.get("duration", 0),
                "description": info.get("description", ""),
                "thumbnail": info.get("thumbnail", ""),
                "view_count": info.get("view_count", 0),
                "tags": info.get("tags", []),
                "categories": info.get("categories", []),
                "width": info.get("width", 1920),
                "height": info.get("height", 1080),
                "fps": info.get("fps", 30)
            }

    def download_video(
        self,
        url: str,
        output_dir: Path,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Path:
        """Download high quality 1080p video + audio stream into target directory."""
        output_dir.mkdir(parents=True, exist_ok=True)
        target_path = output_dir / "source_video.mp4"
        outtmpl = str(output_dir / "source_video.%(ext)s")

        # If already downloaded, avoid re-downloading
        if target_path.exists() and target_path.stat().st_size > 100000:
            if progress_callback:
                progress_callback(100.0, "Source video already downloaded.")
            return target_path

        def ytdl_hook(d):
            if d['status'] == 'downloading':
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded_bytes = d.get('downloaded_bytes') or 0
                percent = (downloaded_bytes / total_bytes * 100) if total_bytes > 0 else 0
                speed = d.get('speed', 0) or 0
                speed_str = f"{speed / (1024 * 1024):.1f} MB/s" if speed else ""
                msg = f"Downloading source video: {percent:.1f}% ({speed_str})"
                if progress_callback:
                    progress_callback(min(percent, 99.0), msg)
            elif d['status'] == 'finished':
                if progress_callback:
                    progress_callback(99.0, "Merging audio and video streams...")

        # Robust yt-dlp configuration to eliminate 403 Forbidden errors:
        # 1. Do NOT force restrictive player_client (which causes SABR skips and 403 on fallback).
        # 2. Use Node.js runtime for solving JS signature challenges.
        # 3. Avoid http_chunk_size limits that trigger CDN range throttling drops.
        opts = {
            "format": "bestvideo[height<=1080][protocol=https]+bestaudio[protocol=https]/best[height<=1080][protocol=https]/best[height<=1080]/best",
            "outtmpl": outtmpl,
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [ytdl_hook],
            "js_runtimes": {"node": {}},
            "remote_components": ["ejs:github"],
            "retries": 15,
            "fragment_retries": 15,
        }
        if self.ffmpeg_bin_dir:
            opts["ffmpeg_location"] = self.ffmpeg_bin_dir

        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

        # Locate resulting mp4 file
        if target_path.exists():
            if progress_callback:
                progress_callback(100.0, "Download completed.")
            return target_path

        # Find any matching source_video file
        for f in output_dir.glob("source_video.*"):
            if f.suffix in [".mp4", ".mkv", ".webm"]:
                return f

        raise FileNotFoundError("Failed to locate downloaded video output file.")

    def extract_audio(self, video_path: Path, output_audio_path: Optional[Path] = None) -> Path:
        """Extract clean 16kHz mono WAV audio for speech transcription."""
        if output_audio_path is None:
            output_audio_path = video_path.parent / "audio_16k.wav"

        if output_audio_path.exists() and output_audio_path.stat().st_size > 1000:
            return output_audio_path

        import subprocess
        ffmpeg_exe = config.FFMPEG_EXE
        cmd = [
            ffmpeg_exe, "-y",
            "-i", str(video_path),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            str(output_audio_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg audio extraction failed: {res.stderr[:300]}")
        return output_audio_path
