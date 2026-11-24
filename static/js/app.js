document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const youtubeUrlInput = document.getElementById('youtubeUrl');
  const btnStart = document.getElementById('btnStart');

  const progressSection = document.getElementById('progressSection');
  const progressStage = document.getElementById('progressStage');
  const progressMessage = document.getElementById('progressMessage');
  const progressPercent = document.getElementById('progressPercent');
  const progressBarFill = document.getElementById('progressBarFill');
  const consoleLogs = document.getElementById('consoleLogs');

  const resultsSection = document.getElementById('resultsSection');
  const videoTitleDisplay = document.getElementById('videoTitleDisplay');
  const videoMetaDisplay = document.getElementById('videoMetaDisplay');
  const clipsGrid = document.getElementById('clipsGrid');
  const btnOpenReport = document.getElementById('btnOpenReport');

  // Steps
  const stepMeta = document.getElementById('stepMeta');
  const stepTranscript = document.getElementById('stepTranscript');
  const stepAI = document.getElementById('stepAI');
  const stepRender = document.getElementById('stepRender');
  const stepQC = document.getElementById('stepQC');

  // Modals & Settings
  const settingsModal = document.getElementById('settingsModal');
  const btnSettings = document.getElementById('btnSettings');
  const btnCloseSettings = document.getElementById('btnCloseSettings');
  const btnSaveSettings = document.getElementById('btnSaveSettings');
  const cfgGeminiKey = document.getElementById('cfgGeminiKey');
  const cfgCropMode = document.getElementById('cfgCropMode');
  const cfgBgBlur = document.getElementById('cfgBgBlur');
  const cfgEnableHookTitle = document.getElementById('cfgEnableHookTitle');
  const cfgHookTitleStyle = document.getElementById('cfgHookTitleStyle');
  const cfgSubPos = document.getElementById('cfgSubPos');
  const cfgHighlightColor = document.getElementById('cfgHighlightColor');
  const cfgFont = document.getElementById('cfgFont');
  const cfgClipCount = document.getElementById('cfgClipCount');

  const historyModal = document.getElementById('historyModal');
  const btnHistory = document.getElementById('btnHistory');
  const btnCloseHistory = document.getElementById('btnCloseHistory');
  const projectsList = document.getElementById('projectsList');

  let currentJobId = null;
  let eventSource = null;

  // 1. Start Analysis
  btnStart.addEventListener('click', async () => {
    const url = youtubeUrlInput.value.trim();
    if (!url) {
      alert('Please enter a valid YouTube video URL.');
      youtubeUrlInput.focus();
      return;
    }

    // Reset UI
    btnStart.disabled = true;
    progressSection.classList.remove('hidden');
    resultsSection.classList.add('hidden');
    clipsGrid.innerHTML = '';
    consoleLogs.innerHTML = '';
    updateProgress(0, 'Initializing pipeline and requesting metadata...');
    resetSteps();

    try {
      const res = await fetch('/api/start-job', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to start analysis job');
      }

      const data = await res.json();
      currentJobId = data.job_id;
      listenToJobProgress(currentJobId);
    } catch (err) {
      alert(`Error starting job: ${err.message}`);
      btnStart.disabled = false;
      progressSection.classList.add('hidden');
    }
  });

  // 2. Stream Job Updates via SSE
  function listenToJobProgress(jobId) {
    if (eventSource) {
      eventSource.close();
    }

    eventSource = new EventSource(`/api/stream/${jobId}`);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const pct = data.progress || 0;
        const msg = data.message || '';

        updateProgress(pct, msg);

        if (data.status === 'completed') {
          eventSource.close();
          btnStart.disabled = false;
          updateStepsByProgress(100);
          if (data.result) {
            displayResults(data.result);
          } else {
            fetchJobResult(jobId);
          }
        } else if (data.status === 'failed') {
          eventSource.close();
          btnStart.disabled = false;
          alert(`Analysis failed: ${data.error || msg}`);
        }
      } catch (e) {
        console.error('Error parsing SSE event:', e);
      }
    };

    eventSource.onerror = (err) => {
      console.warn('SSE connection issue, falling back to polling...', err);
      eventSource.close();
      pollJobProgress(jobId);
    };
  }

  // Polling Fallback
  async function pollJobProgress(jobId) {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/job-status/${jobId}`);
        if (!res.ok) return;
        const data = await res.json();

        updateProgress(data.progress || 0, data.message || '');

        if (data.status === 'completed') {
          clearInterval(interval);
          btnStart.disabled = false;
          if (data.result) {
            displayResults(data.result);
          }
        } else if (data.status === 'failed') {
          clearInterval(interval);
          btnStart.disabled = false;
          alert(`Analysis failed: ${data.error || data.message}`);
        }
      } catch (e) {
        console.error('Polling error:', e);
      }
    }, 1500);
  }

  async function fetchJobResult(jobId) {
    try {
      const res = await fetch(`/api/job-status/${jobId}`);
      const data = await res.json();
      if (data.result) {
        displayResults(data.result);
      }
    } catch (e) {
      console.error('Error fetching result:', e);
    }
  }

  function updateProgress(percent, message) {
    const p = Math.min(100, Math.max(0, percent));
    progressPercent.innerText = `${Math.round(p)}%`;
    progressBarFill.style.width = `${p}%`;
    progressMessage.innerText = message;

    // Stage text
    if (p < 25) {
      progressStage.innerText = "Downloading Source Video...";
    } else if (p < 45) {
      progressStage.innerText = "Transcribing Speech & Timestamps...";
    } else if (p < 60) {
      progressStage.innerText = "AI Analyzing Hooks & Viral Moments...";
    } else if (p < 95) {
      progressStage.innerText = "Tracking Faces & Rendering Vertical 9:16...";
    } else {
      progressStage.innerText = "Finalizing Project & Quality Control...";
    }

    updateStepsByProgress(p);

    // Add log
    const logItem = document.createElement('div');
    logItem.innerText = `[${p.toFixed(1)}%] ${message}`;
    consoleLogs.appendChild(logItem);
    consoleLogs.scrollTop = consoleLogs.scrollHeight;
  }

  function resetSteps() {
    [stepMeta, stepTranscript, stepAI, stepRender, stepQC].forEach(s => {
      s.className = 'step-item';
    });
  }

  function updateStepsByProgress(p) {
    if (p >= 5) setStep(stepMeta, p >= 25 ? 'completed' : 'active');
    if (p >= 25) setStep(stepTranscript, p >= 45 ? 'completed' : 'active');
    if (p >= 45) setStep(stepAI, p >= 60 ? 'completed' : 'active');
    if (p >= 60) setStep(stepRender, p >= 95 ? 'completed' : 'active');
    if (p >= 95) setStep(stepQC, p >= 100 ? 'completed' : 'active');
  }

  function setStep(el, state) {
    el.className = `step-item ${state}`;
  }

  // 3. Display Results
  function displayResults(result) {
    progressSection.classList.add('hidden');
    resultsSection.classList.remove('hidden');

    const videoInfo = result.video_info || {};
    const projectName = result.project_name || '';
    const clips = result.clips || [];

    videoTitleDisplay.innerText = videoInfo.title || 'Generated Clips';
    videoMetaDisplay.innerText = `Creator: ${videoInfo.uploader || 'Unknown'} • Total Clips: ${clips.length} • 1080x1920 Vertical (9:16)`;
    btnOpenReport.href = `/output/${projectName}/report.html`;

    clipsGrid.innerHTML = '';

    clips.forEach(clip => {
      const card = createClipCard(clip, projectName);
      clipsGrid.appendChild(card);
    });

    resultsSection.scrollIntoView({ behavior: 'smooth' });
  }

  function createClipCard(clip, projectName) {
    const card = document.createElement('div');
    card.className = 'ui-clip-card';

    const clipNum = clip.clip_number || 1;
    const padNum = String(clipNum).padStart(2, '0');
    const title = clip.title || `Clip #${clipNum}`;
    const hookTitle = clip.hook_title || title || 'WAIT FOR THE END! 😱';
    const score = clip.engagement_score || 85;
    const dur = (clip.duration || 0).toFixed(1);
    const startM = formatMMSS(clip.start_time || 0);
    const endM = formatMMSS(clip.end_time || 0);
    const hook = clip.hook_description || 'High-retention opening moment.';
    const caption = clip.social_caption || '';
    const hashtags = (clip.hashtags || []).join(' ');
    const fullSocial = `${caption}\n\n${hashtags}`.trim();

    const videoSrc = `/output/${projectName}/clips/clip_${padNum}.mp4`;
    const thumbSrc = `/output/${projectName}/thumbnails/clip_${padNum}.jpg`;
    const srtSrc = `/output/${projectName}/captions/clip_${padNum}.srt`;

    card.innerHTML = `
      <div class="ui-clip-video-wrap">
        <video controls poster="${thumbSrc}" preload="metadata">
          <source src="${videoSrc}" type="video/mp4">
        </video>
        <div class="ui-clip-badge-float">#${padNum} • ${dur}s (${startM}-${endM})</div>
        <div class="ui-clip-score-float">🔥 ${score}/100</div>
      </div>
      <div class="ui-clip-content">
        <h3 class="ui-clip-title">${escapeHtml(title)}</h3>

        <!-- Interactive AI Hook Title Editor (Top of Reel) -->
        <div class="ui-hook-title-box">
          <div class="hook-head">
            <span class="hook-badge">🔥 TOP HOOK TITLE (TOP OF REEL)</span>
            <button class="btn-mini-regen" data-project="${escapeAttr(projectName)}" data-clip="${clipNum}">⚡ AI Regenerate</button>
          </div>
          <div class="hook-input-row">
            <input type="text" class="input-hook-title" data-clip="${clipNum}" value="${escapeAttr(hookTitle)}" placeholder="Top Hook Title..." />
            <button class="btn-update-hook" data-project="${escapeAttr(projectName)}" data-clip="${clipNum}">🔄 Update Video</button>
          </div>
        </div>

        <div class="ui-clip-hook">🎯 <strong>Hook:</strong> ${escapeHtml(hook)}</div>
        <div class="ui-clip-scores">
          <div class="score-chip">
            <span>Hook</span>
            <strong>${clip.hook_score || 8.5}/10</strong>
          </div>
          <div class="score-chip">
            <span>Interest</span>
            <strong>${clip.interest_score || 8.5}/10</strong>
          </div>
          <div class="score-chip">
            <span>Value</span>
            <strong>${clip.value_score || 8.5}/10</strong>
          </div>
        </div>
        <div class="ui-clip-caption-box">
          <div class="caption-head">
            <span>Social Post Copy</span>
            <button class="btn-mini-copy" data-text="${escapeAttr(fullSocial)}">📋 Copy</button>
          </div>
          <div class="caption-body">${escapeHtml(caption)}<br><span style="color:#818cf8">${escapeHtml(hashtags)}</span></div>
        </div>
        <div class="ui-clip-actions">
          <a href="${videoSrc}" download class="btn-primary">⬇️ Download Video</a>
          <a href="${srtSrc}" download class="btn-secondary">📝 SRT</a>
        </div>
      </div>
    `;

    // Hook Title Regenerate Button
    const regenBtn = card.querySelector('.btn-mini-regen');
    if (regenBtn) {
      regenBtn.addEventListener('click', async () => {
        const origText = regenBtn.innerText;
        regenBtn.innerText = '⚡ Thinking...';
        regenBtn.disabled = true;
        try {
          const res = await fetch('/api/clips/regenerate-title', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ project_name: projectName, clip_number: clipNum })
          });
          const data = await res.json();
          if (data.hook_title) {
            const input = card.querySelector('.input-hook-title');
            input.value = data.hook_title;
            input.style.borderColor = '#fbbf24';
            setTimeout(() => input.style.borderColor = '', 1500);
          }
        } catch (e) {
          alert('Failed to regenerate title: ' + e);
        } finally {
          regenBtn.innerText = origText;
          regenBtn.disabled = false;
        }
      });
    }

    // Hook Title Update & Re-render Button
    const updateBtn = card.querySelector('.btn-update-hook');
    if (updateBtn) {
      updateBtn.addEventListener('click', async () => {
        const input = card.querySelector('.input-hook-title');
        const newTitle = input.value.trim();
        if (!newTitle) {
          alert('Please enter a hook title.');
          return;
        }
        const origText = updateBtn.innerText;
        updateBtn.innerText = '⏳ Rendering...';
        updateBtn.disabled = true;
        try {
          const res = await fetch('/api/clips/update-title', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              project_name: projectName,
              clip_number: clipNum,
              hook_title: newTitle
            })
          });
          if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Failed to update video');
          }
          const data = await res.json();
          const video = card.querySelector('video');
          if (video) {
            video.src = data.video_url;
            video.poster = data.thumb_url;
            video.load();
          }
          updateBtn.innerText = '✓ Updated!';
          setTimeout(() => {
            updateBtn.innerText = origText;
            updateBtn.disabled = false;
          }, 2500);
        } catch (e) {
          alert('Error updating title: ' + e.message);
          updateBtn.innerText = origText;
          updateBtn.disabled = false;
        }
      });
    }

    // Copy caption listener
    const copyBtn = card.querySelector('.btn-mini-copy');
    copyBtn.addEventListener('click', (e) => {
      const textToCopy = e.target.getAttribute('data-text');
      navigator.clipboard.writeText(textToCopy).then(() => {
        copyBtn.innerText = '✓ Copied!';
        setTimeout(() => copyBtn.innerText = '📋 Copy', 2000);
      });
    });

    return card;
  }

  function formatMMSS(sec) {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }

  function escapeHtml(str) {
    return (str || '').replace(/[&<>"']/g, m => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
    }[m]));
  }

  function escapeAttr(str) {
    return (str || '').replace(/"/g, '&quot;');
  }

  // 4. Settings Modal
  btnSettings.addEventListener('click', async () => {
    try {
      const res = await fetch('/api/config');
      const cfg = await res.json();
      cfgGeminiKey.value = cfg.gemini_api_key || '';
      cfgCropMode.value = cfg.crop_mode || 'center_zoom';
      if (cfgBgBlur) cfgBgBlur.value = cfg.bg_blur_style || 'cinematic';
      if (cfgEnableHookTitle) cfgEnableHookTitle.value = (cfg.enable_hook_title !== false) ? 'true' : 'false';
      if (cfgHookTitleStyle) cfgHookTitleStyle.value = cfg.hook_title_style || 'bold_headline';
      if (cfgSubPos) cfgSubPos.value = cfg.subtitle_position || 'bottom_safe';
      if (cfgHighlightColor) cfgHighlightColor.value = cfg.caption_highlight || 'yellow';
      if (cfgFont) cfgFont.value = cfg.caption_font || 'Arial Black';
      cfgClipCount.value = cfg.target_clip_count || 5;
    } catch (e) {
      console.error(e);
    }
    settingsModal.classList.remove('hidden');
  });

  btnCloseSettings.addEventListener('click', () => {
    settingsModal.classList.add('hidden');
  });

  btnSaveSettings.addEventListener('click', async () => {
    const key = cfgGeminiKey.value.trim();
    const payload = {
      gemini_api_key: key,
      crop_mode: cfgCropMode.value,
      bg_blur_style: cfgBgBlur ? cfgBgBlur.value : 'cinematic',
      enable_hook_title: cfgEnableHookTitle ? (cfgEnableHookTitle.value === 'true') : true,
      hook_title_style: cfgHookTitleStyle ? cfgHookTitleStyle.value : 'bold_headline',
      subtitle_position: cfgSubPos ? cfgSubPos.value : 'bottom_safe',
      caption_highlight: cfgHighlightColor ? cfgHighlightColor.value : 'yellow',
      caption_font: cfgFont ? cfgFont.value : 'Arial Black',
      target_clip_count: parseInt(cfgClipCount.value) || 5
    };
    try {
      await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      alert('Settings saved successfully!');
      settingsModal.classList.add('hidden');
    } catch (e) {
      alert('Error saving settings: ' + e);
    }
  });

  // 5. Past Projects History
  btnHistory.addEventListener('click', async () => {
    historyModal.classList.remove('hidden');
    projectsList.innerHTML = '<div class="empty-state">Loading projects...</div>';
    try {
      const res = await fetch('/api/projects');
      const projects = await res.json();

      if (!projects || projects.length === 0) {
        projectsList.innerHTML = '<div class="empty-state">No previous projects found.</div>';
        return;
      }

      projectsList.innerHTML = '';
      projects.forEach(p => {
        const item = document.createElement('div');
        item.className = 'project-item';
        item.innerHTML = `
          <div>
            <div class="project-item-title">🎬 ${escapeHtml(p.title)}</div>
            <div class="project-item-meta">Clips: ${p.clip_count} • Duration: ${Math.round(p.duration)}s</div>
          </div>
          <div style="display:flex; gap:8px;">
            <button class="btn-primary btn-open-project" data-folder="${escapeAttr(p.folder_name)}" style="font-size:12px; padding:6px 12px;">📂 Open</button>
            <a href="/output/${p.folder_name}/report.html" target="_blank" class="btn-secondary" style="font-size:12px; padding:6px 12px;">📊 Report</a>
          </div>
        `;
        const openBtn = item.querySelector('.btn-open-project');
        openBtn.addEventListener('click', async () => {
          historyModal.classList.add('hidden');
          try {
            const res = await fetch(`/api/projects/${p.folder_name}`);
            const data = await res.json();
            displayResults({
              project_name: p.folder_name,
              video_info: data.video_info,
              clips: data.clips
            });
          } catch (e) {
            alert('Failed to load project: ' + e);
          }
        });
        projectsList.appendChild(item);
      });
    } catch (e) {
      projectsList.innerHTML = `<div class="empty-state">Failed to load projects: ${e}</div>`;
    }
  });

  btnCloseHistory.addEventListener('click', () => {
    historyModal.classList.add('hidden');
  });

  // Close modals on outside click
  window.addEventListener('click', (e) => {
    if (e.target === settingsModal) settingsModal.classList.add('hidden');
    if (e.target === historyModal) historyModal.classList.add('hidden');
  });
});

