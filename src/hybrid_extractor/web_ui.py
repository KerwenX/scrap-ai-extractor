from __future__ import annotations


def build_web_ui_html() -> str:
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>混合网页解析器</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Noto+Sans+SC:wght@400;500;600;700&display=swap');

    :root {
      --bg: #f3f7fb;
      --panel: rgba(255, 255, 255, 0.92);
      --panel-strong: #ffffff;
      --line: rgba(15, 23, 42, 0.08);
      --line-strong: rgba(30, 64, 175, 0.18);
      --text: #10233f;
      --muted: #5f6f86;
      --primary: #1e40af;
      --primary-2: #3b82f6;
      --success: #0f766e;
      --warning: #b7791f;
      --danger: #b42318;
      --shadow: 0 18px 48px rgba(15, 23, 42, 0.09);
      --radius-xl: 26px;
      --radius-lg: 18px;
      --radius-md: 14px;
      --sans: "Noto Sans SC", "Microsoft YaHei", sans-serif;
      --mono: "Fira Code", Consolas, monospace;
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: var(--sans);
      color: var(--text);
      background:
        radial-gradient(circle at top right, rgba(59, 130, 246, 0.14), transparent 24%),
        radial-gradient(circle at top left, rgba(245, 158, 11, 0.10), transparent 18%),
        var(--bg);
    }
    button, input, textarea, select { font: inherit; }
    .app {
      max-width: 1540px;
      margin: 0 auto;
      padding: 18px 16px 28px;
    }
    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 18px 22px;
      border: 1px solid var(--line);
      border-radius: var(--radius-xl);
      background: rgba(255,255,255,0.82);
      box-shadow: var(--shadow);
      backdrop-filter: blur(12px);
      margin-bottom: 16px;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 14px;
      min-width: 0;
    }
    .brand-mark {
      width: 48px;
      height: 48px;
      border-radius: 16px;
      color: white;
      display: grid;
      place-items: center;
      background: linear-gradient(135deg, var(--primary), var(--primary-2));
      box-shadow: 0 14px 30px rgba(30, 64, 175, 0.24);
      flex: 0 0 auto;
    }
    .brand h1 {
      margin: 0;
      font-size: clamp(24px, 3vw, 34px);
      line-height: 1;
    }
    .brand p {
      margin: 6px 0 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.6;
    }
    .badge-row {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      justify-content: flex-end;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 9px 13px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      border: 1px solid transparent;
      white-space: nowrap;
    }
    .badge.primary { color: var(--primary); background: #dbeafe; border-color: rgba(59,130,246,.2); }
    .badge.success { color: var(--success); background: #ccfbf1; border-color: rgba(15,118,110,.18); }
    .badge.warning { color: var(--warning); background: #fef3c7; border-color: rgba(245,158,11,.18); }
    .hero {
      display: grid;
      grid-template-columns: minmax(0, 1.45fr) minmax(320px, 0.9fr);
      gap: 16px;
      margin-bottom: 16px;
    }
    .card {
      border: 1px solid var(--line);
      border-radius: var(--radius-xl);
      background: var(--panel);
      box-shadow: var(--shadow);
      backdrop-filter: blur(10px);
      min-width: 0;
    }
    .hero-main {
      padding: 24px;
      position: relative;
      overflow: hidden;
    }
    .hero-main::after {
      content: "";
      position: absolute;
      width: 240px;
      height: 240px;
      right: -70px;
      top: -70px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(59,130,246,.18), transparent 68%);
    }
    .hero-kicker {
      display: inline-flex;
      padding: 8px 12px;
      border-radius: 999px;
      background: #dbeafe;
      color: var(--primary);
      font-size: 12px;
      font-weight: 700;
      margin-bottom: 16px;
    }
    .hero-main h2 {
      margin: 0;
      font-size: clamp(24px, 3vw, 36px);
      line-height: 1.08;
      max-width: 18ch;
    }
    .hero-main p {
      margin: 14px 0 0;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.75;
      max-width: 64ch;
    }
    .mini-grid, .stat-grid, .metric-grid, .library-grid {
      display: grid;
      gap: 12px;
    }
    .mini-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); margin-top: 18px; }
    .mini {
      border: 1px solid var(--line);
      border-radius: 18px;
      background: rgba(255,255,255,.78);
      padding: 14px;
      min-width: 0;
    }
    .mini small, .metric small, .stat small {
      display: block;
      margin-bottom: 6px;
      color: var(--muted);
      font-size: 11px;
      letter-spacing: .05em;
      text-transform: uppercase;
    }
    .mini strong, .metric strong, .stat strong {
      display: block;
      line-height: 1.35;
      word-break: break-word;
    }
    .hero-side {
      padding: 22px;
      background: linear-gradient(180deg, #0f172a, #1e293b);
      color: white;
    }
    .hero-side h3 { margin: 0 0 10px; font-size: 18px; }
    .hero-side p { margin: 0 0 16px; color: rgba(226,232,240,.8); font-size: 13px; line-height: 1.7; }
    .stat-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .stat {
      padding: 16px;
      border-radius: 18px;
      background: rgba(255,255,255,.06);
      border: 1px solid rgba(255,255,255,.08);
      min-width: 0;
    }
    .stat strong { font-family: var(--mono); font-size: 22px; }
    .workspace {
      display: grid;
      grid-template-columns: minmax(360px, 420px) minmax(0, 1fr);
      gap: 16px;
      align-items: start;
      margin-bottom: 16px;
    }
    .stack { display: grid; gap: 16px; min-width: 0; }
    .panel { padding: 20px; min-width: 0; overflow: hidden; }
    .panel-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 14px;
    }
    .panel-head h2, .panel-head h3 { margin: 0; font-size: 18px; }
    .subtle { color: var(--muted); font-size: 12px; line-height: 1.6; }
    .field { margin-bottom: 14px; }
    .field label {
      display: block;
      margin-bottom: 8px;
      color: var(--muted);
      font-weight: 600;
      font-size: 13px;
    }
    input[type="text"], textarea, select {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 16px;
      background: rgba(255,255,255,.92);
      padding: 12px 14px;
      color: var(--text);
      outline: none;
      transition: border-color .18s ease, box-shadow .18s ease;
    }
    textarea {
      resize: vertical;
      min-height: 130px;
      line-height: 1.65;
    }
    #htmlInput {
      min-height: 250px;
      font-family: var(--mono);
      font-size: 12px;
    }
    input:focus-visible, textarea:focus-visible, select:focus-visible, button:focus-visible {
      border-color: rgba(59,130,246,.38);
      box-shadow: 0 0 0 4px rgba(59,130,246,.12);
      outline: none;
    }
    .actions, .toolbar, .filters, .pager, .row-actions {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
    }
    .actions { margin-top: 18px; }
    .spacer { flex: 1 1 auto; }
    button, .button-like {
      border: 1px solid transparent;
      border-radius: 999px;
      padding: 10px 16px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      cursor: pointer;
      text-decoration: none;
      transition: transform .18s ease, box-shadow .18s ease, background .18s ease, border-color .18s ease;
    }
    button:hover, .button-like:hover { transform: translateY(-1px); }
    .primary {
      color: white;
      background: linear-gradient(135deg, var(--primary), var(--primary-2));
      box-shadow: 0 14px 28px rgba(30,64,175,.2);
    }
    .secondary, .ghost, .button-like {
      color: var(--text);
      background: rgba(255,255,255,.92);
      border-color: var(--line);
    }
    .warning-button {
      color: #8a5a09;
      background: #fef3c7;
      border-color: rgba(245,158,11,.18);
    }
    .upload {
      position: relative;
      overflow: hidden;
    }
    .upload input {
      position: absolute;
      inset: 0;
      opacity: 0;
      cursor: pointer;
    }
    .status-line {
      min-height: 22px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.6;
    }
    .right-grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 320px;
      gap: 16px;
      align-items: start;
    }
    .result-shell, .detail-shell, .rail-shell {
      display: grid;
      gap: 16px;
      min-width: 0;
    }
    .metric-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    .metric {
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 12px 14px;
      background: rgba(255,255,255,.86);
      min-width: 0;
    }
    .metric strong {
      font-family: var(--mono);
      font-size: 15px;
      overflow-wrap: anywhere;
    }
    pre {
      margin: 0;
      border-radius: 20px;
      background: linear-gradient(180deg, #0f172a, #111c33);
      color: #dbeafe;
      padding: 18px;
      min-height: 260px;
      max-height: 440px;
      overflow: auto;
      font-size: 12px;
      line-height: 1.65;
      font-family: var(--mono);
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }
    .summary-card, .rail-card, .empty {
      border: 1px solid var(--line);
      border-radius: 18px;
      background: rgba(255,255,255,.76);
      padding: 14px 16px;
    }
    .summary-title {
      margin-bottom: 10px;
      font-size: 14px;
      font-weight: 700;
    }
    .summary-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 10px;
    }
    .summary-item {
      border: 1px solid rgba(30,64,175,.08);
      border-radius: 14px;
      background: rgba(239,246,255,.54);
      padding: 10px 12px;
      min-width: 0;
    }
    .summary-item small {
      display: block;
      margin-bottom: 6px;
      font-size: 11px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: .05em;
    }
    .summary-item div {
      font-size: 13px;
      line-height: 1.55;
      overflow-wrap: anywhere;
    }
    .progress-list {
      list-style: none;
      padding: 0;
      margin: 0;
      display: grid;
      gap: 10px;
      max-height: 480px;
      overflow: auto;
    }
    .progress-item {
      border: 1px solid var(--line);
      border-left: 4px solid rgba(59,130,246,.5);
      border-radius: 16px;
      background: rgba(255,255,255,.8);
      padding: 12px 14px;
    }
    .progress-item strong {
      display: block;
      margin-bottom: 5px;
      font-size: 13px;
    }
    .progress-item span {
      display: block;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.55;
      overflow-wrap: anywhere;
    }
    .progress-item.success { border-left-color: rgba(15,118,110,.6); }
    .progress-item.error { border-left-color: rgba(180,35,24,.65); }
    .progress-item.warning { border-left-color: rgba(245,158,11,.65); }
    .progress-item.loading { border-left-color: rgba(59,130,246,.65); }
    .library-grid { grid-template-columns: minmax(0,1fr) minmax(0,1fr); }
    .table-wrap {
      border: 1px solid var(--line);
      border-radius: 18px;
      overflow: auto;
      background: rgba(255,255,255,.78);
    }
    table {
      width: 100%;
      min-width: 880px;
      border-collapse: collapse;
    }
    th, td {
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
      text-align: left;
      font-size: 13px;
    }
    th {
      position: sticky;
      top: 0;
      background: rgba(248,250,252,.98);
      color: var(--muted);
      font-size: 11px;
      letter-spacing: .08em;
      text-transform: uppercase;
    }
    tr:last-child td { border-bottom: 0; }
    tr:hover td { background: rgba(239,246,255,.38); }
    .row-title { font-weight: 700; margin-bottom: 4px; overflow-wrap: anywhere; }
    .row-subtitle, .table-meta, .reason-list { color: var(--muted); font-size: 12px; line-height: 1.55; overflow-wrap: anywhere; }
    .checkbox-cell { width: 42px; }
    .pill {
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 5px 10px;
      font-size: 11px;
      font-weight: 700;
    }
    .pill.success { color: var(--success); background: #ccfbf1; }
    .pill.warning { color: var(--warning); background: #fef3c7; }
    .pill.muted { color: var(--muted); background: #e2e8f0; }
    .empty { color: var(--muted); font-size: 13px; line-height: 1.7; }
    .hidden { display: none !important; }
    @media (max-width: 1220px) {
      .workspace, .right-grid, .hero, .library-grid { grid-template-columns: 1fr; }
      .metric-grid, .mini-grid { grid-template-columns: 1fr; }
    }
    @media (max-width: 820px) {
      .app { padding: 12px 10px 22px; }
      .topbar { flex-direction: column; align-items: flex-start; }
      .badge-row { justify-content: flex-start; }
      .stat-grid { grid-template-columns: 1fr 1fr; }
    }
  </style>
</head>
<body>
  <div class="app">
    <section class="topbar">
      <div class="brand">
        <div class="brand-mark" aria-hidden="true">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
            <path d="M4 6.5h16M4 12h11M4 17.5h8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
          </svg>
        </div>
        <div>
          <h1>混合网页解析器</h1>
          <p>先命中正式模板，再按规则抽取；模板失效或不存在时，才回退到 LLM。批量任务默认只走模板通道。</p>
        </div>
      </div>
      <div class="badge-row">
        <span class="badge primary" id="modeBadge">当前模式：待命</span>
        <span class="badge primary" id="lastRunBadge">最近执行：未开始</span>
        <span class="badge warning" id="resultStatusBadge">结果状态：待命</span>
      </div>
    </section>

    <section class="hero">
      <div class="card hero-main">
        <div class="hero-kicker">Template-first / LLM fallback</div>
        <h2>把网页解析流程收敛成可复用、可固化、可批量运行的服务。</h2>
        <p>单条解析支持自动模板命中和 LLM 回退；批量解析只使用正式模板，并将每条结果连同 URL 写入 JSONL 文件，方便离线回放、审计和迁移到其他机器。</p>
        <div class="mini-grid">
          <div class="mini">
            <small>输入来源</small>
            <strong id="inputSourceStat">手动粘贴</strong>
          </div>
          <div class="mini">
            <small>抽取执行器</small>
            <strong id="extractorTypeStat">未执行</strong>
          </div>
          <div class="mini">
            <small>模板命中</small>
            <strong id="templateHitStat">未命中</strong>
          </div>
        </div>
      </div>
      <div class="card hero-side">
        <h3>运行概览</h3>
        <p>左侧负责输入与触发，右侧同步展示结构化结果、执行明细和模板库状态。无论是单条还是批量，都能看清当前到底走了模板还是走了 LLM。</p>
        <div class="stat-grid">
          <div class="stat">
            <small>正式模板</small>
            <strong id="templateCountStat">0</strong>
          </div>
          <div class="stat">
            <small>候选模板</small>
            <strong id="candidateCountStat">0</strong>
          </div>
          <div class="stat">
            <small>HTML 大小</small>
            <strong id="htmlSizeStat">0 KB</strong>
          </div>
          <div class="stat">
            <small>已选模板</small>
            <strong id="selectedTemplateStat">0</strong>
          </div>
        </div>
      </div>
    </section>

    <section class="workspace">
      <div class="stack">
        <div class="card panel">
          <div class="panel-head">
            <div>
              <h2>单条解析</h2>
              <div class="subtle">普通单条解析默认是自动模式，可命中模板，也可在必要时回退到 LLM。</div>
            </div>
          </div>
          <div class="field">
            <label for="urlInput">页面 URL</label>
            <input id="urlInput" type="text" placeholder="https://example.com/article/123" />
          </div>
          <div class="field">
            <label for="promptInput">抽取需求</label>
            <textarea id="promptInput">提取页面中与用户需求最相关的结构化信息，并尽量输出中文字段名和中文值。</textarea>
          </div>
          <div class="field">
            <label for="htmlInput">网页源码</label>
            <textarea id="htmlInput" placeholder="粘贴 HTML 源码，或使用下方按钮导入本地 HTML 文件"></textarea>
          </div>
          <div class="actions">
            <button class="primary" id="extractBtn" type="button">开始解析</button>
            <label class="button-like upload" for="fileInput">导入 HTML 文件
              <input id="fileInput" type="file" accept=".html,.htm,.txt" />
            </label>
            <button class="ghost" id="sampleBtn" type="button">填充示例</button>
            <button class="ghost" id="clearBtn" type="button">清空输入</button>
          </div>
          <div class="status-line" id="statusLine"></div>
        </div>

        <div class="card panel">
          <div class="panel-head">
            <div>
              <h2>批量模板解析</h2>
              <div class="subtle">导入 JSONL 后直接开始。每行必须包含 <code>url</code> 和 <code>html_path</code>，或兼容已有的 <code>file_path</code>。</div>
            </div>
          </div>
          <div class="field">
            <label for="batchPromptInput">批量抽取需求</label>
            <textarea id="batchPromptInput">提取页面中的结构化信息。批量模式仅允许命中正式模板，不使用 LLM。</textarea>
          </div>
          <div class="field">
            <label for="batchOutputPathInput">结果输出路径（可选）</label>
            <input id="batchOutputPathInput" type="text" placeholder="留空则自动输出到 data/batch_results/" />
          </div>
          <div class="actions">
            <label class="button-like upload" for="batchFileInput">导入 JSONL 文件
              <input id="batchFileInput" type="file" accept=".jsonl,.txt,.json" />
            </label>
            <button class="primary" id="batchExtractBtn" type="button">开始批量解析</button>
          </div>
          <div class="status-line" id="batchStatusLine">尚未选择批量映射文件。</div>
        </div>
      </div>

      <div class="stack">
        <div class="right-grid">
          <div class="result-shell">
            <div class="card panel">
              <div class="panel-head">
                <div>
                  <h2>解析结果</h2>
                  <div class="subtle">原始 API 返回会完整展示在此处。</div>
                </div>
              </div>
              <div class="metric-grid">
                <div class="metric">
                  <small>最近输入</small>
                  <strong id="runSourceStat">未执行</strong>
                </div>
                <div class="metric">
                  <small>执行器</small>
                  <strong id="runExtractorStat">未执行</strong>
                </div>
                <div class="metric">
                  <small>模板</small>
                  <strong id="runTemplateStat">未命中</strong>
                </div>
              </div>
              <pre id="resultBox">{
  "message": "执行后会在这里显示 JSON 结果。"
}</pre>
            </div>

            <div class="card panel">
              <div class="panel-head">
                <div>
                  <h2 id="detailTitle">详情面板</h2>
                  <div class="subtle" id="detailSummary">这里会展示模板命中、页面指纹、校验覆盖率和批量输出信息。</div>
                </div>
              </div>
              <div id="detailBox" class="summary-card">
                <div class="summary-title">等待操作</div>
                <div class="summary-grid">
                  <div class="summary-item">
                    <small>状态</small>
                    <div>未执行</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="rail-shell">
            <div class="card panel">
              <div class="panel-head">
                <div>
                  <h3>解析进度</h3>
                  <div class="subtle">这里会显示文件导入、模板命中、LLM 回退和结果落盘等事件。</div>
                </div>
                <button class="ghost" id="clearProgressBtn" type="button">清空进度</button>
              </div>
              <ul class="progress-list" id="progressList"></ul>
            </div>
          </div>
        </div>

        <div class="library-grid">
          <div class="card panel">
            <div class="panel-head">
              <div>
                <h2>正式模板</h2>
                <div class="subtle">可搜索、分页、批量删除。</div>
              </div>
            </div>
            <div class="filters">
              <input id="templateSearch" type="text" placeholder="搜索 template_id / site_id / template_key" />
              <select id="templateStatusFilter">
                <option value="">全部状态</option>
                <option value="active">active</option>
                <option value="deprecated">deprecated</option>
                <option value="archived">archived</option>
                <option value="draft">draft</option>
              </select>
              <select id="templatePageSize">
                <option value="10">每页 10 条</option>
                <option value="20">每页 20 条</option>
                <option value="50">每页 50 条</option>
              </select>
            </div>
            <div class="toolbar">
              <button class="ghost" id="refreshTemplatesBtn" type="button">刷新</button>
              <button class="warning-button" id="deleteSelectedTemplatesBtn" type="button">删除选中</button>
              <div class="spacer"></div>
              <div class="table-meta" id="templateMeta">共 0 个模板</div>
            </div>
            <div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th class="checkbox-cell"><input type="checkbox" id="selectAllTemplates" /></th>
                    <th>模板</th>
                    <th>站点与场景</th>
                    <th>状态</th>
                    <th>版本</th>
                    <th>必填字段</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody id="templatesTableBody"></tbody>
              </table>
            </div>
            <div class="pager" style="margin-top:12px;">
              <button class="ghost" id="templatePrevBtn" type="button">上一页</button>
              <div class="table-meta" id="templatePagerText">第 1 / 1 页</div>
              <button class="ghost" id="templateNextBtn" type="button">下一页</button>
            </div>
          </div>

          <div class="card panel">
            <div class="panel-head">
              <div>
                <h2>候选模板</h2>
                <div class="subtle">由 LLM 成功抽取后自动固化的候选项。</div>
              </div>
            </div>
            <div class="filters">
              <input id="candidateSearch" type="text" placeholder="搜索 candidate_id / site_id / source_url" />
              <select id="candidatePageSize">
                <option value="10">每页 10 条</option>
                <option value="20">每页 20 条</option>
                <option value="50">每页 50 条</option>
              </select>
            </div>
            <div class="toolbar">
              <button class="ghost" id="refreshCandidatesBtn" type="button">刷新</button>
              <div class="spacer"></div>
              <div class="table-meta" id="candidateMeta">共 0 个候选模板</div>
            </div>
            <div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>候选 ID</th>
                    <th>站点与场景</th>
                    <th>可晋升性</th>
                    <th>字段</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody id="candidatesTableBody"></tbody>
              </table>
            </div>
            <div class="pager" style="margin-top:12px;">
              <button class="ghost" id="candidatePrevBtn" type="button">上一页</button>
              <div class="table-meta" id="candidatePagerText">第 1 / 1 页</div>
              <button class="ghost" id="candidateNextBtn" type="button">下一页</button>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>

  <script>
    const state = {
      templates: [],
      candidates: [],
      selectedTemplateIds: new Set(),
      templatePage: 1,
      candidatePage: 1,
      importedFileName: "",
      batchFileName: "",
      batchFileContent: "",
      lastResponse: null
    };

    const urlInput = document.getElementById("urlInput");
    const promptInput = document.getElementById("promptInput");
    const htmlInput = document.getElementById("htmlInput");
    const extractBtn = document.getElementById("extractBtn");
    const sampleBtn = document.getElementById("sampleBtn");
    const clearBtn = document.getElementById("clearBtn");
    const fileInput = document.getElementById("fileInput");
    const resultBox = document.getElementById("resultBox");
    const detailTitle = document.getElementById("detailTitle");
    const detailSummary = document.getElementById("detailSummary");
    const detailBox = document.getElementById("detailBox");
    const progressList = document.getElementById("progressList");
    const statusLine = document.getElementById("statusLine");
    const batchStatusLine = document.getElementById("batchStatusLine");
    const batchPromptInput = document.getElementById("batchPromptInput");
    const batchOutputPathInput = document.getElementById("batchOutputPathInput");
    const batchFileInput = document.getElementById("batchFileInput");
    const batchExtractBtn = document.getElementById("batchExtractBtn");
    const modeBadge = document.getElementById("modeBadge");
    const lastRunBadge = document.getElementById("lastRunBadge");
    const resultStatusBadge = document.getElementById("resultStatusBadge");
    const templateCountStat = document.getElementById("templateCountStat");
    const candidateCountStat = document.getElementById("candidateCountStat");
    const htmlSizeStat = document.getElementById("htmlSizeStat");
    const selectedTemplateStat = document.getElementById("selectedTemplateStat");
    const inputSourceStat = document.getElementById("inputSourceStat");
    const extractorTypeStat = document.getElementById("extractorTypeStat");
    const templateHitStat = document.getElementById("templateHitStat");
    const runSourceStat = document.getElementById("runSourceStat");
    const runExtractorStat = document.getElementById("runExtractorStat");
    const runTemplateStat = document.getElementById("runTemplateStat");
    const clearProgressBtn = document.getElementById("clearProgressBtn");

    const templateSearch = document.getElementById("templateSearch");
    const templateStatusFilter = document.getElementById("templateStatusFilter");
    const templatePageSize = document.getElementById("templatePageSize");
    const templateMeta = document.getElementById("templateMeta");
    const templatePagerText = document.getElementById("templatePagerText");
    const templatePrevBtn = document.getElementById("templatePrevBtn");
    const templateNextBtn = document.getElementById("templateNextBtn");
    const selectAllTemplates = document.getElementById("selectAllTemplates");
    const templatesTableBody = document.getElementById("templatesTableBody");

    const candidateSearch = document.getElementById("candidateSearch");
    const candidatePageSize = document.getElementById("candidatePageSize");
    const candidateMeta = document.getElementById("candidateMeta");
    const candidatePagerText = document.getElementById("candidatePagerText");
    const candidatePrevBtn = document.getElementById("candidatePrevBtn");
    const candidateNextBtn = document.getElementById("candidateNextBtn");
    const candidatesTableBody = document.getElementById("candidatesTableBody");

    function escapeHtml(value) {
      return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
    }

    function requestJson(url, options = {}) {
      return fetch(url, options).then(async (response) => {
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(payload.error || payload.details || response.statusText);
        }
        return payload;
      });
    }

    function requestNoContent(url, options = {}) {
      return fetch(url, options).then(async (response) => {
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(payload.error || payload.details || response.statusText);
        }
        return payload;
      });
    }

    function paginate(items, page, pageSize) {
      const totalPages = Math.max(1, Math.ceil(items.length / pageSize));
      const currentPage = Math.min(Math.max(page, 1), totalPages);
      const start = (currentPage - 1) * pageSize;
      return {
        items: items.slice(start, start + pageSize),
        page: currentPage,
        totalPages
      };
    }

    function pushProgress(title, message, tone = "loading") {
      const item = document.createElement("li");
      item.className = `progress-item ${tone}`;
      item.innerHTML = `<strong>${escapeHtml(title)}</strong><span>${escapeHtml(message)}</span>`;
      progressList.prepend(item);
    }

    function pushResponseProgress(response) {
      const extractor = response.extractor_type || "unknown";
      const templateId = response.template_id || "未命中";
      const status = response.status === "success" ? "success" : "error";
      pushProgress("解析完成", `执行器：${extractor}；模板：${templateId}；状态：${response.status}`, status);

      if (extractor === "deterministic") {
        pushProgress("命中正式模板", templateId, "success");
      } else if (extractor === "llm" || extractor === "hybrid") {
        pushProgress("进入 LLM 回退", `当前执行器：${extractor}`, "warning");
      } else {
        pushProgress("未命中模板", "本次没有可用的正式模板。", "warning");
      }
    }

    function resetProgress() {
      progressList.innerHTML = "";
    }

    function setStatus(message, tone = "idle") {
      statusLine.textContent = message;
      if (tone === "success") {
        statusLine.style.color = "var(--success)";
      } else if (tone === "error") {
        statusLine.style.color = "var(--danger)";
      } else {
        statusLine.style.color = "var(--muted)";
      }
    }

    function setBatchStatus(message, tone = "idle") {
      batchStatusLine.textContent = message;
      if (tone === "success") {
        batchStatusLine.style.color = "var(--success)";
      } else if (tone === "error") {
        batchStatusLine.style.color = "var(--danger)";
      } else {
        batchStatusLine.style.color = "var(--muted)";
      }
    }

    function updateRunBadges(modeText, resultText, statusText) {
      modeBadge.textContent = `当前模式：${modeText || "待命"}`;
      lastRunBadge.textContent = `最近执行：${resultText || "未开始"}`;
      resultStatusBadge.textContent = `结果状态：${statusText || "待命"}`;
      resultStatusBadge.className = `badge ${statusText === "成功" ? "success" : statusText === "失败" ? "warning" : "primary"}`;
    }

    function updateHeroStats() {
      templateCountStat.textContent = String(state.templates.length);
      candidateCountStat.textContent = String(state.candidates.length);
      selectedTemplateStat.textContent = String(state.selectedTemplateIds.size);
      htmlSizeStat.textContent = `${Math.max(0, Math.round((htmlInput.value || "").length / 1024))} KB`;
      inputSourceStat.textContent = state.importedFileName ? `文件：${state.importedFileName}` : "手动粘贴";
      const extractor = state.lastResponse?.extractor_type || "未执行";
      extractorTypeStat.textContent = extractor;
      runExtractorStat.textContent = extractor;
      const templateId = state.lastResponse?.template_id || "未命中";
      templateHitStat.textContent = templateId;
      runTemplateStat.textContent = templateId;
      runSourceStat.textContent = state.batchFileName ? `批量：${state.batchFileName}` : (state.importedFileName ? `单条：${state.importedFileName}` : "手动输入");
    }

    function buildDetailSummary(payload) {
      const match = payload.template_match || payload.debug_trace?.template_match;
      const classification = payload.classification || payload.debug_trace?.classification;
      const validation = payload.validation_report || payload.debug_trace?.deterministic_validation || payload.debug_trace?.llm_validation;
      const fingerprint = payload.fingerprint || payload.debug_trace?.fingerprint;
      const items = [];

      if (classification) {
        items.push({ label: "站点", value: classification.site_id || "unknown" });
        items.push({ label: "页面类型", value: classification.page_type || "unknown" });
        items.push({ label: "场景", value: classification.scenario || "unknown" });
      }
      if (match) {
        items.push({ label: "模板", value: match.template_id || "未命中" });
        items.push({ label: "匹配分数", value: String(match.match_score ?? "-") });
        items.push({ label: "定位命中率", value: String(match.selector_hit_rate ?? "-") });
      }
      if (validation) {
        items.push({ label: "校验通过", value: String(validation.passed) });
        items.push({ label: "覆盖率", value: String(validation.coverage ?? "-") });
      }
      if (fingerprint) {
        items.push({ label: "DOM 指纹", value: fingerprint.dom_signature || "-" });
      }

      if (!items.length) {
        return '<div class="summary-card"><div class="summary-title">暂无摘要</div><div class="subtle">当前对象没有可展示的摘要信息。</div></div>';
      }

      return `
        <div class="summary-card">
          <div class="summary-title">执行摘要</div>
          <div class="summary-grid">
            ${items.map((item) => `
              <div class="summary-item">
                <small>${escapeHtml(item.label)}</small>
                <div>${escapeHtml(item.value)}</div>
              </div>
            `).join("")}
          </div>
        </div>
      `;
    }

    function setDetail(title, payload, summaryText = "", summaryHtml = "") {
      detailTitle.textContent = title;
      detailSummary.textContent = summaryText || "这里会展示模板命中、页面指纹、校验覆盖率和批量输出信息。";
      detailBox.innerHTML = summaryHtml || `<pre>${escapeHtml(JSON.stringify(payload, null, 2))}</pre>`;
    }

    function getFilteredTemplates() {
      const search = templateSearch.value.trim().toLowerCase();
      const status = templateStatusFilter.value.trim();
      return state.templates.filter((item) => {
        if (status && item.lifecycle_status !== status) return false;
        if (!search) return true;
        const haystack = [item.template_id, item.site_id, item.template_key, item.scenario]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();
        return haystack.includes(search);
      });
    }

    function getFilteredCandidates() {
      const search = candidateSearch.value.trim().toLowerCase();
      return state.candidates.filter((item) => {
        if (!search) return true;
        const haystack = [item.candidate_id, item.site_id, item.source_url, item.scenario]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();
        return haystack.includes(search);
      });
    }

    function renderTemplates() {
      const filtered = getFilteredTemplates();
      const view = paginate(filtered, state.templatePage, Number(templatePageSize.value || 10));
      state.templatePage = view.page;
      templateMeta.textContent = `共 ${filtered.length} 个模板，已选 ${state.selectedTemplateIds.size} 个`;
      templatePagerText.textContent = `第 ${view.page} / ${view.totalPages} 页`;
      templatePrevBtn.disabled = view.page <= 1;
      templateNextBtn.disabled = view.page >= view.totalPages;

      if (!filtered.length) {
        templatesTableBody.innerHTML = '<tr><td colspan="7"><div class="empty">没有符合条件的模板。</div></td></tr>';
        updateHeroStats();
        return;
      }

      templatesTableBody.innerHTML = view.items.map((item) => {
        const selected = state.selectedTemplateIds.has(item.template_id) ? "checked" : "";
        const requiredFields = Array.isArray(item.required_fields) ? item.required_fields.join("，") : "";
        const statusClass = item.active ? "success" : item.lifecycle_status === "archived" ? "warning" : "muted";
        return `
          <tr>
            <td class="checkbox-cell"><input type="checkbox" data-template-checkbox="${escapeHtml(item.template_id)}" ${selected} /></td>
            <td>
              <div class="row-title">${escapeHtml(item.template_id)}</div>
              <div class="row-subtitle">${escapeHtml(item.template_key || "-")}</div>
            </td>
            <td>
              <div>${escapeHtml(item.site_id || "-")}</div>
              <div class="row-subtitle">${escapeHtml(item.scenario || "-")}</div>
            </td>
            <td><span class="pill ${statusClass}">${escapeHtml(item.lifecycle_status || "-")}</span></td>
            <td>${escapeHtml(item.version || "-")}</td>
            <td>${escapeHtml(requiredFields || "-")}</td>
            <td>
              <div class="row-actions">
                <button class="ghost" type="button" data-template-detail="${escapeHtml(item.template_id)}">详情</button>
                <button class="warning-button" type="button" data-template-delete="${escapeHtml(item.template_id)}">删除</button>
              </div>
            </td>
          </tr>
        `;
      }).join("");

      templatesTableBody.querySelectorAll("[data-template-checkbox]").forEach((node) => {
        node.addEventListener("change", () => {
          if (node.checked) state.selectedTemplateIds.add(node.dataset.templateCheckbox);
          else state.selectedTemplateIds.delete(node.dataset.templateCheckbox);
          renderTemplates();
        });
      });
      templatesTableBody.querySelectorAll("[data-template-detail]").forEach((node) => {
        node.addEventListener("click", () => showTemplateDetail(node.dataset.templateDetail));
      });
      templatesTableBody.querySelectorAll("[data-template-delete]").forEach((node) => {
        node.addEventListener("click", () => deleteTemplate(node.dataset.templateDelete));
      });

      const visibleIds = view.items.map((item) => item.template_id);
      selectAllTemplates.checked = visibleIds.length > 0 && visibleIds.every((id) => state.selectedTemplateIds.has(id));
      updateHeroStats();
    }

    function renderCandidates() {
      const filtered = getFilteredCandidates();
      const view = paginate(filtered, state.candidatePage, Number(candidatePageSize.value || 10));
      state.candidatePage = view.page;
      candidateMeta.textContent = `共 ${filtered.length} 个候选模板`;
      candidatePagerText.textContent = `第 ${view.page} / ${view.totalPages} 页`;
      candidatePrevBtn.disabled = view.page <= 1;
      candidateNextBtn.disabled = view.page >= view.totalPages;

      if (!filtered.length) {
        candidatesTableBody.innerHTML = '<tr><td colspan="5"><div class="empty">没有符合条件的候选模板。</div></td></tr>';
        updateHeroStats();
        return;
      }

      candidatesTableBody.innerHTML = view.items.map((item) => {
        const check = item.promotion_check || {};
        const promotable = Boolean(check.promotable);
        const extractedFields = Array.isArray(item.extracted_fields) ? item.extracted_fields.join("，") : "";
        const pill = promotable
          ? '<span class="pill success">可晋升</span>'
          : `<span class="pill ${check.action === "reuse" ? "muted" : "warning"}">${escapeHtml(check.action_label || "不可晋升")}</span>`;
        const reason = [check.detail, ...(check.reasons || []).slice(0, 2)].filter(Boolean).join("；");
        return `
          <tr>
            <td>
              <div class="row-title">${escapeHtml(item.candidate_id)}</div>
              <div class="row-subtitle">${escapeHtml(item.source_url || "-")}</div>
            </td>
            <td>
              <div>${escapeHtml(item.site_id || "-")}</div>
              <div class="row-subtitle">${escapeHtml(item.scenario || "-")}</div>
            </td>
            <td>
              ${pill}
              <div class="reason-list">${escapeHtml(reason || "已具备正式模板固化条件。")}</div>
            </td>
            <td>${escapeHtml(extractedFields || "-")}</td>
            <td>
              <div class="row-actions">
                <button class="ghost" type="button" data-candidate-detail="${escapeHtml(item.candidate_id)}">详情</button>
                <button class="secondary" type="button" data-candidate-promote="${escapeHtml(item.candidate_id)}" ${promotable ? "" : "disabled"}>${check.action === "upgrade" ? "升级" : "晋升"}</button>
                <button class="warning-button" type="button" data-candidate-delete="${escapeHtml(item.candidate_id)}">删除</button>
              </div>
            </td>
          </tr>
        `;
      }).join("");

      candidatesTableBody.querySelectorAll("[data-candidate-detail]").forEach((node) => {
        node.addEventListener("click", () => showCandidateDetail(node.dataset.candidateDetail));
      });
      candidatesTableBody.querySelectorAll("[data-candidate-promote]").forEach((node) => {
        node.addEventListener("click", () => promoteCandidate(node.dataset.candidatePromote));
      });
      candidatesTableBody.querySelectorAll("[data-candidate-delete]").forEach((node) => {
        node.addEventListener("click", () => deleteCandidate(node.dataset.candidateDelete));
      });

      updateHeroStats();
    }

    async function loadTemplates() {
      const payload = await requestJson("/templates");
      state.templates = payload.templates || [];
      renderTemplates();
    }

    async function loadCandidates() {
      const payload = await requestJson("/template-candidates");
      state.candidates = payload.candidates || [];
      renderCandidates();
    }

    async function showTemplateDetail(templateId) {
      const payload = await requestJson(`/templates/${encodeURIComponent(templateId)}`);
      setDetail(`模板 ${templateId}`, payload, "正式模板详情。", buildDetailSummary(payload));
    }

    async function showCandidateDetail(candidateId) {
      const payload = await requestJson(`/template-candidates/${encodeURIComponent(candidateId)}`);
      setDetail(`候选模板 ${candidateId}`, payload, "候选模板详情。", buildDetailSummary(payload));
    }

    async function deleteTemplate(templateId) {
      if (!window.confirm(`确认删除模板 ${templateId} 吗？`)) return;
      const payload = await requestNoContent(`/templates/${encodeURIComponent(templateId)}`, { method: "DELETE" });
      state.selectedTemplateIds.delete(templateId);
      setDetail(`删除模板 ${templateId}`, payload, "模板已删除。", buildDetailSummary(payload));
      await loadTemplates();
    }

    async function deleteSelectedTemplates() {
      const templateIds = Array.from(state.selectedTemplateIds);
      if (!templateIds.length) {
        setDetail("批量删除", { message: "未选择模板" }, "请先选择需要删除的模板。");
        return;
      }
      if (!window.confirm(`确认删除选中的 ${templateIds.length} 个模板吗？`)) return;
      const payload = await requestJson("/templates/delete-batch", {
        method: "POST",
        headers: { "Content-Type": "application/json; charset=utf-8" },
        body: JSON.stringify({ template_ids: templateIds })
      });
      state.selectedTemplateIds.clear();
      setDetail("批量删除模板", payload, "选中的模板已删除。", buildDetailSummary(payload));
      await loadTemplates();
    }

    async function deleteCandidate(candidateId) {
      if (!window.confirm(`确认删除候选模板 ${candidateId} 吗？`)) return;
      const payload = await requestNoContent(`/template-candidates/${encodeURIComponent(candidateId)}`, { method: "DELETE" });
      setDetail(`删除候选模板 ${candidateId}`, payload, "候选模板已删除。", buildDetailSummary(payload));
      await loadCandidates();
    }

    async function promoteCandidate(candidateId) {
      const templateKeyInput = window.prompt("请输入模板族标识 template_key；留空则自动生成。", "");
      if (templateKeyInput === null) return;
      const payload = await requestJson(`/template-candidates/${encodeURIComponent(candidateId)}/promote`, {
        method: "POST",
        headers: { "Content-Type": "application/json; charset=utf-8" },
        body: JSON.stringify({
          template_key: templateKeyInput.trim() || undefined,
          deactivate_previous_versions: true
        })
      });
      setDetail(`晋升候选模板 ${candidateId}`, payload, "候选模板已固化为正式模板。", buildDetailSummary(payload));
      await Promise.all([loadTemplates(), loadCandidates()]);
    }

    sampleBtn.addEventListener("click", () => {
      urlInput.value = "https://example.com/article/123";
      promptInput.value = "这是一个文章页面，提取标题、摘要、作者、发布时间和正文要点。";
      htmlInput.value = "<html><head><title>示例页面</title><meta name=\\"description\\" content=\\"这是一个示例摘要\\"></head><body><main><h1>示例标题</h1><div class=\\"author\\">张三</div><time>2026-06-21</time><article><p>这里是正文。</p></article></main></body></html>";
      state.importedFileName = "";
      state.batchFileName = "";
      state.lastResponse = null;
      setStatus("已填充示例数据。", "success");
      updateRunBadges("单条自动解析", "示例待执行", "待命");
      resetProgress();
      pushProgress("已填充示例数据", "可以直接点击开始解析。", "success");
      updateHeroStats();
    });

    clearBtn.addEventListener("click", () => {
      urlInput.value = "";
      htmlInput.value = "";
      promptInput.value = "提取页面中与用户需求最相关的结构化信息，并尽量输出中文字段名和中文值。";
      state.importedFileName = "";
      state.lastResponse = null;
      resultBox.textContent = JSON.stringify({ message: "执行后会在这里显示 JSON 结果。" }, null, 2);
      setDetail("详情面板", { message: "待执行" }, "这里会展示模板命中、页面指纹、校验覆盖率和批量输出信息。", "");
      setStatus("", "idle");
      updateRunBadges("待命", "未开始", "待命");
      resetProgress();
      updateHeroStats();
    });

    clearProgressBtn.addEventListener("click", resetProgress);

    fileInput.addEventListener("change", async (event) => {
      const [file] = event.target.files || [];
      if (!file) return;
      htmlInput.value = await file.text();
      state.importedFileName = file.name;
      setStatus(`已导入文件：${file.name}`, "success");
      resetProgress();
      pushProgress("已导入 HTML 文件", `${file.name} / ${Math.max(1, Math.round(file.size / 1024))} KB`, "success");
      updateHeroStats();
    });

    batchFileInput.addEventListener("change", async (event) => {
      const [file] = event.target.files || [];
      if (!file) return;
      state.batchFileName = file.name;
      state.batchFileContent = await file.text();
      setBatchStatus(`已导入批量文件：${file.name}`, "success");
      pushProgress("已导入 JSONL 文件", `${file.name} / ${Math.max(1, Math.round(file.size / 1024))} KB`, "success");
      updateHeroStats();
    });

    htmlInput.addEventListener("input", updateHeroStats);

    extractBtn.addEventListener("click", async () => {
      const payload = {
        url: urlInput.value.trim(),
        user_prompt: promptInput.value.trim(),
        raw_html: htmlInput.value
      };
      if (!payload.raw_html.trim()) {
        setStatus("请先提供网页源码。", "error");
        pushProgress("缺少网页源码", "请先粘贴 HTML 或导入本地 HTML 文件。", "error");
        return;
      }

      state.batchFileName = "";
      resetProgress();
      updateRunBadges("单条自动解析", "执行中", "待命");
      pushProgress("输入已就绪", state.importedFileName ? `单条文件：${state.importedFileName}` : `手动输入 HTML，长度 ${payload.raw_html.length} 字符`, "success");
      pushProgress(payload.url ? "已提供 URL" : "未提供 URL", payload.url || "本次会优先用 HTML 进行自动解析。", payload.url ? "success" : "warning");
      pushProgress("开始解析", "正在判断模板命中与回退策略。", "loading");
      setStatus("解析中...", "idle");

      try {
        const response = await requestJson("/extract", {
          method: "POST",
          headers: { "Content-Type": "application/json; charset=utf-8" },
          body: JSON.stringify(payload)
        });
        state.lastResponse = response;
        resultBox.textContent = JSON.stringify(response, null, 2);
        setStatus(response.status === "success" ? "解析成功" : "解析失败", response.status === "success" ? "success" : "error");
        setDetail("本次解析详情", response, "单条解析执行详情。", buildDetailSummary(response));
        updateRunBadges("单条自动解析", response.extractor_type || "未知", response.status === "success" ? "成功" : "失败");
        pushResponseProgress(response);
        updateHeroStats();
        await Promise.all([loadTemplates(), loadCandidates()]);
      } catch (error) {
        resultBox.textContent = JSON.stringify({ error: String(error) }, null, 2);
        setStatus("解析失败", "error");
        setDetail("解析失败", { error: String(error) }, "服务端返回错误。");
        updateRunBadges("单条自动解析", "失败", "失败");
        pushProgress("解析失败", String(error), "error");
      }
    });

    batchExtractBtn.addEventListener("click", async () => {
      if (!state.batchFileContent.trim()) {
        setBatchStatus("请先导入 JSONL 文件。", "error");
        pushProgress("缺少批量文件", "请先导入包含 url 和 html_path 的 JSONL 文件。", "error");
        return;
      }

      resetProgress();
      state.lastResponse = null;
      updateRunBadges("批量模板解析", "执行中", "待命");
      pushProgress("批量任务已就绪", state.batchFileName || "内存中的 JSONL 内容", "success");
      pushProgress("开始批量模板解析", "该通道只允许命中正式模板，不会调用 LLM。", "loading");
      setBatchStatus("批量解析中...", "idle");

      try {
        const response = await requestJson("/extract/batch", {
          method: "POST",
          headers: { "Content-Type": "application/json; charset=utf-8" },
          body: JSON.stringify({
            jsonl_content: state.batchFileContent,
            user_prompt: batchPromptInput.value.trim(),
            output_jsonl_path: batchOutputPathInput.value.trim()
          })
        });
        resultBox.textContent = JSON.stringify(response, null, 2);
        setBatchStatus(`批量解析完成，输出文件：${response.output_jsonl_path}`, "success");
        setDetail(
          "批量解析完成",
          response,
          "批量模板解析结果摘要。",
          `
            <div class="summary-card">
              <div class="summary-title">批量输出</div>
              <div class="summary-grid">
                <div class="summary-item"><small>输出文件</small><div>${escapeHtml(response.output_jsonl_path || "-")}</div></div>
                <div class="summary-item"><small>总数</small><div>${escapeHtml(response.total_count || 0)}</div></div>
                <div class="summary-item"><small>成功</small><div>${escapeHtml(response.success_count || 0)}</div></div>
                <div class="summary-item"><small>失败</small><div>${escapeHtml(response.failed_count || 0)}</div></div>
              </div>
            </div>
          `
        );
        updateRunBadges("批量模板解析", `${response.success_count}/${response.total_count}`, response.failed_count ? "失败" : "成功");
        pushProgress("批量输出已落盘", response.output_jsonl_path || "未返回路径", "success");
        pushProgress("批量解析完成", `成功 ${response.success_count} 条，失败 ${response.failed_count} 条`, response.failed_count ? "warning" : "success");
      } catch (error) {
        resultBox.textContent = JSON.stringify({ error: String(error) }, null, 2);
        setBatchStatus("批量解析失败", "error");
        setDetail("批量解析失败", { error: String(error) }, "批量任务执行失败。");
        updateRunBadges("批量模板解析", "失败", "失败");
        pushProgress("批量解析失败", String(error), "error");
      }
    });

    document.getElementById("refreshTemplatesBtn").addEventListener("click", loadTemplates);
    document.getElementById("refreshCandidatesBtn").addEventListener("click", loadCandidates);
    document.getElementById("deleteSelectedTemplatesBtn").addEventListener("click", deleteSelectedTemplates);

    [templateSearch, templateStatusFilter, templatePageSize].forEach((node) => {
      node.addEventListener("input", () => { state.templatePage = 1; renderTemplates(); });
      node.addEventListener("change", () => { state.templatePage = 1; renderTemplates(); });
    });
    [candidateSearch, candidatePageSize].forEach((node) => {
      node.addEventListener("input", () => { state.candidatePage = 1; renderCandidates(); });
      node.addEventListener("change", () => { state.candidatePage = 1; renderCandidates(); });
    });

    templatePrevBtn.addEventListener("click", () => { state.templatePage -= 1; renderTemplates(); });
    templateNextBtn.addEventListener("click", () => { state.templatePage += 1; renderTemplates(); });
    candidatePrevBtn.addEventListener("click", () => { state.candidatePage -= 1; renderCandidates(); });
    candidateNextBtn.addEventListener("click", () => { state.candidatePage += 1; renderCandidates(); });
    selectAllTemplates.addEventListener("change", () => {
      const filtered = getFilteredTemplates();
      const view = paginate(filtered, state.templatePage, Number(templatePageSize.value || 10));
      if (selectAllTemplates.checked) view.items.forEach((item) => state.selectedTemplateIds.add(item.template_id));
      else view.items.forEach((item) => state.selectedTemplateIds.delete(item.template_id));
      renderTemplates();
    });

    updateRunBadges("待命", "未开始", "待命");
    updateHeroStats();
    loadTemplates().catch((error) => {
      templatesTableBody.innerHTML = `<tr><td colspan="7"><div class="empty">模板加载失败：${escapeHtml(String(error))}</div></td></tr>`;
    });
    loadCandidates().catch((error) => {
      candidatesTableBody.innerHTML = `<tr><td colspan="5"><div class="empty">候选模板加载失败：${escapeHtml(String(error))}</div></td></tr>`;
    });
  </script>
</body>
</html>
"""
