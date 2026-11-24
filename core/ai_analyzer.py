import os
import re
import json
from typing import List, Dict, Any, Optional, Set
import config
from core.hinglish_transliteration import to_hinglish
from core.hook_title_generator import HookTitleGenerator

class AIAnalyzer:
    """Analyzes timestamped transcript and metadata to find viral, high-value clip candidates."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        cfg = config.load_config()
        self.api_key = api_key or cfg.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY", "")
        self.model_name = model or cfg.get("gemini_model", "gemini-3.8-flash")

    def analyze_and_select_clips(
        self,
        video_info: Dict[str, Any],
        transcript_segments: List[Dict[str, Any]],
        target_count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Runs AI analysis to select top clips.
        Tries Gemini 3.8 Flash if API key is present; otherwise uses autonomous local NLP engine.
        """
        if not transcript_segments:
            return []

        # If Gemini API key is provided, attempt Gemini analysis
        if self.api_key:
            try:
                clips = self._analyze_with_gemini(video_info, transcript_segments, target_count)
                if clips and len(clips) > 0:
                    return clips
            except Exception as e:
                print(f"[AIAnalyzer] Gemini API analysis failed ({e}). Falling back to local NLP engine.")

        # Local NLP heuristic engine fallback
        return self._analyze_with_local_engine(video_info, transcript_segments, target_count)

    def _analyze_with_gemini(
        self,
        video_info: Dict[str, Any],
        transcript_segments: List[Dict[str, Any]],
        target_count: int = 5
    ) -> List[Dict[str, Any]]:
        """Uses Gemini 3.8 Flash to analyze transcript and select top engaging moments."""
        from google import genai

        client = genai.Client(api_key=self.api_key)

        # Build concise timestamped transcript summary
        lines = []
        for s in transcript_segments:
            lines.append(f"[{s['start']:.1f}s - {s['end']:.1f}s] {s['text']}")
        transcript_text = "\n".join(lines)
        if len(transcript_text) > 40000:
            transcript_text = transcript_text[:40000] + "\n...[truncated for length]"

        prompt = f"""
You are an expert viral video editor and content strategist specializing in YouTube Shorts, Instagram Reels, and TikTok clips.

Analyze the following video transcript and identify the top {target_count} most engaging, high-value, and self-contained moments suitable for 9:16 vertical shorts.

VIDEO DETAILS:
Title: {video_info.get('title', 'Unknown')}
Uploader: {video_info.get('uploader', 'Unknown')}
Duration: {video_info.get('duration', 0)} seconds

TRANSCRIPT WITH EXACT TIMESTAMPS:
{transcript_text}

SELECTION CRITERIA:
1. Duration: Target 30-60 seconds (allowed 15-90 seconds if justified).
2. Content: Look for strong opening hooks, surprising facts, important explanations, real-life stories, emotional/motivational moments, controversial opinions, or unexpected punchlines.
3. Completeness: Clip must make complete sense on its own. Never cut off in the middle of a sentence or key thought.
4. Hook & Ending: Must open with an attention-grabbing hook and conclude with a punchline, conclusion, or curiosity gap.
5. Accuracy: Use EXACT timestamps matching the transcript lines above. Do not invent timestamps.
6. Non-overlapping: Clips must not overlap.
7. CRITICAL HOOK TITLE UNIQUENESS & CONTENT UNDERSTANDING:
   - "hook_title": Must be an engaging, curiosity-driven viral headline (3 to 6 words MAX, in ALL CAPS with 1 fitting emoji).
   - EVERY SINGLE CLIP MUST HAVE A COMPLETELY DIFFERENT, UNIQUE HOOK TITLE reflecting what happens in THAT EXACT CLIP's timestamp range.
   - NEVER use the same hook title twice across clips in the video.
   - DO NOT use generic phrases like "KEY INSIGHT" or "MUST WATCH".
   - Support natural Roman Hinglish or English (ZERO Devanagari Hindi).

Return ONLY a JSON array with exactly {target_count} objects in this format:
[
  {{
    "clip_number": 1,
    "title": "Punchy Catchy Clip Title",
    "hook_title": "SHORT UNIQUE VIRAL HOOK TITLE (3-6 WORDS MAX, ALL CAPS + 1 EMOJI)",
    "start_time": 45.2,
    "end_time": 92.5,
    "duration": 47.3,
    "topic": "Brief topic summary",
    "why_selected": "Detailed explanation of why this moment is valuable and engaging",
    "hook_description": "Description of the opening hook",
    "hook_score": 9.5,
    "interest_score": 9.0,
    "value_score": 8.8,
    "emotional_score": 8.5,
    "context_score": 9.2,
    "ending_score": 9.0,
    "engagement_score": 90.0,
    "social_caption": "Engaging social media post copy with call to action",
    "hashtags": ["#shorts", "#viral", "#reels", "#fyp", "#tips"],
    "recommended_layout": "smart_crop"
  }}
]
"""
        response = client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )

        response_text = response.text.strip()
        # Extract json array from response
        match = re.search(r'\[\s*\{.*\}\s*\]', response_text, re.DOTALL)
        if match:
            json_str = match.group(0)
            data = json.loads(json_str)
            # Normalize fields with uniqueness enforcement
            return self._normalize_clips(data, video_info.get("duration", 0), video_info=video_info)

        return []

    def _analyze_with_local_engine(
        self,
        video_info: Dict[str, Any],
        transcript_segments: List[Dict[str, Any]],
        target_count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Deep NLP & Heuristic Engine for viral moment detection.
        Scans lexical patterns, hook indicators, semantic density, and natural sentence boundaries.
        """
        total_duration = video_info.get("duration", 0) or (transcript_segments[-1]["end"] if transcript_segments else 0)
        if not transcript_segments:
            return []

        # High-impact hook phrases and regex patterns
        hook_patterns = [
            r"\b(why|how|what if|have you ever|did you know)\b",
            r"\b(the secret|the truth|nobody tells you|the biggest mistake)\b",
            r"\b(never|always|stop doing|start doing|rule number)\b",
            r"\b(shocking|crazy|insane|unbelievable|magic|huge)\b",
            r"\b(first thing|most important|lesson|remember this)\b",
            r"\b(\d+ (ways|tips|steps|reasons|mistakes|things|secrets))\b",
            r"\b(when I started|in my experience|story time|one day)\b",
            r"\b(actually|literally|in reality|here is the thing)\b",
        ]

        # Conclusion patterns
        conclusion_patterns = [
            r"\b(and that is why|so remember|the point is|in conclusion)\b",
            r"\b(that is how|which means|final thought|takeaway)\b",
            r"\b(let me know|what do you think|subscribe|share this)\b",
            r"[\.!?]$"
        ]

        # Generate candidate windows between 25 and 70 seconds
        candidates = []
        n_segs = len(transcript_segments)

        for i in range(n_segs):
            start_seg = transcript_segments[i]
            start_time = start_seg["start"]
            
            # Skip first 10 seconds of long video if it's just intro music/greetings
            if total_duration > 180 and start_time < 12.0 and re.search(r"\b(welcome back|hey guys|intro|like and subscribe)\b", start_seg["text"], re.I):
                continue

            # Evaluate hook strength of opening segment
            opening_text = start_seg["text"].lower()
            hook_matches = sum(1 for p in hook_patterns if re.search(p, opening_text, re.I))
            
            # Additional hook signals: questions, brevity, exclamations
            is_question = "?" in start_seg["text"]
            has_number = bool(re.search(r"\d+", start_seg["text"]))
            
            base_hook_score = 6.0 + (hook_matches * 1.2) + (1.0 if is_question else 0.0) + (0.8 if has_number else 0.0)
            hook_score = min(round(base_hook_score, 1), 9.9)

            # Find matching ending segment within 30 to 65 seconds
            cumulative_text = [start_seg["text"]]
            for j in range(i + 1, min(i + 35, n_segs)):
                end_seg = transcript_segments[j]
                dur = end_seg["end"] - start_time
                cumulative_text.append(end_seg["text"])

                if 28.0 <= dur <= 65.0:
                    ending_text = end_seg["text"].lower()
                    has_conclusion = any(re.search(p, ending_text, re.I) for p in conclusion_patterns)
                    ends_with_period = end_seg["text"].strip().endswith((".", "!", "?"))

                    # Compute dimension scores
                    interest_score = min(round(6.5 + (len(" ".join(cumulative_text).split()) / (dur * 3.5)) * 2.0, 1), 9.8)
                    value_score = min(round(7.0 + (1.5 if has_number else 0.5) + (hook_matches * 0.4), 1), 9.9)
                    emotional_score = min(round(6.5 + (1.5 if "!" in " ".join(cumulative_text) else 0.5), 1), 9.6)
                    context_score = 9.0 if (ends_with_period or has_conclusion) else 7.5
                    ending_score = min(round(7.0 + (1.5 if has_conclusion else 0.5) + (1.0 if ends_with_period else 0.0), 1), 9.8)

                    # Overall engagement score (weighted formula)
                    overall_score = round(
                        (hook_score * 0.28) +
                        (interest_score * 0.22) +
                        (value_score * 0.18) +
                        (emotional_score * 0.12) +
                        (context_score * 0.10) +
                        (ending_score * 0.10)
                    ) * 10.0 / 10.0
                    overall_score = min(max(round(overall_score * 10, 1), 60.0), 98.0)

                    clip_full_text = " ".join(cumulative_text)
                    
                    # Synthesize engaging title
                    first_sentence = re.split(r'[\.\?!]', clip_full_text)[0].strip()
                    title_candidate = first_sentence if (5 < len(first_sentence) < 55) else f"Key Insight #{i+1}"
                    # Capitalize words
                    title = " ".join(w.capitalize() for w in title_candidate.split()[:7])

                    # Synthesize ultra-catchy top Hook Title
                    hook_title = self.generate_smart_hook_title(
                        text=clip_full_text,
                        hook_text=start_seg["text"],
                        fallback_title=title,
                        video_title=video_info.get("title", "")
                    )

                    candidates.append({
                        "start_time": round(start_time, 2),
                        "end_time": round(end_seg["end"], 2),
                        "duration": round(dur, 2),
                        "title": title,
                        "hook_title": hook_title,
                        "text": clip_full_text,
                        "hook_text": start_seg["text"],
                        "hook_score": hook_score,
                        "interest_score": interest_score,
                        "value_score": value_score,
                        "emotional_score": emotional_score,
                        "context_score": context_score,
                        "ending_score": ending_score,
                        "engagement_score": overall_score,
                        "why_selected": f"Identified strong opening hook with high speech information density and clean conversational resolution.",
                        "hook_description": f"Starts immediately with: '{start_seg['text'][:60]}...'",
                        "recommended_layout": "auto"
                    })

        # Sort candidates by overall engagement score descending
        candidates.sort(key=lambda c: c["engagement_score"], reverse=True)

        # Select non-overlapping top clips and assign unique, content-tailored hook titles
        selected = []
        used_hook_titles: Set[str] = set()
        domain = HookTitleGenerator.detect_video_domain(video_info)

        for cand in candidates:
            # Check overlap with already selected
            overlap = False
            for s in selected:
                # If overlap duration > 5 seconds
                start_max = max(cand["start_time"], s["start_time"])
                end_min = min(cand["end_time"], s["end_time"])
                if end_min - start_max > 5.0:
                    overlap = True
                    break
            if not overlap:
                cand["clip_number"] = len(selected) + 1
                # Assign 100% unique, domain-aware, dialogue-specific hook title
                cand["hook_title"] = HookTitleGenerator.generate_hook_title(
                    clip=cand,
                    video_info=video_info,
                    used_titles=used_hook_titles,
                    domain=domain
                )
                # Generate social caption & hashtags
                cand["social_caption"] = f"{cand['title']} 🔥 Watch until the end for the key takeaway! Let me know your thoughts in the comments."
                cand["hashtags"] = ["#Shorts", "#Reels", "#ViralShorts", "#ContentCreation", "#LifeHacks", "#Insight"]
                selected.append(cand)
                if len(selected) >= target_count:
                    break

        # Fallback if no candidate passed filters (e.g. very short video)
        if not selected and transcript_segments:
            s_start = transcript_segments[0]["start"]
            s_end = min(transcript_segments[-1]["end"], s_start + 45.0)
            fb_clip = {
                "clip_number": 1,
                "title": video_info.get("title", "Highlight Moment")[:40],
                "start_time": round(s_start, 2),
                "end_time": round(s_end, 2),
                "duration": round(s_end - s_start, 2),
                "topic": "Key highlight",
                "why_selected": "Best focal moment from source video.",
                "hook_description": "Opening statement.",
                "hook_score": 8.0,
                "interest_score": 8.0,
                "value_score": 8.0,
                "emotional_score": 7.5,
                "context_score": 8.5,
                "ending_score": 8.0,
                "engagement_score": 82.0,
                "social_caption": f"Must watch highlight from {video_info.get('title', 'this video')}!",
                "hashtags": ["#shorts", "#reels", "#fyp", "#viral"],
                "recommended_layout": "auto"
            }
            fb_clip["hook_title"] = HookTitleGenerator.generate_hook_title(
                clip=fb_clip,
                video_info=video_info,
                used_titles=used_hook_titles,
                domain=domain
            )
            selected.append(fb_clip)

        return selected

    def _normalize_clips(
        self,
        raw_clips: List[Dict[str, Any]],
        max_video_duration: float,
        video_info: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Validates and standardizes clip objects from Gemini, strictly guaranteeing unique, non-repeating hook titles."""
        normalized = []
        used_hook_titles: Set[str] = set()
        info = video_info or {}
        domain = HookTitleGenerator.detect_video_domain(info)

        for idx, item in enumerate(raw_clips):
            start = float(item.get("start_time", 0.0))
            end = float(item.get("end_time", start + 45.0))
            dur = round(end - start, 2)
            if dur <= 0:
                continue
            if max_video_duration > 0 and end > max_video_duration:
                end = max_video_duration
                dur = round(end - start, 2)

            title = item.get("title", f"Clip #{idx+1}")
            raw_hook = item.get("hook_title", "").strip().upper()

            # Verify uniqueness across all clips in this video
            if raw_hook and raw_hook not in used_hook_titles and len(raw_hook.split()) <= 7:
                hook_title = raw_hook
                used_hook_titles.add(hook_title)
            else:
                hook_title = HookTitleGenerator.generate_hook_title(
                    clip=item,
                    video_info=info,
                    used_titles=used_hook_titles,
                    domain=domain
                )

            normalized.append({
                "clip_number": idx + 1,
                "title": title,
                "hook_title": hook_title,
                "start_time": round(start, 2),
                "end_time": round(end, 2),
                "duration": dur,
                "topic": item.get("topic", item.get("title", "")),
                "why_selected": item.get("why_selected", "Selected by AI for high engagement potential."),
                "hook_description": item.get("hook_description", "Strong opening hook."),
                "hook_score": float(item.get("hook_score", 8.5)),
                "interest_score": float(item.get("interest_score", 8.5)),
                "value_score": float(item.get("value_score", 8.5)),
                "emotional_score": float(item.get("emotional_score", 8.0)),
                "context_score": float(item.get("context_score", 8.5)),
                "ending_score": float(item.get("ending_score", 8.5)),
                "engagement_score": float(item.get("engagement_score", 85.0)),
                "social_caption": item.get("social_caption", f"{title} 🔥"),
                "hashtags": item.get("hashtags", ["#shorts", "#reels", "#viral"]),
                "recommended_layout": item.get("recommended_layout", "auto")
            })
        return normalized

    def generate_smart_hook_title(
        self,
        text: str,
        hook_text: str = "",
        fallback_title: str = "",
        video_title: str = "",
        clip: Optional[Dict[str, Any]] = None,
        video_info: Optional[Dict[str, Any]] = None,
        used_titles: Optional[Set[str]] = None
    ) -> str:
        """Synthesizes a short, curiosity-driven viral Hook Title using HookTitleGenerator."""
        dummy = clip or {"text": text, "hook_text": hook_text, "title": fallback_title}
        info = video_info or {"title": video_title}
        return HookTitleGenerator.generate_hook_title(dummy, info, used_titles=used_titles)

    def regenerate_hook_title(
        self,
        clip_data: Dict[str, Any],
        video_title: str = "",
        video_info: Optional[Dict[str, Any]] = None,
        used_titles: Optional[Set[str]] = None
    ) -> str:
        """Regenerates an alternative viral hook title ensuring no collision with other clips."""
        info = video_info or {"title": video_title}
        return HookTitleGenerator.regenerate_title(clip_data, info, used_titles=used_titles)

