import os
import sys
import json
import time
import uuid
import asyncio
import threading
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import config
from core.pipeline import ClippingPipeline
from core.project_manager import ProjectManager
from core.ai_analyzer import AIAnalyzer
from core.subtitle_generator import SubtitleGenerator
from core.renderer import Renderer
from core.report_generator import ReportGenerator

app = FastAPI(
    title="AI Clipper for Instagram & Youtube Shorts (AIYT Clipper)",
    description="Autonomous AI video clipping system that converts long-form YouTube videos into high-retention vertical shorts, reels, and TikToks. Developed by Mohsin Khawaja.",
    version="1.0.0"
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "OUTPUT"

STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# In-memory job state tracker
JOBS: Dict[str, Dict[str, Any]] = {}
ACTIVE_JOB_QUEUES: Dict[str, list] = {}

class StartJobRequest(BaseModel):
    url: str

class ConfigUpdateRequest(BaseModel):
    gemini_api_key: Optional[str] = None
    crop_mode: Optional[str] = None
    bg_blur_style: Optional[str] = None
    enable_hook_title: Optional[bool] = None
    hook_title_style: Optional[str] = None
    subtitle_position: Optional[str] = None
    caption_highlight: Optional[str] = None
    caption_font: Optional[str] = None
    target_clip_count: Optional[int] = None

class RegenerateTitleRequest(BaseModel):
    project_name: str
    clip_number: int

class UpdateTitleRequest(BaseModel):
    project_name: str
    clip_number: int
    hook_title: str

@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/config")
async def get_config():
    return config.load_config()

@app.post("/api/config")
async def update_config(req: ConfigUpdateRequest):
    current = config.load_config()
    if req.gemini_api_key is not None:
        current["gemini_api_key"] = req.gemini_api_key
    if req.crop_mode is not None:
        current["crop_mode"] = req.crop_mode
    if req.bg_blur_style is not None:
        current["bg_blur_style"] = req.bg_blur_style
    if req.enable_hook_title is not None:
        current["enable_hook_title"] = req.enable_hook_title
    if req.hook_title_style is not None:
        current["hook_title_style"] = req.hook_title_style
    if req.subtitle_position is not None:
        current["subtitle_position"] = req.subtitle_position
    if req.caption_highlight is not None:
        current["caption_highlight"] = req.caption_highlight
    if req.caption_font is not None:
        current["caption_font"] = req.caption_font
    if req.target_clip_count is not None:
        current["target_clip_count"] = req.target_clip_count
    config.save_config(current)
    return {"status": "ok", "config": current}

@app.get("/api/projects")
async def list_projects():
    pm = ProjectManager()
    return pm.list_projects()

@app.get("/api/projects/{project_name}")
async def get_project(project_name: str):
    pm = ProjectManager()
    proj = pm.get_project(project_name)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    info = proj.load_original_info()
    analysis = proj.load_clip_analysis()
    return {
        "folder_name": project_name,
        "video_info": info,
        "clips": analysis,
        "report_url": f"/output/{project_name}/report.html"
    }

@app.post("/api/clips/regenerate-title")
async def regenerate_clip_title(req: RegenerateTitleRequest):
    pm = ProjectManager()
    proj = pm.get_project(req.project_name)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    analysis = proj.load_clip_analysis()
    clip = next((c for c in analysis if c.get("clip_number") == req.clip_number), None)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    info = proj.load_original_info()
    existing_titles = {c.get("hook_title") for c in analysis if c.get("hook_title")}
    ai = AIAnalyzer()
    new_title = ai.regenerate_hook_title(clip, video_title=info.get("title", ""), video_info=info, used_titles=existing_titles)
    return {"status": "ok", "clip_number": req.clip_number, "hook_title": new_title}

@app.post("/api/clips/update-title")
async def update_clip_title(req: UpdateTitleRequest):
    pm = ProjectManager()
    proj = pm.get_project(req.project_name)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    analysis = proj.load_clip_analysis()
    clip = next((c for c in analysis if c.get("clip_number") == req.clip_number), None)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    clean_title = req.hook_title.strip()
    clip["hook_title"] = clean_title
    proj.save_clip_analysis(analysis)

    # Re-generate ASS subtitle with new Hook Title
    sub_gen = SubtitleGenerator()
    ass_path = proj.get_ass_caption_path(req.clip_number)
    clip_transcript = clip.get("transcript_slice", [])
    dur = float(clip.get("duration", 45.0))
    visual_info = clip.get("visual_info", {})
    cfg = config.load_config()

    sub_gen.generate_ass(
        clip_transcript=clip_transcript,
        output_ass_path=ass_path,
        face_y_ratio=visual_info.get("face_y_ratio", 0.4),
        has_bottom_facecam=visual_info.get("has_bottom_facecam", False),
        hook_title=clean_title if cfg.get("enable_hook_title", True) else None,
        clip_duration=dur
    )

    # Re-render clip using source video in temp_dir
    renderer = Renderer()
    source_video = proj.temp_dir / "source_video.mp4"
    if not source_video.exists():
        for f in proj.temp_dir.glob("source_video.*"):
            source_video = f
            break

    if not source_video.exists():
        raise HTTPException(status_code=400, detail="Source video not available in project temp folder for re-render.")

    clip_output = proj.get_clip_path(req.clip_number)
    thumb_output = proj.get_thumbnail_path(req.clip_number)

    renderer.render_clip(
        source_video_path=source_video,
        start_time=float(clip["start_time"]),
        duration=dur,
        visual_info=visual_info,
        ass_sub_path=ass_path,
        output_clip_path=clip_output,
        thumbnail_path=thumb_output,
        bg_blur_style=cfg.get("bg_blur_style", "cinematic")
    )

    # Also update HTML report
    try:
        rg = ReportGenerator()
        rg.generate_html_report(proj.load_original_info(), analysis, proj.report_path)
    except Exception as e:
        print(f"[UpdateTitle] Report generation notice: {e}")

    timestamp_str = str(int(time.time()))
    return {
        "status": "ok",
        "clip_number": req.clip_number,
        "hook_title": clean_title,
        "video_url": f"/output/{req.project_name}/clips/clip_{req.clip_number:02d}.mp4?v={timestamp_str}",
        "thumb_url": f"/output/{req.project_name}/thumbnails/clip_{req.clip_number:02d}.jpg?v={timestamp_str}"
    }

def run_pipeline_worker(job_id: str, url: str):
    """Worker running in a background thread."""
    def progress_callback(pct: float, msg: str, extra: Optional[Dict[str, Any]] = None):
        job = JOBS.get(job_id)
        if job:
            job["progress"] = pct
            job["message"] = msg
            job["logs"].append(f"[{pct:05.1f}%] {msg}")
            if extra:
                job["result"] = extra

            # Push event to SSE listeners
            queues = ACTIVE_JOB_QUEUES.get(job_id, [])
            payload = json.dumps({
                "job_id": job_id,
                "progress": pct,
                "message": msg,
                "status": job["status"],
                "result": job.get("result")
            })
            for q in queues:
                try:
                    q.append(payload)
                except Exception:
                    pass

    try:
        pipeline = ClippingPipeline()
        result = pipeline.process_video(url, progress_callback=progress_callback)
        JOBS[job_id]["status"] = "completed"
        JOBS[job_id]["progress"] = 100.0
        JOBS[job_id]["message"] = "Processing complete!"
        JOBS[job_id]["result"] = result
        progress_callback(100.0, "All clips successfully generated and verified!", result)
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"[Worker Error] {e}\n{tb}")
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["message"] = str(e)
        JOBS[job_id]["error"] = str(e)
        progress_callback(JOBS[job_id].get("progress", 0), f"Error: {str(e)}")

@app.post("/api/start-job")
async def start_job(req: StartJobRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="YouTube URL is required")

    job_id = str(uuid.uuid4())
    JOBS[job_id] = {
        "job_id": job_id,
        "url": url,
        "status": "running",
        "progress": 0.0,
        "message": "Initializing job...",
        "logs": [],
        "created_at": time.time(),
        "result": None,
        "error": None
    }
    ACTIVE_JOB_QUEUES[job_id] = []

    # Run pipeline in background daemon thread
    thread = threading.Thread(target=run_pipeline_worker, args=(job_id, url), daemon=True)
    thread.start()

    return {"job_id": job_id, "status": "started"}

@app.get("/api/job-status/{job_id}")
async def get_job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/api/stream/{job_id}")
async def stream_job_updates(job_id: str):
    """Server-Sent Events endpoint for real-time progress updates."""
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        q = []
        if job_id in ACTIVE_JOB_QUEUES:
            ACTIVE_JOB_QUEUES[job_id].append(q)

        # Send initial state
        job = JOBS.get(job_id, {})
        initial_payload = json.dumps({
            "job_id": job_id,
            "progress": job.get("progress", 0.0),
            "message": job.get("message", ""),
            "status": job.get("status", "running"),
            "result": job.get("result")
        })
        yield f"data: {initial_payload}\n\n"

        while True:
            # Drain queue
            while len(q) > 0:
                item = q.pop(0)
                yield f"data: {item}\n\n"

            job = JOBS.get(job_id)
            if not job or job.get("status") in ["completed", "failed"]:
                # Send final event
                final_payload = json.dumps({
                    "job_id": job_id,
                    "progress": job.get("progress", 100.0) if job else 100.0,
                    "message": job.get("message", "") if job else "Done",
                    "status": job.get("status", "completed") if job else "completed",
                    "result": job.get("result") if job else None,
                    "error": job.get("error") if job else None
                })
                yield f"data: {final_payload}\n\n"
                break

            await asyncio.sleep(0.5)

        if job_id in ACTIVE_JOB_QUEUES and q in ACTIVE_JOB_QUEUES[job_id]:
            ACTIVE_JOB_QUEUES[job_id].remove(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    import webbrowser
    import socket

    def find_free_port(start_port=8000, max_attempts=50):
        for p in range(start_port, start_port + max_attempts):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(("127.0.0.1", p))
                    return p
                except OSError:
                    continue
        return start_port

    port = find_free_port(8000)

    def open_browser():
        time.sleep(1.5)
        webbrowser.open(f"http://127.0.0.1:{port}")

    threading.Thread(target=open_browser, daemon=True).start()
    print("=" * 70)
    print("  ⚡ AI Clipper for Instagram & Youtube Shorts (AIYT Clipper)")
    print("  \"Autonomous AI Video Clipper for Shorts, Reels & TikTok\"")
    print("  Developed by Mohsin Khawaja (@csib.mohsin)")
    print(f"  Web Dashboard: http://127.0.0.1:{port}")
    print("  Output Directory: " + str(OUTPUT_DIR))
    if port != 8000:
        print(f"  [NOTE] Port 8000 was in use. Auto-switched to port {port}.")
    print("=" * 70)
    uvicorn.run("app:app", host="127.0.0.1", port=port, reload=False)

