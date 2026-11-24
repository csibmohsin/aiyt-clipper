import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import config
from core.hinglish_transliteration import to_hinglish, contains_devanagari

class SubtitleGenerator:
    """Generates 100% Roman Hinglish .srt subtitles and viral kinetic word-highlighted .ass subtitles."""

    def __init__(self):
        cfg = config.load_config()
        self.style = cfg.get("caption_style", {})

    def generate_srt(self, clip_transcript: List[Dict[str, Any]], output_srt_path: Path):
        """Generates standard SRT caption file strictly in Roman Hinglish (zero Devanagari)."""
        output_srt_path.parent.mkdir(parents=True, exist_ok=True)
        lines = []
        entry_idx = 1

        for seg in clip_transcript:
            start_sec = seg["rel_start"]
            end_sec = seg["rel_end"]
            raw_text = seg["text"].strip()
            if not raw_text:
                continue

            # Convert to Roman Hinglish
            hinglish_text = to_hinglish(raw_text)
            if not hinglish_text:
                continue

            start_str = self._format_timestamp_srt(start_sec)
            end_str = self._format_timestamp_srt(end_sec)

            lines.append(f"{entry_idx}")
            lines.append(f"{start_str} --> {end_str}")
            lines.append(hinglish_text)
            lines.append("")
            entry_idx += 1

        with open(output_srt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def generate_ass(
        self,
        clip_transcript: List[Dict[str, Any]],
        output_ass_path: Path,
        face_y_ratio: float = 0.75,
        has_bottom_facecam: bool = True,
        hook_title: Optional[str] = None,
        clip_duration: Optional[float] = None
    ):
        """
        Generates modern viral ASS subtitles with word-by-word karaoke highlighting
        and an optional viral curiosity Hook Title at the TOP of the vertical video.
        100% Roman Hinglish with bold typography and safe margins.
        """
        output_ass_path.parent.mkdir(parents=True, exist_ok=True)

        cfg = config.load_config()
        font_name = cfg.get("caption_font") or "Arial Black"
        font_size = 50
        primary_color = "&H00FFFFFF"     # Crisp White

        # Highlight color from user preference
        h_choice = str(cfg.get("caption_highlight", "yellow")).lower()
        highlight_color = config.HIGHLIGHT_COLORS.get(h_choice, "&H0000FFFF")

        outline_color = "&H00000000"     # Thick Black Outline
        outline_w = 4.0
        shadow_d = 2.0

        # Safe vertical positioning from user preference for bottom captions
        pos_choice = str(cfg.get("subtitle_position", "bottom_safe")).lower()
        margin_v = config.SUBTITLE_POSITIONS.get(pos_choice, 260)

        enable_hook = cfg.get("enable_hook_title", True)
        title_style = cfg.get("hook_title_style", "bold_headline")

        header = f"""[Script Info]
Title: Viral Short Roman Hinglish Captions
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{primary_color},&H000000FF,{outline_color},&H80000000,-1,0,0,0,100,100,0,0,1,{outline_w},{shadow_d},2,40,40,{margin_v},1
Style: HookTitle,{font_name},58,{primary_color},&H000000FF,{outline_color},&H90000000,-1,0,0,0,100,100,0,0,1,5.0,2.5,8,60,60,150,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        events = []

        # 1. Add Top Persistent Hook Title if enabled
        if enable_hook and hook_title:
            clean_title = to_hinglish(hook_title).upper().strip()
            if clean_title:
                # Determine total duration for the title event
                total_dur = clip_duration or (clip_transcript[-1]["rel_end"] if clip_transcript else 60.0)
                end_str = self._format_timestamp_ass(total_dur)

                # Format title into 1 or 2 lines for optimal readability
                words = clean_title.split()
                if len(words) >= 5 or len(clean_title) > 24:
                    mid = len(words) // 2
                    line1 = " ".join(words[:mid])
                    line2 = " ".join(words[mid:])
                    if title_style == "solid_yellow":
                        formatted_title = f"{{\\c{highlight_color}&}}{line1}\\N{{\\c{highlight_color}&}}{line2}"
                    elif title_style == "solid_white":
                        formatted_title = f"{{\\c{primary_color}&}}{line1}\\N{{\\c{primary_color}&}}{line2}"
                    else:  # bold_headline (dual-tone)
                        formatted_title = f"{{\\c{primary_color}&}}{line1}\\N{{\\c{highlight_color}&}}{line2}"
                else:
                    if title_style == "solid_white":
                        formatted_title = f"{{\\c{primary_color}&}}{clean_title}"
                    else:
                        formatted_title = f"{{\\c{highlight_color}&}}{clean_title}"

                events.append(f"Dialogue: 2,0:00:00.00,{end_str},HookTitle,,0,0,0,,{formatted_title}")

        words_per_batch = 4  # Short punchy batches (max 1-2 lines)

        for seg in clip_transcript:
            words = seg.get("words", [])
            if not words:
                t_start = self._format_timestamp_ass(seg["rel_start"])
                t_end = self._format_timestamp_ass(seg["rel_end"])
                clean_text = to_hinglish(seg["text"]).upper().strip()
                if clean_text:
                    events.append(f"Dialogue: 0,{t_start},{t_end},Default,,0,0,0,,{clean_text}")
                continue

            # Process word-by-word with transliteration
            transliterated_words = []
            for w in words:
                w_text = to_hinglish(w["word"]).upper().strip()
                if w_text:
                    transliterated_words.append({
                        "word": w_text,
                        "rel_start": w["rel_start"],
                        "rel_end": w["rel_end"]
                    })

            if not transliterated_words:
                continue

            # Group into punchy batches of 3-4 words
            for i in range(0, len(transliterated_words), words_per_batch):
                batch = transliterated_words[i:i + words_per_batch]
                if not batch:
                    continue

                for w_idx, current_word in enumerate(batch):
                    w_start_str = self._format_timestamp_ass(current_word["rel_start"])
                    w_end_str = self._format_timestamp_ass(current_word["rel_end"])

                    styled_tokens = []
                    for other_idx, other_word in enumerate(batch):
                        word_txt = other_word["word"]
                        if other_idx == w_idx:
                            styled_tokens.append(f"{{\\c{highlight_color}&}}{word_txt}{{\\c{primary_color}&}}")
                        else:
                            styled_tokens.append(word_txt)

                    dialogue_text = " ".join(styled_tokens)
                    events.append(f"Dialogue: 0,{w_start_str},{w_end_str},Default,,0,0,0,,{dialogue_text}")

        full_ass = header + "\n".join(events) + "\n"
        with open(output_ass_path, "w", encoding="utf-8") as f:
            f.write(full_ass)

    @staticmethod
    def _format_timestamp_srt(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int(round((seconds - int(seconds)) * 1000))
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    @staticmethod
    def _format_timestamp_ass(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centis = int(round((seconds - int(seconds)) * 100))
        if centis >= 100:
            centis = 99
        return f"{hours:1d}:{minutes:02d}:{secs:02d}.{centis:02d}"
