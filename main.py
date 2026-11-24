import os
import sys
import argparse
from pathlib import Path

# Ensure package directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import config
from core.pipeline import ClippingPipeline

def main():
    parser = argparse.ArgumentParser(
        description="AI Clipper for Instagram & Youtube Shorts (AIYT Clipper) - Convert long videos into viral 9:16 vertical shorts."
    )
    parser.add_argument("url", nargs="?", help="YouTube video URL to analyze and clip")
    parser.add_argument("--clips", type=int, default=None, help="Number of clips to generate (default: 5)")
    parser.add_argument("--mode", choices=["auto", "smart_crop", "blurred_bg", "split_screen", "center_zoom"], default=None, help="Cropping mode")
    parser.add_argument("--key", type=str, default=None, help="Google Gemini API key")

    args = parser.parse_args()

    # Load and update config if flags provided
    cfg = config.load_config()
    if args.clips:
        cfg["target_clip_count"] = args.clips
    if args.mode:
        cfg["crop_mode"] = args.mode
    if args.key:
        cfg["gemini_api_key"] = args.key
    config.save_config(cfg)

    url = args.url
    if not url:
        print("\n" + "="*70)
        print("  ⚡ AI Clipper for Instagram & Youtube Shorts (AIYT Clipper)")
        print("  Developed by Mohsin Khawaja (@csib.mohsin)")
        print("="*70)
        url = input("\nEnter YouTube Video URL: ").strip()

    if not url:
        print("Error: No YouTube URL provided.")
        sys.exit(1)

    print(f"\nProcessing YouTube URL: {url}")
    print("-" * 70)

    pipeline = ClippingPipeline()
    try:
        result = pipeline.process_video(url)
        print("\n" + "="*70)
        print("  🎉 Clipping Complete!")
        print("="*70)
        print(f"Project Folder: {result['project_dir']}")
        print(f"HTML Report:    {result['report_path']}")
        print(f"Total Clips:    {len(result['clips'])}")
        print("Clips:")
        for c in result["clips"]:
            dur = c["duration"]
            score = c.get("engagement_score", 0)
            print(f"  • Clip #{c['clip_number']:02d}: {c['title']} ({dur:.1f}s) - Score: {score}/100")
        print("="*70)
    except Exception as e:
        print(f"\n❌ Pipeline failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

