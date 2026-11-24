import os
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

import config
from core.project_manager import ProjectManager, Project
from core.downloader import Downloader
from core.transcriber import Transcriber
from core.ai_analyzer import AIAnalyzer
from core.clip_selector import ClipSelector
from core.face_tracker import FaceTracker
from core.subtitle_generator import SubtitleGenerator
from core.renderer import Renderer
from core.quality_checker import QualityChecker
from core.report_generator import ReportGenerator

class ClippingPipeline:
    """Master workflow orchestrator for AI-powered YouTube Long-to-Short clipping."""

    def __init__(self):
        self.project_manager = ProjectManager()
        self.downloader = Downloader()
        self.transcriber = Transcriber()
        self.ai_analyzer = AIAnalyzer()
        self.clip_selector = ClipSelector()
        self.face_tracker = FaceTracker()
        self.subtitle_generator = SubtitleGenerator()
        self.renderer = Renderer()
        self.quality_checker = QualityChecker()
        self.report_generator = ReportGenerator()

    def process_video(
        self,
        youtube_url: str,
        progress_callback: Optional[Callable[[float, str, Optional[Dict[str, Any]]], None]] = None
    ) -> Dict[str, Any]:
        """
        Executes the complete end-to-end clipping process.
        """
        def report_step(percent: float, message: str, extra: Optional[Dict[str, Any]] = None):
            print(f"[{percent:05.1f}%] {message}")
            if progress_callback:
                progress_callback(percent, message, extra)

        cfg = config.load_config()
        user_crop_mode = cfg.get("crop_mode", "auto")
        target_clips = cfg.get("target_clip_count", 5)

        # 1. Video ID and Info
        report_step(2.0, "Extracting video metadata...")
        video_id = self.downloader.extract_video_id(youtube_url)
        if not video_id:
            raise ValueError(f"Invalid YouTube URL: {youtube_url}")

        video_info = self.downloader.get_video_info(youtube_url)
        title = video_info.get("title", "YouTube_Video")
        duration = video_info.get("duration", 0)

        # 2. Setup Project Folder
        report_step(5.0, f"Initializing project folder for '{title}'...")
        project: Project = self.project_manager.create_project(video_id, title)
        project.save_original_info(video_info)

        # 3. Download Source Video & Audio
        report_step(10.0, "Downloading source video (1080p) & audio stream...")
        source_video_path = self.downloader.download_video(
            youtube_url,
            project.temp_dir,
            progress_callback=lambda pct, msg: report_step(10.0 + (pct * 0.15), msg)
        )

        report_step(25.0, "Extracting audio track for transcription...")
        audio_path = self.downloader.extract_audio(source_video_path, project.temp_dir / "audio_16k.wav")

        # 4. Transcribe Speech
        report_step(30.0, "Generating speech transcript with word-level timestamps...")
        transcript_data = self.transcriber.get_transcript(
            video_id,
            audio_path,
            progress_callback=lambda pct, msg: report_step(30.0 + (pct * 0.15), msg)
        )
        if not transcript_data:
            raise RuntimeError("Failed to extract or generate video transcript.")
        project.save_transcript(transcript_data)

        # 5. AI Content Analysis
        report_step(45.0, "AI analyzing content for viral hooks, retention moments, and key stories...")
        raw_clips = self.ai_analyzer.analyze_and_select_clips(video_info, transcript_data, target_count=target_clips)
        if not raw_clips:
            raise RuntimeError("AI analyzer could not identify candidate clips.")

        # 6. Refine Selection & Boundary Snapping
        report_step(55.0, "Refining clip boundaries and verifying sentence completeness...")
        refined_clips = self.clip_selector.refine_clips(raw_clips, transcript_data, duration)

        # 7. Render Individual Clips
        total_clips = len(refined_clips)
        rendered_clips = []
        used_hook_titles: set = set()
        report_step(60.0, f"Processing {total_clips} vertical clips (Face tracking, ASS captions, 1080x1920 H.264 rendering)...")

        for idx, clip in enumerate(refined_clips):
            clip_num = clip["clip_number"]
            start_t = clip["start_time"]
            end_t = clip["end_time"]
            dur = clip["duration"]
            pct_base = 60.0 + (idx / max(total_clips, 1)) * 32.0

            report_step(pct_base, f"Clip #{clip_num}: Analyzing visuals and tracking active speaker...")
            visual_info = self.face_tracker.analyze_clip_visuals(
                source_video_path,
                start_t,
                end_t,
                user_crop_mode=user_crop_mode
            )
            clip["visual_info"] = visual_info
            clip["recommended_layout"] = visual_info.get("layout", "center_zoom_blurred_bg")

            # Generate Subtitles & Top AI Hook Title
            report_step(pct_base + 1.0, f"Clip #{clip_num}: Generating synchronized captions & AI Hook Title...")
            srt_path = project.get_caption_path(clip_num)
            ass_path = project.get_ass_caption_path(clip_num)
            clip_transcript = clip.get("transcript_slice", [])

            # Ensure unique, content-tailored hook title is present on clip
            raw_hook = clip.get("hook_title", "").strip().upper()
            if raw_hook and raw_hook not in used_hook_titles and len(raw_hook.split()) <= 7:
                clip_hook_title = raw_hook
                used_hook_titles.add(clip_hook_title)
            else:
                clip_hook_title = self.ai_analyzer.generate_smart_hook_title(
                    text=clip.get("text", ""),
                    hook_text=clip.get("hook_text", ""),
                    fallback_title=clip.get("title", ""),
                    video_title=title,
                    clip=clip,
                    video_info=video_info,
                    used_titles=used_hook_titles
                )
            clip["hook_title"] = clip_hook_title

            self.subtitle_generator.generate_srt(clip_transcript, srt_path)
            self.subtitle_generator.generate_ass(
                clip_transcript,
                ass_path,
                face_y_ratio=visual_info.get("face_y_ratio", 0.4),
                has_bottom_facecam=visual_info.get("has_bottom_facecam", False),
                hook_title=clip_hook_title if cfg.get("enable_hook_title", True) else None,
                clip_duration=dur
            )

            # Render 9:16 Video
            clip_output_path = project.get_clip_path(clip_num)
            thumb_path = project.get_thumbnail_path(clip_num)

            report_step(pct_base + 2.0, f"Clip #{clip_num}: Rendering 1080x1920 video with FFmpeg...")
            self.renderer.render_clip(
                source_video_path=source_video_path,
                start_time=start_t,
                duration=dur,
                visual_info=visual_info,
                ass_sub_path=ass_path,
                output_clip_path=clip_output_path,
                thumbnail_path=thumb_path,
                bg_blur_style=cfg.get("bg_blur_style", "cinematic")
            )

            # Quality Check
            report_step(pct_base + 3.0, f"Clip #{clip_num}: Performing quality control validation...")
            passed, qc_msg, qc_details = self.quality_checker.verify_clip(clip_output_path)
            clip["quality_control"] = {
                "passed": passed,
                "message": qc_msg,
                "details": qc_details
            }

            if not passed:
                print(f"[QualityControl] Clip #{clip_num} failed QC: {qc_msg}")

            rendered_clips.append(clip)

        # 8. Save Clip Analysis
        report_step(94.0, "Saving project analysis and metadata...")
        project.save_clip_analysis(rendered_clips)

        # 9. Generate HTML Report
        report_step(96.0, "Generating interactive HTML clip report...")
        self.report_generator.generate_html_report(video_info, rendered_clips, project.report_path)

        # 10. Finalize & Cleanup Temp
        report_step(99.0, "Finalizing project outputs...")
        project.clean_temp()

        report_step(100.0, f"Successfully created {len(rendered_clips)} vertical clips!", {
            "project_dir": str(project.dir),
            "report_path": str(project.report_path),
            "clips": rendered_clips
        })

        return {
            "project_dir": str(project.dir),
            "project_name": project.dir.name,
            "report_path": str(project.report_path),
            "video_info": video_info,
            "clips": rendered_clips
        }

