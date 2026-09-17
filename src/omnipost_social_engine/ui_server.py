"""
Omnipost Social Engine - Studio UI Server
Zero-dependency ThreadingHTTPServer serving Material 3 Omnipost Studio UI (design influenced by Google Material tokens)
and REST APIs (/api/health, /api/format, /api/split, /api/hooks, /api/analyze, /api/export, /api/mcp/config).
"""

from __future__ import annotations

import cgi
import http.server
import json
import mimetypes
import os
import socket
import sys
import threading
import urllib.parse
from typing import Any, Dict, Optional, Tuple

from .campaign_exporter import CampaignExporter
from .mcp_server import (
    analyze_engagement_engine,
    format_post_engine,
    generate_hooks_engine,
    get_client_configs,
    get_diagnostics_engine,
    split_thread_engine,
)
from .accessibility_synthesizer import evaluate_accessibility_suite


def get_public_dir() -> str:
    """Find the public static assets directory."""
    # Check relative to module path (repository root)
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    repo_public = os.path.abspath(os.path.join(pkg_dir, "..", "..", "public"))
    if os.path.isdir(repo_public) and os.path.isfile(os.path.join(repo_public, "index.html")):
        return repo_public

    # Check current working directory
    cwd_public = os.path.join(os.getcwd(), "public")
    if os.path.isdir(cwd_public):
        return cwd_public

    return repo_public


EMBEDDED_STUDIO_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Omnipost Social Engine — Material 3 Studio</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --md-sys-color-primary: #6750A4;
      --md-sys-color-on-primary: #FFFFFF;
      --md-sys-color-primary-container: #EADDFF;
      --md-sys-color-on-primary-container: #21005D;
      --md-sys-color-surface: #1C1B1F;
      --md-sys-color-surface-dim: #141218;
      --md-sys-color-surface-container: #2B2930;
      --md-sys-color-surface-container-high: #36343B;
      --md-sys-color-on-surface: #E6E1E5;
      --md-sys-color-on-surface-variant: #CAC4D0;
      --md-sys-color-outline: #938F99;
      --md-sys-color-outline-variant: #49454F;
      --md-sys-color-secondary: #CCC2DC;
      --md-sys-color-tertiary: #EFB8C8;
      --md-sys-color-error: #F2B8B5;
      --md-sys-color-success: #81C784;
      --font-main: 'Plus Jakarta Sans', system-ui, sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--md-sys-color-surface-dim);
      color: var(--md-sys-color-on-surface);
      font-family: var(--font-main);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    /* Top App Bar */
    header {
      background: var(--md-sys-color-surface-container);
      border-bottom: 1px solid var(--md-sys-color-outline-variant);
      padding: 0.85rem 1.5rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 100;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      font-weight: 800;
      font-size: 1.25rem;
      letter-spacing: -0.5px;
      color: #FFFFFF;
    }
    .brand-badge {
      background: linear-gradient(135deg, #7C4DFF, #FF4081);
      color: #FFF;
      font-size: 0.7rem;
      font-weight: 700;
      padding: 0.2rem 0.6rem;
      border-radius: 999px;
      text-transform: uppercase;
    }
    .status-pill {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.8rem;
      background: var(--md-sys-color-surface-container-high);
      padding: 0.35rem 0.8rem;
      border-radius: 20px;
      border: 1px solid var(--md-sys-color-outline-variant);
    }
    .status-dot {
      width: 8px;
      height: 8px;
      background: #4CAF50;
      border-radius: 50%;
      box-shadow: 0 0 8px #4CAF50;
    }

    /* Navigation Tabs */
    .tabs-bar {
      background: var(--md-sys-color-surface);
      border-bottom: 1px solid var(--md-sys-color-outline-variant);
      display: flex;
      gap: 0.5rem;
      padding: 0.5rem 1.5rem 0;
      overflow-x: auto;
    }
    .tab-btn {
      background: transparent;
      border: none;
      color: var(--md-sys-color-on-surface-variant);
      font-family: var(--font-main);
      font-weight: 600;
      font-size: 0.9rem;
      padding: 0.75rem 1.25rem;
      cursor: pointer;
      border-bottom: 3px solid transparent;
      transition: all 0.2s ease;
      white-space: nowrap;
    }
    .tab-btn:hover {
      color: var(--md-sys-color-on-surface);
    }
    .tab-btn.active {
      color: #D0BCFF;
      border-bottom-color: #D0BCFF;
    }

    /* Main Container */
    main {
      flex: 1;
      padding: 1.5rem;
      max-width: 1280px;
      margin: 0 auto;
      width: 100%;
    }

    .tab-content { display: none; }
    .tab-content.active { display: block; animation: fadeIn 0.25s ease-out; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

    /* Grid Layouts */
    .two-col {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.5rem;
    }
    @media (max-width: 900px) {
      .two-col { grid-template-columns: 1fr; }
    }

    /* Cards */
    .card {
      background: var(--md-sys-color-surface-container);
      border: 1px solid var(--md-sys-color-outline-variant);
      border-radius: 16px;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .card-title {
      font-size: 1.1rem;
      font-weight: 700;
      color: #FFFFFF;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    /* Form Controls */
    label {
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--md-sys-color-on-surface-variant);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    textarea, input, select {
      background: var(--md-sys-color-surface-container-high);
      border: 1px solid var(--md-sys-color-outline-variant);
      color: #FFFFFF;
      font-family: inherit;
      font-size: 0.95rem;
      border-radius: 10px;
      padding: 0.75rem 1rem;
      width: 100%;
      outline: none;
      transition: border-color 0.2s;
    }
    textarea:focus, input:focus, select:focus {
      border-color: #D0BCFF;
    }
    textarea {
      min-height: 140px;
      resize: vertical;
      line-height: 1.5;
    }
    .code-box {
      font-family: var(--font-mono);
      font-size: 0.85rem;
      white-space: pre-wrap;
      word-break: break-word;
      background: #111014;
      border: 1px solid #332F38;
      border-radius: 10px;
      padding: 1rem;
      color: #00E676;
      max-height: 400px;
      overflow-y: auto;
    }

    /* Buttons */
    .btn-row {
      display: flex;
      gap: 0.75rem;
      flex-wrap: wrap;
    }
    .btn {
      background: var(--md-sys-color-primary);
      color: var(--md-sys-color-on-primary);
      border: none;
      padding: 0.65rem 1.25rem;
      border-radius: 20px;
      font-family: inherit;
      font-weight: 600;
      font-size: 0.9rem;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      transition: all 0.2s;
    }
    .btn:hover {
      background: #7F67BE;
      transform: translateY(-1px);
    }
    .btn-tonal {
      background: var(--md-sys-color-surface-container-high);
      color: var(--md-sys-color-on-surface);
      border: 1px solid var(--md-sys-color-outline-variant);
    }
    .btn-tonal:hover {
      background: #413E47;
    }

    /* Stats Chips */
    .chip-row {
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
    }
    .chip {
      background: var(--md-sys-color-surface-dim);
      border: 1px solid var(--md-sys-color-outline-variant);
      padding: 0.35rem 0.75rem;
      border-radius: 8px;
      font-size: 0.8rem;
      font-family: var(--font-mono);
    }
    .chip.good { color: #81C784; border-color: #388E3C; }
    .chip.warn { color: #FFB74D; border-color: #F57C00; }
    .chip.bad { color: #E57373; border-color: #D32F2F; }

    /* Results list */
    .item-list {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }
    .item-card {
      background: var(--md-sys-color-surface-dim);
      border: 1px solid var(--md-sys-color-outline-variant);
      border-radius: 10px;
      padding: 1rem;
    }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <span>✨ Omnipost Studio</span>
      <span class="brand-badge">Material 3</span>
    </div>
    <div class="status-pill">
      <div class="status-dot"></div>
      <span>API & MCP Engine Live</span>
    </div>
  </header>

  <nav class="tabs-bar">
    <button class="tab-btn active" onclick="switchTab('format')">📝 Formatter & Styles</button>
    <button class="tab-btn" onclick="switchTab('split')">🧵 Thread Splitter</button>
    <button class="tab-btn" onclick="switchTab('hooks')">⚡ Viral Hooks</button>
    <button class="tab-btn" onclick="switchTab('analyze')">📊 Viral Analyzer</button>
    <button class="tab-btn" onclick="switchTab('export')">📅 Campaign Exporter</button>
    <button class="tab-btn" onclick="switchTab('mcp')">🤖 MCP Client Configs</button>
  </nav>

  <main>
    <!-- TAB 1: FORMAT -->
    <div id="tab-format" class="tab-content active">
      <div class="two-col">
        <div class="card">
          <div class="card-title">Input Content</div>
          <div>
            <label>Platform</label>
            <select id="fmt-platform" onchange="runFormat()">
              <option value="twitter">Twitter / X (280 chars)</option>
              <option value="bluesky">Bluesky (300 chars)</option>
              <option value="threads">Meta Threads (500 chars)</option>
              <option value="mastodon">Mastodon (500 chars)</option>
              <option value="linkedin">LinkedIn (3000 chars)</option>
            </select>
          </div>
          <div>
            <label>Unicode Typography Style</label>
            <select id="fmt-style" onchange="runFormat()">
              <option value="normal">Normal (Default)</option>
              <option value="bold">Bold (𝗕𝗼𝗹𝗱)</option>
              <option value="italic">Italic (𝘐𝘵𝘢𝘭𝘪𝘤)</option>
              <option value="bold_italic">Bold Italic (𝘽𝙤𝙡𝙙 𝙄𝙩𝙖𝙡𝙞𝙘)</option>
              <option value="monospace">Monospace (𝙼𝚘𝚗𝚘𝚜𝚙𝚊𝚌𝚎)</option>
              <option value="script">Script (𝒮𝒸𝓇𝒾𝓅𝓉)</option>
              <option value="double_struck">Double Struck (𝔻𝕠𝕦𝕓𝕝𝕖)</option>
              <option value="sans">Sans-Serif (𝖲𝖺𝗇𝗌)</option>
              <option value="underline">Underline (U̲n̲d̲e̲r̲l̲i̲n̲e̲)</option>
              <option value="strikethrough">Strikethrough (S̶t̶r̶i̶k̶e̶)</option>
            </select>
          </div>
          <div>
            <label>Post Text</label>
            <textarea id="fmt-text" placeholder="Write or paste your post here..." oninput="runFormat()">Stop spending 4 hours writing social posts for 5 different platforms.

We built a pure-Python zero-dependency engine that formats, styles, and splits posts in 200ms.</textarea>
          </div>
          <div>
            <label>Append Hashtags (comma separated)</label>
            <input type="text" id="fmt-tags" placeholder="buildinpublic, python, mcp" oninput="runFormat()">
          </div>
        </div>

        <div class="card">
          <div class="card-title">Live Preview & Diagnostics</div>
          <div class="chip-row">
            <div id="fmt-chip-count" class="chip good">0 / 280 chars</div>
            <div id="fmt-chip-words" class="chip">0 words</div>
            <div id="fmt-chip-valid" class="chip good">Valid</div>
          </div>
          <label>Formatted Output</label>
          <div id="fmt-output" class="code-box"></div>
          <div class="btn-row">
            <button class="btn" onclick="copyOutput('fmt-output')">📋 Copy Post</button>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 2: SPLIT -->
    <div id="tab-split" class="tab-content">
      <div class="two-col">
        <div class="card">
          <div class="card-title">Long Copy Input</div>
          <div>
            <label>Character Limit</label>
            <input type="number" id="split-limit" value="280">
          </div>
          <div>
            <label>Numbering Style</label>
            <select id="split-format">
              <option value="fraction">(1/N) Standard</option>
              <option value="fraction_thread">🧵 1/N Thread Header</option>
              <option value="bracket">[1/N] Brackets</option>
              <option value="counter">1. Ordered List</option>
            </select>
          </div>
          <div>
            <label>Full Longform Article / Copy</label>
            <textarea id="split-text" style="min-height: 220px;" placeholder="Paste long article or guide here...">Why we rejected a 300MB node_modules stack for our social automation engine:

Last month, we audited our team's social publishing workflow. We were juggling 4 different SaaS tabs, fighting character count truncations, and fixing broken line breaks on mobile.

Instead of subscribing to another $99/mo tool, we engineered Omnipost:
1/ 100% offline & local-first
2/ Native Model Context Protocol (MCP) server for Claude & Cursor
3/ Material 3 UI Studio served over local HTTP
4/ Automatic Unicode typography styling

Simplicity scales.</textarea>
          </div>
          <button class="btn" onclick="runSplit()">🧵 Split into Thread</button>
        </div>

        <div class="card">
          <div class="card-title">
            <span>Generated Thread</span>
            <span id="split-total-badge" class="chip">0 posts</span>
          </div>
          <div id="split-results" class="item-list"></div>
        </div>
      </div>
    </div>

    <!-- TAB 3: HOOKS -->
    <div id="tab-hooks" class="tab-content">
      <div class="two-col">
        <div class="card">
          <div class="card-title">Viral Hook Generator</div>
          <div>
            <label>Topic / Concept</label>
            <input type="text" id="hook-topic" value="Zero-Dependency Python Tools">
          </div>
          <div>
            <label>Niche / Target Audience</label>
            <input type="text" id="hook-niche" value="Software Engineers">
          </div>
          <div>
            <label>Framework</label>
            <select id="hook-framework">
              <option value="all">All Proven Frameworks</option>
              <option value="contrarian">Contrarian / Unpopular Opinion</option>
              <option value="question">Curiosity Question</option>
              <option value="number_list">Numbered List / Micro-habits</option>
              <option value="curiosity_gap">Curiosity Gap</option>
              <option value="transformation">Zero to Mastery Transformation</option>
              <option value="how_to">How-To Masterclass</option>
              <option value="negative_bias">Costly Mistakes / Negative Bias</option>
              <option value="secret_mistake">Secret Blueprint</option>
              <option value="story_lead">Behind-the-Scenes Story</option>
            </select>
          </div>
          <button class="btn" onclick="runHooks()">⚡ Generate 10 Hooks</button>
        </div>

        <div class="card">
          <div class="card-title">Generated Viral Hooks</div>
          <div id="hooks-results" class="item-list"></div>
        </div>
      </div>
    </div>

    <!-- TAB 4: ANALYZE -->
    <div id="tab-analyze" class="tab-content">
      <div class="two-col">
        <div class="card">
          <div class="card-title">Engagement Analyzer</div>
          <div>
            <label>Target Platform</label>
            <select id="ana-platform">
              <option value="twitter">Twitter / X</option>
              <option value="linkedin">LinkedIn</option>
              <option value="threads">Meta Threads</option>
              <option value="bluesky">Bluesky</option>
            </select>
          </div>
          <div>
            <label>Post Content to Analyze</label>
            <textarea id="ana-text" style="min-height: 200px;">Most developers think building AI tools requires 50 npm packages and a complex backend.

They are completely wrong.

Here is how we built a standalone MCP server with 0 dependencies in Python:
- Built-in JSON-RPC 2.0 stdio loop
- ThreadingHTTPServer for Material 3 UI
- Pure Unicode math mapping

What is your favorite stdlib trick? Drop it below 👇</textarea>
          </div>
          <button class="btn" onclick="runAnalyze()">📊 Score Post</button>
        </div>

        <div class="card">
          <div class="card-title">
            <span>Viral Readiness Score</span>
            <span id="ana-score-badge" class="chip good" style="font-size: 1.1rem;">-- / 100</span>
          </div>
          <div id="ana-metrics" class="chip-row"></div>
          <div class="card-title" style="font-size: 0.95rem; margin-top: 0.5rem;">Actionable Recommendations</div>
          <div id="ana-tips" class="item-list"></div>
        </div>
      </div>
    </div>

    <!-- TAB 5: EXPORT -->
    <div id="tab-export" class="tab-content">
      <div class="two-col">
        <div class="card">
          <div class="card-title">Campaign Exporter</div>
          <div>
            <label>Export Format</label>
            <select id="exp-format">
              <option value="json">JSON Bundle (Full Schema)</option>
              <option value="csv">CSV - Buffer Format</option>
              <option value="csv-hootsuite">CSV - Hootsuite Format</option>
              <option value="csv-typefully">CSV - Typefully Format</option>
              <option value="markdown">Markdown Calendar Table</option>
              <option value="markdown-cards">Markdown Post Cards</option>
              <option value="txt">Raw Plain Text Queue</option>
            </select>
          </div>
          <div class="btn-row">
            <button class="btn" onclick="runExportSample()">📦 Load Demo Campaign</button>
          </div>
        </div>

        <div class="card">
          <div class="card-title">Export Preview</div>
          <div id="exp-output" class="code-box"></div>
          <div class="btn-row">
            <button class="btn" onclick="copyOutput('exp-output')">📋 Copy Export</button>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 6: MCP CONFIGS -->
    <div id="tab-mcp" class="tab-content">
      <div class="card">
        <div class="card-title">Model Context Protocol (MCP) Client Integrations</div>
        <p style="color: var(--md-sys-color-on-surface-variant); font-size: 0.9rem;">
          Connect your local Omnipost MCP server directly to Claude Desktop, Cursor, Cline, or Zed to give your AI assistants native social posting & campaign tools.
        </p>
        <div class="two-col">
          <div>
            <label>Claude Desktop (~/.config/Claude/claude_desktop_config.json)</label>
            <div id="mcp-claude" class="code-box">Loading...</div>
          </div>
          <div>
            <label>Cursor (.cursor/mcp.json)</label>
            <div id="mcp-cursor" class="code-box">Loading...</div>
          </div>
        </div>
        <div class="two-col" style="margin-top: 1rem;">
          <div>
            <label>Cline (cline_mcp_settings.json)</label>
            <div id="mcp-cline" class="code-box">Loading...</div>
          </div>
          <div>
            <label>Zed (settings.json)</label>
            <div id="mcp-zed" class="code-box">Loading...</div>
          </div>
        </div>
      </div>
    </div>
  </main>

  <script>
    function switchTab(tabId) {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      event.target.classList.add('active');
      document.getElementById('tab-' + tabId).classList.add('active');
      if (tabId === 'mcp') loadMcpConfig();
    }

    async function runFormat() {
      const text = document.getElementById('fmt-text').value;
      const platform = document.getElementById('fmt-platform').value;
      const style = document.getElementById('fmt-style').value;
      const tagsStr = document.getElementById('fmt-tags').value;
      const hashtags = tagsStr ? tagsStr.split(',').map(s => s.trim()).filter(Boolean) : [];

      try {
        const res = await fetch('/api/format', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({text, platform, style, hashtags})
        });
        const data = await res.json();
        document.getElementById('fmt-output').innerText = data.text || '';
        
        const countChip = document.getElementById('fmt-chip-count');
        countChip.innerText = `${data.char_count} / ${data.char_limit} chars`;
        countChip.className = 'chip ' + (data.is_valid ? 'good' : 'bad');

        document.getElementById('fmt-chip-words').innerText = `${data.word_count} words`;
        
        const validChip = document.getElementById('fmt-chip-valid');
        validChip.innerText = data.is_valid ? '✅ Valid' : `⚠️ Exceeds by ${-data.remaining_chars}`;
        validChip.className = 'chip ' + (data.is_valid ? 'good' : 'bad');
      } catch (e) {
        console.error(e);
      }
    }

    async function runSplit() {
      const text = document.getElementById('split-text').value;
      const limit = parseInt(document.getElementById('split-limit').value) || 280;
      const numbering_format = document.getElementById('split-format').value;

      try {
        const res = await fetch('/api/split', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({text, limit, numbering_format, numbering: true})
        });
        const data = await res.json();
        document.getElementById('split-total-badge').innerText = `${data.total_posts} posts`;
        const container = document.getElementById('split-results');
        container.innerHTML = '';
        data.posts.forEach((p, idx) => {
          const div = document.createElement('div');
          div.className = 'item-card';
          div.innerHTML = `<div style="font-weight:700; color:#D0BCFF; margin-bottom:0.4rem;">Post ${idx+1}/${data.total_posts} <span style="font-size:0.8rem; color:#888;">(${p.char_count} chars)</span></div><pre style="white-space:pre-wrap; font-family:var(--font-main); font-size:0.9rem;">${p.content}</pre>`;
          container.appendChild(div);
        });
      } catch (e) {
        console.error(e);
      }
    }

    async function runHooks() {
      const topic = document.getElementById('hook-topic').value;
      const niche = document.getElementById('hook-niche').value;
      const framework = document.getElementById('hook-framework').value;

      try {
        const res = await fetch('/api/hooks', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({topic, niche, framework, count: 10})
        });
        const data = await res.json();
        const container = document.getElementById('hooks-results');
        container.innerHTML = '';
        data.hooks.forEach(h => {
          const div = document.createElement('div');
          div.className = 'item-card';
          div.innerHTML = `<div style="font-size:0.75rem; text-transform:uppercase; color:#D0BCFF; font-weight:700;">${h.framework}</div><div style="margin-top:0.3rem; font-size:0.95rem;">${h.hook}</div>`;
          container.appendChild(div);
        });
      } catch (e) {
        console.error(e);
      }
    }

    async function runAnalyze() {
      const text = document.getElementById('ana-text').value;
      const platform = document.getElementById('ana-platform').value;

      try {
        const res = await fetch('/api/analyze', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({text, platform})
        });
        const data = await res.json();
        const badge = document.getElementById('ana-score-badge');
        badge.innerText = `${data.score} / 100 (${data.grade} - ${data.viral_readiness})`;
        badge.className = 'chip ' + (data.score >= 75 ? 'good' : (data.score >= 50 ? 'warn' : 'bad'));

        const metricsBox = document.getElementById('ana-metrics');
        metricsBox.innerHTML = `
          <div class="chip">Reading Ease: ${data.metrics.flesch_reading_ease}</div>
          <div class="chip">Grade Level: ${data.metrics.reading_grade_level}</div>
          <div class="chip">Read Time: ${data.metrics.reading_time_sec}s</div>
          <div class="chip">Power Words: ${data.metrics.power_words_count}</div>
          <div class="chip">CTA Detected: ${data.metrics.has_cta ? 'Yes' : 'No'}</div>
        `;

        const tipsBox = document.getElementById('ana-tips');
        tipsBox.innerHTML = '';
        data.recommendations.forEach(r => {
          const div = document.createElement('div');
          div.className = 'item-card';
          div.innerText = '💡 ' + r;
          tipsBox.appendChild(div);
        });
      } catch (e) {
        console.error(e);
      }
    }

    async function runExportSample() {
      const fmtVal = document.getElementById('exp-format').value;
      let format = 'json';
      let preset = 'buffer';
      let view = 'calendar';

      if (fmtVal === 'csv') { format = 'csv'; preset = 'buffer'; }
      else if (fmtVal === 'csv-hootsuite') { format = 'csv'; preset = 'hootsuite'; }
      else if (fmtVal === 'csv-typefully') { format = 'csv'; preset = 'typefully'; }
      else if (fmtVal === 'markdown') { format = 'md'; view = 'table'; }
      else if (fmtVal === 'markdown-cards') { format = 'md'; view = 'cards'; }
      else if (fmtVal === 'txt') { format = 'txt'; }

      try {
        const res = await fetch('/api/export', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            campaign: 'sample',
            format,
            preset,
            view
          })
        });
        const data = await res.json();
        document.getElementById('exp-output').innerText = data.content;
      } catch (e) {
        console.error(e);
      }
    }

    async function loadMcpConfig() {
      try {
        const res = await fetch('/api/mcp/config');
        const data = await res.json();
        document.getElementById('mcp-claude').innerText = JSON.stringify(data.claude_desktop, null, 2);
        document.getElementById('mcp-cursor').innerText = JSON.stringify(data.cursor, null, 2);
        document.getElementById('mcp-cline').innerText = JSON.stringify(data.cline, null, 2);
        document.getElementById('mcp-zed').innerText = JSON.stringify(data.zed, null, 2);
      } catch (e) {
        console.error(e);
      }
    }

    function copyOutput(elementId) {
      const text = document.getElementById(elementId).innerText;
      navigator.clipboard.writeText(text);
      alert('Copied to clipboard!');
    }

    // Initialize default formatter view
    window.addEventListener('DOMContentLoaded', () => {
      runFormat();
      runSplit();
      runHooks();
      runAnalyze();
      runExportSample();
    });
  </script>
</body>
</html>
"""


class OmnipostRequestHandler(http.server.BaseHTTPRequestHandler):
    """HTTP Request Handler for Omnipost UI Studio & REST APIs."""

    def log_message(self, format: str, *args: Any) -> None:
        """Quiet logging during tests unless DEBUG is set."""
        if os.environ.get("OMNIPOST_DEBUG"):
            super().log_message(format, *args)

    def _send_cors_headers(self) -> None:
        """Send standard Cross-Origin Resource Sharing headers."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

    def _send_json(self, data: Any, status: int = 200) -> None:
        """Send JSON response with CORS headers."""
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, message: str, status: int = 400) -> None:
        """Send JSON error response."""
        self._send_json({"error": message, "status": status}, status=status)

    def do_OPTIONS(self) -> None:
        """Handle CORS pre-flight requests."""
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        """Handle GET requests for static files and REST endpoints."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        if not path:
            path = "/"

        # API Endpoints
        if path == "/api/health":
            self._send_json({
                "status": "ok",
                "service": "omnipost-studio",
                "version": "1.0.0",
                "timestamp": sys.version,
            })
            return

        elif path == "/api/mcp/config":
            configs = get_client_configs()
            self._send_json(configs)
            return

        elif path == "/api/diagnostics":
            query = urllib.parse.parse_qs(parsed.query)
            platform_q = query.get("platform", [None])[0]
            diag = get_diagnostics_engine(platform_q)
            self._send_json(diag)
            return

        elif path == "/api/hooks":
            query = urllib.parse.parse_qs(parsed.query)
            topic = query.get("topic", ["Social Media Automation"])[0]
            niche = query.get("niche", ["tech"])[0]
            framework = query.get("framework", ["all"])[0]
            count = int(query.get("count", [10])[0])
            hooks = generate_hooks_engine(topic=topic, niche=niche, framework=framework, count=count)
            self._send_json(hooks)
            return

        elif path == "/api/accessibility":
            query = urllib.parse.parse_qs(parsed.query)
            alt_text = query.get("alt", query.get("alt_text", [""]))[0]
            post_text = query.get("post", query.get("post_text", [""]))[0]
            platform = query.get("platform", ["twitter"])[0]
            res = evaluate_accessibility_suite(alt_text=alt_text, post_text=post_text, platform=platform)
            self._send_json(res)
            return

        # Static File Serving
        self._serve_static(path)

    def do_POST(self) -> None:
        """Handle POST REST API requests."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")

        # Read JSON body
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except json.JSONDecodeError as e:
            self._send_error_json(f"Invalid JSON payload: {str(e)}", 400)
            return

        if path == "/api/format":
            text = payload.get("text", "")
            platform = payload.get("platform", "twitter")
            style = payload.get("style", "normal")
            hashtags = payload.get("hashtags")
            trim = payload.get("trim", True)
            res = format_post_engine(text=text, platform=platform, style=style, hashtags=hashtags, trim=trim)
            self._send_json(res)

        elif path == "/api/split":
            text = payload.get("text", "")
            limit = payload.get("limit", 280)
            platform = payload.get("platform", "twitter")
            numbering = payload.get("numbering", True)
            numbering_format = payload.get("numbering_format", "fraction")
            res = split_thread_engine(
                text=text,
                limit=limit,
                platform=platform,
                numbering=numbering,
                numbering_format=numbering_format,
            )
            self._send_json(res)

        elif path == "/api/hooks":
            topic = payload.get("topic", "AI Tools")
            niche = payload.get("niche", "tech")
            framework = payload.get("framework", "all")
            count = payload.get("count", 10)
            res = generate_hooks_engine(topic=topic, niche=niche, framework=framework, count=count)
            self._send_json(res)

        elif path == "/api/analyze":
            text = payload.get("text", "")
            platform = payload.get("platform", "twitter")
            res = analyze_engagement_engine(text=text, platform=platform)
            self._send_json(res)

        elif path == "/api/export":
            campaign_data = payload.get("campaign", "sample")
            if campaign_data == "sample":
                camp = CampaignExporter.create_sample_campaign()
            else:
                camp = campaign_data

            fmt = payload.get("format", "json")
            preset = payload.get("preset", "buffer")
            view = payload.get("view", "calendar")
            try:
                exported_str = CampaignExporter.export(camp, format=fmt, preset=preset, view=view)
                ext = "md" if fmt in ("md", "markdown") else (fmt if fmt in ("json", "csv", "txt") else "json")
                filename = f"campaign_export.{ext}"
                self._send_json({
                    "content": exported_str,
                    "format": fmt,
                    "preset": preset,
                    "filename": filename,
                })
            except Exception as e:
                self._send_error_json(f"Export failed: {str(e)}", 500)

        elif path == "/api/accessibility":
            alt_text = payload.get("alt", payload.get("alt_text", ""))
            post_text = payload.get("post", payload.get("post_text", ""))
            platform = payload.get("platform", "twitter")
            res = evaluate_accessibility_suite(alt_text=alt_text, post_text=post_text, platform=platform)
            self._send_json(res)

        else:
            self._send_error_json(f"Unknown POST endpoint: {path}", 404)

    def _serve_static(self, path: str) -> None:
        """Serve public directory static assets or fallback to embedded Material 3 UI."""
        public_dir = get_public_dir()

        # Handle root index request
        if path == "/" or path == "/index.html":
            index_path = os.path.join(public_dir, "index.html")
            if os.path.isfile(index_path):
                self._serve_file(index_path, "text/html; charset=utf-8")
            else:
                # Serve embedded Material 3 UI
                body = EMBEDDED_STUDIO_HTML.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(body)
            return

        # Attempt to serve file from public_dir
        rel_path = path.lstrip("/")
        file_path = os.path.normpath(os.path.join(public_dir, rel_path))

        # Security check: ensure path is within public_dir
        if not file_path.startswith(os.path.abspath(public_dir)):
            self._send_error_json("Forbidden", 403)
            return

        if os.path.isfile(file_path):
            mime_type, _ = mimetypes.guess_type(file_path)
            content_type = mime_type or "application/octet-stream"
            self._serve_file(file_path, content_type)
        else:
            self._send_error_json(f"Not found: {path}", 404)

    def _serve_file(self, file_path: str, content_type: str) -> None:
        """Read and serve a local static file."""
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self._send_error_json(f"Error reading file: {str(e)}", 500)


class OmnipostServer:
    """Threaded HTTP Server for Omnipost Studio."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8086):
        self.host = host
        self.port = port
        self.httpd: Optional[http.server.ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    @property
    def url(self) -> str:
        """Returns the base URL of the running server."""
        display_host = "127.0.0.1" if self.host in ("0.0.0.0", "") else self.host
        return f"http://{display_host}:{self.port}"

    def start(self, background: bool = True) -> None:
        """Start the HTTP server on specified host and port."""
        server_address = (self.host, self.port)
        self.httpd = http.server.ThreadingHTTPServer(server_address, OmnipostRequestHandler)
        # Update port in case 0 was passed for dynamic port allocation
        self.port = self.httpd.server_port

        if background:
            self._thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
            self._thread.start()
        else:
            try:
                self.httpd.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                self.stop()

    def stop(self) -> None:
        """Shutdown the running HTTP server."""
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None


def run_server(host: str = "0.0.0.0", port: int = 8086, open_browser: bool = False) -> None:
    """Entry point for CLI command `omnipost serve`."""
    server = OmnipostServer(host=host, port=port)
    print(f"\n✨ Omnipost Studio live at: {server.url}")
    print(f"📊 REST APIs: {server.url}/api/health")
    print(f"🤖 MCP Configs: {server.url}/api/mcp/config")
    print("Press Ctrl+C to stop.\n")

    if open_browser:
        import webbrowser
        try:
            webbrowser.open(server.url)
        except Exception:
            pass

    try:
        server.start(background=False)
    except KeyboardInterrupt:
        print("\nStopping Omnipost Studio server...")
    finally:
        server.stop()
