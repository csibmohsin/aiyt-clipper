import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
import config

class Transcriber:
    """Extracts timestamped speech transcript with word-level timing."""

    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self._whisper_model = None

    def _get_whisper_model(self):
        if self._whisper_model is None:
            from faster_whisper import WhisperModel
            # Load on CPU with int8 quantization for high speed and low memory footprint
            self._whisper_model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
        return self._whisper_model

    def get_transcript(
        self,
        video_id: str,
        audio_path: Optional[Path] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Attempts to fetch YouTube official/auto transcript first for instantaneous speed.
        Falls back to faster-whisper on audio for word-level timestamps or missing captions.
        """
        transcript_data = []

        # 1. Try YouTube official or auto-generated transcript
        if progress_callback:
            progress_callback(10.0, "Checking YouTube subtitles / captions...")

        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            api = YouTubeTranscriptApi()
            transcript_list = api.list(video_id)
            
            # Find matching transcript (prefer manual en/hi, then generated en/hi)
            target_t = None
            try:
                target_t = transcript_list.find_manually_created_transcript(['en', 'en-US', 'en-GB', 'hi'])
            except Exception:
                try:
                    target_t = transcript_list.find_generated_transcript(['en', 'en-US', 'en-GB', 'hi'])
                except Exception:
                    # Take first available
                    for t in transcript_list:
                        target_t = t
                        break

            if target_t:
                raw_segments = target_t.fetch().to_raw_data()
                transcript_data = self._format_youtube_transcript(raw_segments)
                if progress_callback:
                    progress_callback(50.0, f"Found YouTube transcript ({len(transcript_data)} segments). Refining word timings...")
                return transcript_data
        except Exception as e:
            if progress_callback:
                progress_callback(20.0, f"YouTube transcript not available ({e}). Using Whisper model...")

        # 2. Whisper fallback (Audio transcription with word-level timestamps)
        if audio_path and audio_path.exists():
            transcript_data = self.transcribe_audio_whisper(audio_path, progress_callback)
            return transcript_data

        return transcript_data

    def _format_youtube_transcript(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Converts raw YouTube transcript segments into standardized segment/word structure."""
        formatted = []
        for i, item in enumerate(raw_data):
            text = item.get("text", "").replace("\n", " ").strip()
            start = float(item.get("start", 0.0))
            duration = float(item.get("duration", 0.0))
            end = round(start + duration, 3)

            # Estimate word-level timestamps proportionally across segment
            words_raw = text.split()
            words = []
            if words_raw:
                time_per_word = duration / len(words_raw) if len(words_raw) > 0 else 0.3
                for w_idx, w in enumerate(words_raw):
                    w_start = round(start + (w_idx * time_per_word), 3)
                    w_end = round(w_start + time_per_word, 3)
                    words.append({
                        "word": w,
                        "start": w_start,
                        "end": w_end,
                        "probability": 0.95
                    })

            formatted.append({
                "id": i,
                "start": start,
                "end": end,
                "text": text,
                "words": words
            })
        return formatted

    def transcribe_audio_whisper(
        self,
        audio_path: Path,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> List[Dict[str, Any]]:
        """Transcribe audio with faster-whisper for accurate word-level timestamps and Hindi/English support."""
        if progress_callback:
            progress_callback(30.0, "Loading Whisper speech recognition engine...")

        model = self._get_whisper_model()

        if progress_callback:
            progress_callback(40.0, "Transcribing audio and aligning word timestamps...")

        segments, info = model.transcribe(
            str(audio_path),
            beam_size=5,
            word_timestamps=True,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        formatted = []
        seg_list = list(segments)
        total_segs = len(seg_list)

        for i, segment in enumerate(seg_list):
            words = []
            if segment.words:
                for w in segment.words:
                    words.append({
                        "word": w.word.strip(),
                        "start": round(w.start, 3),
                        "end": round(w.end, 3),
                        "probability": round(w.probability, 3)
                    })

            formatted.append({
                "id": i,
                "start": round(segment.start, 3),
                "end": round(segment.end, 3),
                "text": segment.text.strip(),
                "words": words
            })

            if progress_callback and total_segs > 0:
                pct = 40.0 + (i / total_segs) * 50.0
                progress_callback(pct, f"Transcribed segment {i+1}/{total_segs}")

        if progress_callback:
            progress_callback(95.0, f"Transcription completed ({len(formatted)} segments).")

        return formatted

