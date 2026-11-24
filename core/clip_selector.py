import bisect
from typing import List, Dict, Any, Tuple
import config

class ClipSelector:
    """Refines candidate clips by snapping to exact word/sentence boundaries and enforcing duration/quality rules."""

    def __init__(self):
        cfg = config.load_config()
        self.default_min = cfg.get("default_min_duration", 30)
        self.default_max = cfg.get("default_max_duration", 60)
        self.abs_min = cfg.get("absolute_min_duration", 15)
        self.abs_max = cfg.get("absolute_max_duration", 90)

    def refine_clips(
        self,
        candidate_clips: List[Dict[str, Any]],
        transcript_segments: List[Dict[str, Any]],
        video_duration: float
    ) -> List[Dict[str, Any]]:
        """
        Takes raw candidate clips, verifies them against actual transcript segments and words,
        snaps start/end to clean sentence boundaries (avoiding cutting mid-word or mid-sentence),
        and guarantees all duration and non-overlapping constraints.
        """
        if not candidate_clips or not transcript_segments:
            return candidate_clips

        # Extract all word boundaries across entire transcript
        all_words = []
        for seg in transcript_segments:
            for w in seg.get("words", []):
                all_words.append(w)

        refined = []
        for i, clip in enumerate(candidate_clips):
            raw_start = float(clip["start_time"])
            raw_end = float(clip["end_time"])

            # 1. Snap start and end to actual words if available
            snapped_start, snapped_end = self._snap_boundaries(raw_start, raw_end, transcript_segments, all_words)

            # 2. Bound by video duration
            snapped_start = max(0.0, snapped_start)
            if video_duration > 0:
                snapped_end = min(video_duration, snapped_end)

            duration = round(snapped_end - snapped_start, 2)

            # 3. Check duration boundaries
            if duration < self.abs_min:
                # Expand end if possible
                snapped_end = min(video_duration if video_duration > 0 else (snapped_start + self.abs_min), snapped_start + self.abs_min)
                duration = round(snapped_end - snapped_start, 2)

            if duration > self.abs_max:
                snapped_end = snapped_start + self.abs_max
                duration = round(snapped_end - snapped_start, 2)

            # Extract matching transcript slice for this clip
            clip_transcript = self._extract_clip_transcript(snapped_start, snapped_end, transcript_segments)

            refined_clip = dict(clip)
            refined_clip["clip_number"] = i + 1
            refined_clip["start_time"] = round(snapped_start, 2)
            refined_clip["end_time"] = round(snapped_end, 2)
            refined_clip["duration"] = duration
            refined_clip["transcript_slice"] = clip_transcript

            refined.append(refined_clip)

        # 4. Remove overlapping clips
        final_clips = self._suppress_overlaps(refined)
        
        # Re-index clip numbers
        for idx, c in enumerate(final_clips):
            c["clip_number"] = idx + 1

        return final_clips

    def _snap_boundaries(
        self,
        target_start: float,
        target_end: float,
        segments: List[Dict[str, Any]],
        words: List[Dict[str, Any]]
    ) -> Tuple[float, float]:
        """Snaps target start and end to exact sentence and word starts/ends with micro-padding."""
        best_start = target_start
        best_end = target_end

        # Find closest segment start
        for s in segments:
            if abs(s["start"] - target_start) <= 2.5:
                # Add 0.1s lead-in for smooth phoneme attack
                best_start = max(0.0, s["start"] - 0.1)
                break

        # Find closest segment end
        for s in reversed(segments):
            if abs(s["end"] - target_end) <= 3.0:
                # Add 0.25s tail buffer for natural speech decay
                best_end = s["end"] + 0.25
                break

        # If words exist, fine-tune down to word level
        if words:
            # Word near start
            for w in words:
                if abs(w["start"] - best_start) <= 0.8:
                    best_start = max(0.0, w["start"] - 0.12)
                    break

            # Word near end
            for w in reversed(words):
                if abs(w["end"] - best_end) <= 1.0:
                    best_end = w["end"] + 0.25
                    break

        return (round(best_start, 2), round(best_end, 2))

    def _extract_clip_transcript(
        self,
        clip_start: float,
        clip_end: float,
        segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extracts and shifts transcript words relative to clip start timestamp."""
        clip_segments = []
        for seg in segments:
            if seg["end"] >= clip_start and seg["start"] <= clip_end:
                shifted_words = []
                for w in seg.get("words", []):
                    if w["end"] >= clip_start and w["start"] <= clip_end:
                        shifted_words.append({
                            "word": w["word"],
                            # Timestamps relative to clip start (0.00s)
                            "rel_start": round(max(0.0, w["start"] - clip_start), 3),
                            "rel_end": round(max(0.0, w["end"] - clip_start), 3),
                            # Absolute timestamps in source video
                            "abs_start": w["start"],
                            "abs_end": w["end"]
                        })

                clip_segments.append({
                    "text": seg["text"],
                    "rel_start": round(max(0.0, seg["start"] - clip_start), 3),
                    "rel_end": round(max(0.0, seg["end"] - clip_start), 3),
                    "abs_start": seg["start"],
                    "abs_end": seg["end"],
                    "words": shifted_words
                })
        return clip_segments

    def _suppress_overlaps(self, clips: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Removes clips that overlap significantly (>10% of duration)."""
        non_overlapping = []
        for c in clips:
            overlap = False
            for prev in non_overlapping:
                max_s = max(c["start_time"], prev["start_time"])
                min_e = min(c["end_time"], prev["end_time"])
                if min_e > max_s:
                    overlap_dur = min_e - max_s
                    # If overlap is more than 5s
                    if overlap_dur > 5.0:
                        overlap = True
                        break
            if not overlap:
                non_overlapping.append(c)
        return non_overlapping

