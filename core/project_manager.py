import os
import re
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
import config

class ProjectManager:
    """Manages project directories and files according to project specifications."""

    def __init__(self, base_output_dir: Optional[Path] = None):
        self.base_output_dir = base_output_dir or config.OUTPUT_DIR
        self.base_output_dir.mkdir(parents=True, exist_ok=True)

    def create_project(self, video_id: str, title: str) -> "Project":
        # Sanitize title for directory name
        clean_title = re.sub(r'[\\/*?:"<>|]', "", title).strip()
        clean_title = re.sub(r'\s+', "_", clean_title)[:40]
        project_folder_name = f"Project_{clean_title}_{video_id}"
        project_dir = self.base_output_dir / project_folder_name
        project_dir.mkdir(parents=True, exist_ok=True)

        return Project(project_dir, video_id, title)

    def get_project(self, project_name: str) -> Optional["Project"]:
        project_dir = self.base_output_dir / project_name
        if project_dir.exists() and project_dir.is_dir():
            info_file = project_dir / "original_info.json"
            video_id = ""
            title = project_name
            if info_file.exists():
                try:
                    with open(info_file, "r", encoding="utf-8") as f:
                        info = json.load(f)
                        video_id = info.get("id", "")
                        title = info.get("title", project_name)
                except Exception:
                    pass
            return Project(project_dir, video_id, title)
        return None

    def list_projects(self) -> List[Dict[str, Any]]:
        projects = []
        if not self.base_output_dir.exists():
            return projects

        for item in sorted(self.base_output_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
            if item.is_dir() and item.name.startswith("Project_"):
                info_file = item / "original_info.json"
                analysis_file = item / "clip_analysis.json"
                clips_dir = item / "clips"
                
                title = item.name
                thumbnail = ""
                duration = 0
                clip_count = 0
                created_at = item.stat().st_mtime

                if info_file.exists():
                    try:
                        with open(info_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            title = data.get("title", title)
                            thumbnail = data.get("thumbnail", "")
                            duration = data.get("duration", 0)
                    except Exception:
                        pass

                if clips_dir.exists():
                    clip_count = len(list(clips_dir.glob("*.mp4")))

                projects.append({
                    "folder_name": item.name,
                    "title": title,
                    "thumbnail": thumbnail,
                    "duration": duration,
                    "clip_count": clip_count,
                    "created_at": created_at,
                    "path": str(item)
                })
        return projects


class Project:
    """Represents a single video project with required folder structure."""

    def __init__(self, project_dir: Path, video_id: str, title: str):
        self.dir = project_dir
        self.video_id = video_id
        self.title = title

        # Required subdirectories
        self.clips_dir = self.dir / "clips"
        self.captions_dir = self.dir / "captions"
        self.thumbnails_dir = self.dir / "thumbnails"
        self.temp_dir = self.dir / "temp"

        self.clips_dir.mkdir(exist_ok=True)
        self.captions_dir.mkdir(exist_ok=True)
        self.thumbnails_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)

        # Key file paths
        self.original_info_path = self.dir / "original_info.json"
        self.transcript_path = self.dir / "transcript.json"
        self.clip_analysis_path = self.dir / "clip_analysis.json"
        self.report_path = self.dir / "report.html"

    def save_original_info(self, info: Dict[str, Any]):
        with open(self.original_info_path, "w", encoding="utf-8") as f:
            json.dump(info, f, indent=2, ensure_ascii=False)

    def load_original_info(self) -> Dict[str, Any]:
        if self.original_info_path.exists():
            with open(self.original_info_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_transcript(self, transcript_data: List[Dict[str, Any]]):
        with open(self.transcript_path, "w", encoding="utf-8") as f:
            json.dump(transcript_data, f, indent=2, ensure_ascii=False)

    def load_transcript(self) -> List[Dict[str, Any]]:
        if self.transcript_path.exists():
            with open(self.transcript_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def save_clip_analysis(self, analysis_data: List[Dict[str, Any]]):
        def default_serializer(obj):
            if hasattr(obj, 'item'):
                return obj.item()
            return str(obj)
        with open(self.clip_analysis_path, "w", encoding="utf-8") as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False, default=default_serializer)

    def load_clip_analysis(self) -> List[Dict[str, Any]]:
        if self.clip_analysis_path.exists():
            with open(self.clip_analysis_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def save_report(self, html_content: str):
        with open(self.report_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    def get_clip_path(self, clip_index: int) -> Path:
        return self.clips_dir / f"clip_{clip_index:02d}.mp4"

    def get_caption_path(self, clip_index: int) -> Path:
        return self.captions_dir / f"clip_{clip_index:02d}.srt"

    def get_ass_caption_path(self, clip_index: int) -> Path:
        return self.temp_dir / f"clip_{clip_index:02d}.ass"

    def get_thumbnail_path(self, clip_index: int) -> Path:
        return self.thumbnails_dir / f"clip_{clip_index:02d}.jpg"

    def clean_temp(self):
        """Cleans intermediate audio temporary files while preserving source video and ASS subtitles for rapid re-renders."""
        if self.temp_dir.exists():
            for f in self.temp_dir.iterdir():
                if f.name.startswith("audio_") or f.suffix in [".wav", ".pcm"]:
                    try:
                        f.unlink()
                    except Exception:
                        pass

