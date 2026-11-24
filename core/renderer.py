import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import config

class Renderer:
    """Renders 1080x1920 vertical videos with professional multi-layout options."""

    def __init__(self, ffmpeg_exe: Optional[str] = None):
        self.ffmpeg_exe = ffmpeg_exe or config.FFMPEG_EXE

    def render_clip(
        self,
        source_video_path: Path,
        start_time: float,
        duration: float,
        visual_info: Dict[str, Any],
        ass_sub_path: Optional[Path],
        output_clip_path: Path,
        thumbnail_path: Optional[Path] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
        bg_blur_style: str = "cinematic"
    ) -> Path:
        """
        Renders a 9:16 vertical clip (1080x1920, 30fps, H.264, AAC).
        Supports:
        - center_zoom: 0.96:1 Center-Region Zoom Crop with Blurred Background
        - smart_crop: 100% Full-Frame 9:16 Smart Face Crop
        - split_screen: 50/50 Dual Stack (top gameplay + bottom facecam)
        - blurred_bg: Classic 16:9 on full blurred canvas
        """
        output_clip_path.parent.mkdir(parents=True, exist_ok=True)
        if thumbnail_path:
            thumbnail_path.parent.mkdir(parents=True, exist_ok=True)

        layout = visual_info.get("layout", "center_zoom_blurred_bg")

        # Resolve blur filter for background
        if bg_blur_style == "heavy":
            blur_filter = "boxblur=40:8,colorchannelmixer=aa=1.0:rr=0.75:gg=0.75:bb=0.75"
        elif bg_blur_style == "subtle":
            blur_filter = "boxblur=10:3"
        elif bg_blur_style == "black_bars":
            blur_filter = "drawbox=x=0:y=0:w=1080:h=1920:color=black:t=fill"
        else:  # cinematic (default)
            blur_filter = "boxblur=22:5,colorchannelmixer=aa=1.0:rr=0.88:gg=0.88:bb=0.88"

        # Prepare ASS subtitle filter
        ass_filter_str = ""
        if ass_sub_path and ass_sub_path.exists():
            clean_ass_path = str(ass_sub_path.resolve()).replace("\\", "/").replace(":", r"\:")
            ass_filter_str = f"ass='{clean_ass_path}'"

        # 1. Split Screen Dual Stack (50/50 Top & Bottom)
        if layout == "split_screen":
            top = visual_info.get("top_crop", {"x": 480, "y": 60, "w": 960, "h": 540})
            bot = visual_info.get("bot_crop", {"x": 380, "y": 540, "w": 540, "h": 540})
            filter_complex = (
                f"[0:v]crop={top['w']}:{top['h']}:{top['x']}:{top['y']},scale=1080:960:flags=lanczos[top];"
                f"[0:v]crop={bot['w']}:{bot['h']}:{bot['x']}:{bot['y']},scale=1080:960:flags=lanczos[bot];"
                f"[top][bot]vstack=inputs=2,fps=30"
            )

        # 2. Full-frame 9:16 Smart Face Crop
        elif layout == "smart_crop":
            crop_x = visual_info.get("crop_x", 442)
            crop_w = visual_info.get("crop_width", 608)
            crop_h = visual_info.get("crop_height", 1080)
            filter_complex = f"[0:v]crop={crop_w}:{crop_h}:{crop_x}:0,scale=1080:1920:flags=lanczos,fps=30"

        # 3. Classic 16:9 on Blurred Background
        elif layout == "blurred_bg":
            filter_complex = (
                f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,{blur_filter}[bg];"
                f"[0:v]scale=1080:-2:flags=lanczos[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2,fps=30"
            )

        # 4. Default: Center-Region Zoom Crop with Blurred Background (~0.96:1)
        else:
            crop_x = visual_info.get("crop_x", 372)
            crop_w = visual_info.get("crop_width", 1038)
            crop_h = visual_info.get("crop_height", 1080)
            filter_complex = (
                f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,{blur_filter}[bg];"
                f"[0:v]crop={crop_w}:{crop_h}:{crop_x}:0,scale=1080:-2:flags=lanczos[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2,fps=30"
            )

        if ass_filter_str:
            filter_complex += f",{ass_filter_str}[outv]"
        else:
            filter_complex += "[outv]"

        cmd = [
            self.ffmpeg_exe, "-y",
            "-ss", f"{start_time:.3f}",
            "-t", f"{duration:.3f}",
            "-i", str(source_video_path),
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-map", "0:a?",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "19",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",
            "-movflags", "+faststart",
            str(output_clip_path)
        ]

        if progress_callback:
            progress_callback(f"Rendering clip ({layout})...")

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg rendering failed: {res.stderr[-400:]}")

        # Generate thumbnail at 1.5s mark
        if thumbnail_path:
            thumb_time = min(1.5, max(0.2, duration / 2.0))
            thumb_cmd = [
                self.ffmpeg_exe, "-y",
                "-ss", f"{thumb_time:.2f}",
                "-i", str(output_clip_path),
                "-vframes", "1",
                "-q:v", "2",
                str(thumbnail_path)
            ]
            subprocess.run(thumb_cmd, capture_output=True)

        return output_clip_path
