import html
from pathlib import Path
from typing import Dict, Any, List

class ReportGenerator:
    """Generates a modern, professional White/Light SaaS HTML report (report.html) matching the main dashboard UI."""

    def generate_html_report(
        self,
        video_info: Dict[str, Any],
        clips_data: List[Dict[str, Any]],
        output_file: Path
    ) -> str:
        """Constructs modern SaaS HTML report with video players, metric scores, social copy, and download actions."""
        raw_title = video_info.get("title", "YouTube Clipping Project")
        title = html.escape(raw_title)
        uploader = html.escape(video_info.get("uploader", "Creator"))
        total_clips = len(clips_data)
        avg_score = round(sum(c.get("engagement_score", 0) for c in clips_data) / max(total_clips, 1), 1)

        clip_cards_html = []
        for c in clips_data:
            c_num = c.get("clip_number", 1)
            c_title = html.escape(c.get("title", f"Clip #{c_num}"))
            c_hook_title = html.escape(c.get("hook_title", c.get("title", "")))
            start_str = self._format_mmss(c.get("start_time", 0))
            end_str = self._format_mmss(c.get("end_time", 0))
            dur = c.get("duration", 0)
            score = c.get("engagement_score", 85)
            hook_desc = html.escape(c.get("hook_description", "Strong opening moment"))
            why_selected = html.escape(c.get("why_selected", "High engagement potential"))
            caption = html.escape(c.get("social_caption", ""))
            raw_hashtags = c.get("hashtags", [])
            hashtags = " ".join(html.escape(h) for h in raw_hashtags)
            layout = c.get("recommended_layout", "smart_crop").replace("_", " ").title()

            hook_s = c.get("hook_score", 8.5)
            interest_s = c.get("interest_score", 8.5)
            value_s = c.get("value_score", 8.5)
            emo_s = c.get("emotional_score", 8.0)
            context_s = c.get("context_score", 8.5)
            ending_s = c.get("ending_score", 8.5)

            video_filename = f"clips/clip_{c_num:02d}.mp4"
            thumb_filename = f"thumbnails/clip_{c_num:02d}.jpg"
            srt_filename = f"captions/clip_{c_num:02d}.srt"

            # Dynamic score badge colors
            if score >= 88:
                score_bg = "#ecfdf5"
                score_color = "#059669"
                score_border = "#a7f3d0"
            elif score >= 75:
                score_bg = "#fffbeb"
                score_color = "#d97706"
                score_border = "#fde68a"
            else:
                score_bg = "#eef2ff"
                score_color = "#4f46e5"
                score_border = "#c7d2fe"

            card = f"""
            <div class="clip-card" id="clip-{c_num}">
              <div class="clip-header">
                <div class="clip-title-group">
                  <span class="clip-badge">CLIP #{c_num:02d}</span>
                  <div class="clip-heading-wrap">
                    <h3 class="clip-title">{c_title}</h3>
                    <div class="hook-title-pill">
                      <span class="hook-icon">🔥</span>
                      <span class="hook-label">TOP HOOK:</span>
                      <span class="hook-text">{c_hook_title}</span>
                    </div>
                  </div>
                </div>
                <div class="score-badge" style="background: {score_bg}; color: {score_color}; border-color: {score_border};">
                  <span class="score-val">{score}</span>
                  <span class="score-lbl">VIRAL SCORE</span>
                </div>
              </div>

              <div class="clip-body">
                <div class="video-preview-wrapper">
                  <div class="video-frame">
                    <video controls poster="{thumb_filename}" preload="metadata">
                      <source src="{video_filename}" type="video/mp4">
                      Your browser does not support video playback.
                    </video>
                  </div>
                  <div class="video-meta-tags">
                    <span class="meta-tag">⏱ {dur:.1f}s</span>
                    <span class="meta-tag">📍 {start_str} - {end_str}</span>
                    <span class="meta-tag">🎨 {layout}</span>
                  </div>
                </div>

                <div class="clip-details">
                  <div class="detail-block">
                    <div class="detail-label"><span class="detail-icon">🎯</span> OPENING HOOK</div>
                    <div class="detail-content">{hook_desc}</div>
                  </div>

                  <div class="detail-block">
                    <div class="detail-label"><span class="detail-icon">💡</span> WHY AI SELECTED THIS</div>
                    <div class="detail-content">{why_selected}</div>
                  </div>

                  <div class="scores-section">
                    <div class="scores-header">6-DIMENSIONAL RETENTION MATRIX</div>
                    <div class="scores-grid">
                      <div class="score-item">
                        <span class="s-name">Hook</span>
                        <span class="s-val">{hook_s}</span>
                      </div>
                      <div class="score-item">
                        <span class="s-name">Interest</span>
                        <span class="s-val">{interest_s}</span>
                      </div>
                      <div class="score-item">
                        <span class="s-name">Value</span>
                        <span class="s-val">{value_s}</span>
                      </div>
                      <div class="score-item">
                        <span class="s-name">Emotion</span>
                        <span class="s-val">{emo_s}</span>
                      </div>
                      <div class="score-item">
                        <span class="s-name">Context</span>
                        <span class="s-val">{context_s}</span>
                      </div>
                      <div class="score-item">
                        <span class="s-name">Ending</span>
                        <span class="s-val">{ending_s}</span>
                      </div>
                    </div>
                  </div>

                  <div class="social-box">
                    <div class="social-header">
                      <span class="social-label">📱 SUGGESTED SOCIAL POST</span>
                      <button class="btn-copy" onclick="copyText('social-{c_num}', this)">📋 Copy Post</button>
                    </div>
                    <div class="social-content" id="social-{c_num}">{caption}<br><br><span class="hashtags">{hashtags}</span></div>
                  </div>

                  <div class="card-actions">
                    <a href="{video_filename}" download class="btn-action primary">⬇️ Download Video (MP4)</a>
                    <a href="{srt_filename}" download class="btn-action secondary">📝 Download SRT</a>
                  </div>
                </div>
              </div>
            </div>
            """
            clip_cards_html.append(card)

        all_cards = "\n".join(clip_cards_html)

        html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Clipping Intelligence Report - {title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-primary: #f8fafc;
      --bg-secondary: #ffffff;
      --card-bg: #ffffff;
      --border-color: #e2e8f0;
      --border-subtle: #f1f5f9;
      --accent: #4f46e5;
      --accent-hover: #4338ca;
      --accent-light: #eef2ff;
      --accent-glow: rgba(79, 70, 229, 0.16);
      --text-main: #0f172a;
      --text-muted: #475569;
      --text-dim: #64748b;
      --success: #059669;
      --success-light: #ecfdf5;
      --radius-sm: 8px;
      --radius-md: 12px;
      --radius-lg: 16px;
      --radius-xl: 20px;
      --font-main: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
      --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
      --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
      --shadow-lg: 0 10px 25px -3px rgba(15, 23, 42, 0.08), 0 4px 6px -4px rgba(15, 23, 42, 0.04);
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      background-color: var(--bg-primary);
      color: var(--text-main);
      font-family: var(--font-main);
      line-height: 1.5;
      min-height: 100vh;
      background-image: radial-gradient(ellipse at 50% -10%, rgba(99, 102, 241, 0.08) 0%, rgba(248, 250, 252, 0) 70%);
      padding-bottom: 60px;
    }}

    /* Sticky Navbar */
    .navbar {{
      border-bottom: 1px solid var(--border-color);
      background: rgba(255, 255, 255, 0.9);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      position: sticky;
      top: 0;
      z-index: 50;
      box-shadow: var(--shadow-sm);
    }}

    .nav-container {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 14px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}

    .brand {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .logo-icon {{
      font-size: 22px;
      background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
      color: #fff;
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: var(--radius-md);
      box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);
    }}

    .brand-text h1 {{
      font-size: 19px;
      font-weight: 800;
      letter-spacing: -0.5px;
      color: var(--text-main);
    }}

    .badge {{
      font-size: 11px;
      font-weight: 700;
      color: var(--accent);
      background: var(--accent-light);
      padding: 2px 8px;
      border-radius: 9999px;
      display: inline-block;
      margin-top: 2px;
    }}

    .nav-actions {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .nav-instagram {{
      background: linear-gradient(135deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%);
      color: #fff;
      text-decoration: none;
      font-size: 12px;
      font-weight: 700;
      padding: 6px 14px;
      border-radius: 9999px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      box-shadow: 0 2px 6px rgba(220, 39, 67, 0.25);
      transition: opacity 0.2s, transform 0.15s;
    }}

    .nav-instagram:hover {{
      opacity: 0.92;
      transform: translateY(-1px);
    }}

    .btn-nav {{
      background: #ffffff;
      color: var(--text-main);
      border: 1px solid var(--border-color);
      padding: 7px 16px;
      border-radius: var(--radius-sm);
      font-size: 13px;
      font-weight: 600;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s;
    }}

    .btn-nav:hover {{
      background: var(--bg-tertiary, #f1f5f9);
      border-color: #cbd5e1;
    }}

    /* Main Container */
    .container {{
      max-width: 1240px;
      margin: 32px auto 0 auto;
      padding: 0 24px;
    }}

    /* Hero / Project Summary Card */
    .project-header-card {{
      background: #ffffff;
      border: 1px solid var(--border-color);
      border-radius: var(--radius-xl);
      padding: 32px;
      margin-bottom: 32px;
      box-shadow: var(--shadow-lg);
    }}

    .hero-pill {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: var(--accent-light);
      border: 1px solid rgba(79, 70, 229, 0.2);
      padding: 5px 14px;
      border-radius: 9999px;
      font-size: 12px;
      font-weight: 700;
      color: var(--accent);
      margin-bottom: 16px;
    }}

    .project-title {{
      font-size: 26px;
      font-weight: 800;
      letter-spacing: -0.5px;
      color: var(--text-main);
      margin-bottom: 18px;
      line-height: 1.3;
    }}

    .gradient-text {{
      background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #db2777 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}

    .project-stats-grid {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      padding-top: 16px;
      border-top: 1px solid var(--border-subtle);
    }}

    .stat-pill {{
      display: flex;
      align-items: center;
      gap: 8px;
      background: var(--bg-primary);
      border: 1px solid var(--border-color);
      padding: 8px 16px;
      border-radius: var(--radius-md);
      font-size: 13px;
      color: var(--text-muted);
    }}

    .stat-pill strong {{
      color: var(--text-main);
      font-weight: 700;
    }}

    .stat-pill.success {{
      background: var(--success-light);
      border-color: #a7f3d0;
      color: var(--success);
    }}

    .stat-pill.success strong {{
      color: var(--success);
    }}

    /* Section Title */
    .section-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 20px;
    }}

    .section-title {{
      font-size: 18px;
      font-weight: 800;
      color: var(--text-main);
      letter-spacing: -0.3px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .section-count {{
      font-size: 12px;
      font-weight: 700;
      color: var(--accent);
      background: var(--accent-light);
      padding: 4px 10px;
      border-radius: 9999px;
    }}

    /* Clips Grid */
    .clips-grid {{
      display: flex;
      flex-direction: column;
      gap: 28px;
    }}

    /* Clip Card */
    .clip-card {{
      background: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-lg);
      overflow: hidden;
      box-shadow: var(--shadow-md);
      transition: transform 0.2s, box-shadow 0.2s;
    }}

    .clip-card:hover {{
      box-shadow: var(--shadow-lg);
    }}

    .clip-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      padding: 20px 24px;
      border-bottom: 1px solid var(--border-color);
      background: #fafbfc;
      gap: 16px;
    }}

    .clip-title-group {{
      display: flex;
      align-items: flex-start;
      gap: 14px;
      flex: 1;
    }}

    .clip-badge {{
      background: var(--accent);
      color: #ffffff;
      font-weight: 800;
      font-size: 11px;
      padding: 4px 10px;
      border-radius: 6px;
      letter-spacing: 0.5px;
      margin-top: 2px;
      white-space: nowrap;
    }}

    .clip-heading-wrap {{
      display: flex;
      flex-direction: column;
      gap: 4px;
    }}

    .clip-title {{
      font-size: 17px;
      font-weight: 700;
      color: var(--text-main);
      line-height: 1.4;
    }}

    .hook-title-pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: #fffbeb;
      border: 1px solid #fde68a;
      color: #b45309;
      font-size: 12px;
      font-weight: 700;
      padding: 3px 10px;
      border-radius: 6px;
      margin-top: 4px;
      width: fit-content;
    }}

    .score-badge {{
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 6px 16px;
      border-radius: var(--radius-md);
      border: 1px solid;
      min-width: 90px;
    }}

    .score-val {{
      font-size: 22px;
      font-weight: 900;
      font-family: var(--font-mono);
      line-height: 1.1;
    }}

    .score-lbl {{
      font-size: 9px;
      font-weight: 800;
      letter-spacing: 0.5px;
      opacity: 0.85;
      text-transform: uppercase;
      margin-top: 2px;
    }}

    /* Clip Body Grid */
    .clip-body {{
      display: grid;
      grid-template-columns: 320px 1fr;
      gap: 28px;
      padding: 24px;
    }}

    @media (max-width: 960px) {{
      .clip-body {{
        grid-template-columns: 1fr;
      }}
    }}

    /* Video Player */
    .video-preview-wrapper {{
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}

    .video-frame {{
      background: #0f172a;
      border-radius: var(--radius-md);
      overflow: hidden;
      border: 1px solid var(--border-color);
      box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
      position: relative;
    }}

    video {{
      width: 100%;
      aspect-ratio: 9/16;
      display: block;
      object-fit: cover;
      max-height: 520px;
      background: #000;
    }}

    .video-meta-tags {{
      display: flex;
      justify-content: space-between;
      gap: 8px;
    }}

    .meta-tag {{
      flex: 1;
      text-align: center;
      font-size: 11px;
      font-weight: 600;
      color: var(--text-muted);
      background: var(--bg-tertiary, #f1f5f9);
      border: 1px solid var(--border-color);
      padding: 6px 8px;
      border-radius: var(--radius-sm);
      white-space: nowrap;
    }}

    /* Clip Details */
    .clip-details {{
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}

    .detail-block {{
      background: #f8fafc;
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      padding: 14px 16px;
    }}

    .detail-label {{
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.5px;
      color: var(--text-dim);
      margin-bottom: 4px;
      display: flex;
      align-items: center;
      gap: 6px;
      text-transform: uppercase;
    }}

    .detail-content {{
      font-size: 14px;
      color: var(--text-main);
      line-height: 1.5;
    }}

    /* Scores Section */
    .scores-section {{
      background: #ffffff;
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      padding: 14px 16px;
    }}

    .scores-header {{
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.5px;
      color: var(--text-dim);
      margin-bottom: 10px;
      text-transform: uppercase;
    }}

    .scores-grid {{
      display: grid;
      grid-template-columns: repeat(6, 1fr);
      gap: 8px;
    }}

    @media (max-width: 600px) {{
      .scores-grid {{
        grid-template-columns: repeat(3, 1fr);
      }}
    }}

    .score-item {{
      background: #f8fafc;
      border: 1px solid var(--border-color);
      border-radius: var(--radius-sm);
      padding: 8px 4px;
      text-align: center;
    }}

    .s-name {{
      display: block;
      font-size: 10px;
      font-weight: 700;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.3px;
    }}

    .s-val {{
      display: block;
      font-size: 14px;
      font-weight: 800;
      font-family: var(--font-mono);
      color: var(--accent);
      margin-top: 2px;
    }}

    /* Social Post Box */
    .social-box {{
      background: #f8fafc;
      border: 1px dashed #cbd5e1;
      border-radius: var(--radius-md);
      padding: 14px 16px;
    }}

    .social-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }}

    .social-label {{
      font-size: 11px;
      font-weight: 800;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.3px;
    }}

    .btn-copy {{
      background: #ffffff;
      border: 1px solid var(--border-color);
      color: var(--text-main);
      padding: 4px 12px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 12px;
      font-weight: 600;
      transition: all 0.2s;
    }}

    .btn-copy:hover {{
      background: var(--bg-tertiary, #f1f5f9);
      border-color: #cbd5e1;
    }}

    .social-content {{
      font-size: 13px;
      color: #334155;
      white-space: pre-wrap;
      line-height: 1.5;
    }}

    .hashtags {{
      color: var(--accent);
      font-weight: 600;
    }}

    /* Card Actions */
    .card-actions {{
      display: flex;
      gap: 12px;
      margin-top: auto;
      padding-top: 8px;
    }}

    .btn-action {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 10px 18px;
      border-radius: var(--radius-md);
      font-size: 13px;
      font-weight: 700;
      text-decoration: none;
      transition: all 0.2s;
    }}

    .btn-action.primary {{
      background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
      color: #ffffff;
      box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);
    }}

    .btn-action.primary:hover {{
      opacity: 0.94;
      transform: translateY(-1px);
    }}

    .btn-action.secondary {{
      background: #ffffff;
      color: var(--text-main);
      border: 1px solid var(--border-color);
    }}

    .btn-action.secondary:hover {{
      background: var(--bg-tertiary, #f1f5f9);
      border-color: #cbd5e1;
    }}

    /* Footer */
    .report-footer {{
      margin-top: 60px;
      padding-top: 24px;
      border-top: 1px solid var(--border-color);
      text-align: center;
      font-size: 13px;
      color: var(--text-dim);
    }}

    .report-footer a {{
      color: var(--accent);
      text-decoration: none;
      font-weight: 600;
    }}
  </style>
</head>
<body>
  <!-- Navigation Header -->
  <header class="navbar">
    <div class="nav-container">
      <div class="brand">
        <div class="logo-icon">⚡</div>
        <div class="brand-text">
          <h1>AIYT Clipper</h1>
          <span class="badge">Shorts & Reels &bull; By Mohsin Khawaja</span>
        </div>
      </div>
      <div class="nav-actions">
        <a href="https://www.instagram.com/csib.mohsin/" target="_blank" rel="noopener noreferrer" class="nav-instagram">
          📸 <span>@csib.mohsin</span>
        </a>
        <a href="http://127.0.0.1:8000" class="btn-nav">
          <span>⚡ Studio Dashboard</span>
        </a>
      </div>
    </div>
  </header>

  <!-- Content Container -->
  <main class="container">
    <!-- Project Overview Card -->
    <div class="project-header-card">
      <div class="hero-pill">
        <span>✨</span>
        <span>Autonomous AI Video Repurposing Report</span>
      </div>
      <h2 class="project-title">🎬 {title}</h2>
      <div class="project-stats-grid">
        <div class="stat-pill">👤 Channel: <strong>{uploader}</strong></div>
        <div class="stat-pill">⚡ Generated Clips: <strong>{total_clips}</strong></div>
        <div class="stat-pill success">🔥 Avg Viral Score: <strong>{avg_score} / 100</strong></div>
        <div class="stat-pill">📐 Format: <strong>1080×1920 (9:16 Vertical 60FPS)</strong></div>
        <div class="stat-pill">🧠 Engine: <strong>Autonomous NLP & Vision Studio</strong></div>
      </div>
    </div>

    <div class="section-header">
      <h3 class="section-title">
        <span>Curated Vertical Deliverables</span>
      </h3>
      <span class="section-count">{total_clips} Ready-to-Post Clips</span>
    </div>

    <!-- Clips Grid -->
    <div class="clips-grid">
      {all_cards}
    </div>

    <!-- Footer -->
    <footer class="report-footer">
      <p>AIYT Clipper &bull; Engineered by <strong>Mohsin Khawaja</strong> &bull; Follow on Instagram: <a href="https://www.instagram.com/csib.mohsin/" target="_blank">@csib.mohsin</a></p>
      <p style="margin-top: 4px; font-size: 11px; color: #94a3b8;">Personal & Non-Commercial License &bull; High-Retention Autonomous Video Repurposing</p>
    </footer>
  </main>

  <script>
    // Copy Text with dynamic button feedback
    function copyText(id, btn) {{
      const el = document.getElementById(id);
      if (!el) return;
      const text = el.innerText;
      navigator.clipboard.writeText(text).then(() => {{
        const originalText = btn.innerHTML;
        btn.innerHTML = "✅ Copied!";
        btn.style.background = "#ecfdf5";
        btn.style.color = "#059669";
        btn.style.borderColor = "#a7f3d0";
        setTimeout(() => {{
          btn.innerHTML = originalText;
          btn.style.background = "";
          btn.style.color = "";
          btn.style.borderColor = "";
        }}, 2000);
      }}).catch(err => {{
        console.error("Copy failed", err);
      }});
    }}

    // Pause other videos when one plays
    document.addEventListener("play", function(e) {{
      const videos = document.getElementsByTagName("video");
      for (let i = 0; i < videos.length; i++) {{
        if (videos[i] !== e.target) {{
          videos[i].pause();
        }}
      }}
    }}, true);
  </script>
</body>
</html>"""
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_doc)
        return html_doc

    @staticmethod
    def _format_mmss(seconds: float) -> str:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
