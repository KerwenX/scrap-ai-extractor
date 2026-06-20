from __future__ import annotations


def build_web_ui_html() -> str:
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>混合网页解析器</title>
  <style>
    :root {
      --bg: linear-gradient(135deg, #f4efe7 0%, #eef4ef 45%, #e6edf6 100%);
      --panel: rgba(255, 255, 255, 0.84);
      --text: #17212b;
      --muted: #5d6874;
      --line: rgba(23, 33, 43, 0.12);
      --line-strong: rgba(23, 33, 43, 0.2);
      --accent: #0d6b63;
      --accent-strong: #094840;
      --danger: #8f2d2d;
      --warning: #8c5f0a;
      --shadow: 0 24px 60px rgba(18, 26, 34, 0.12);
      --radius: 24px;
      --mono: "Cascadia Code", "SFMono-Regular", Consolas, monospace;
      --sans: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      font-family: var(--sans);
      color: var(--text);
      background: var(--bg);
    }
    .shell {
      max-width: 1480px;
      margin: 0 auto;
      padding: 28px 18px 40px;
    }
    .hero, .workspace, .library-grid { display: grid; gap: 18px; }
    .hero { grid-template-columns: 1.3fr 0.9fr; margin-bottom: 18px; }
    .workspace { grid-template-columns: minmax(360px, 430px) minmax(0, 1fr); align-items: start; }
    .workspace-side { display: grid; gap: 18px; align-content: start; min-width: 0; }
    .library-grid { margin-top: 18px; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      backdrop-filter: blur(10px);
      min-width: 0;
    }
    .hero-copy, .hero-meta, .form-panel, .result-panel, .library-panel, .detail-panel { padding: 22px 24px; }
    .hero-copy { position: relative; overflow: hidden; }
    .hero-copy::after {
      content: "";
      position: absolute;
      width: 220px;
      height: 220px;
      right: -70px;
      bottom: -80px;
      background: radial-gradient(circle, rgba(13, 107, 99, 0.28), rgba(13, 107, 99, 0));
    }
    h1 {
      margin: 0 0 12px;
      font-size: clamp(30px, 4vw, 48px);
      line-height: 1.04;
      letter-spacing: -0.04em;
    }
    .subtitle {
      margin: 0;
      max-width: 56ch;
      font-size: 15px;
      line-height: 1.75;
      color: var(--muted);
    }
    .hero-meta { display: grid; gap: 12px; align-content: center; }
    .stat, .empty {
      border: 1px solid var(--line);
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.6);
    }
    .stat { padding: 14px 16px; }
    .stat-label, label, .status, .mini-note, .hint, .card-meta, .table-meta { color: var(--muted); }
    .stat-label { display: block; margin-bottom: 6px; font-size: 12px; }
    .stat-value { font-size: 15px; font-weight: 600; }
    .section-title { margin: 0 0 16px; font-size: 18px; font-weight: 700; }
    .field { margin-bottom: 14px; }
    label { display: block; margin-bottom: 8px; font-size: 13px; }
    input[type="text"], textarea, select {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 12px 14px;
      background: rgba(255, 255, 255, 0.82);
      color: var(--text);
      font: inherit;
    }
    textarea { min-height: 132px; resize: vertical; }
    .html-box { min-height: 220px; font-family: var(--mono); font-size: 12px; line-height: 1.55; }
    .actions, .toolbar, .result-toolbar, .filter-row, .pager {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
    }
    .result-toolbar, .pager { justify-content: space-between; }
    .actions { margin-top: 18px; }
    .filter-row { margin: 14px 0 10px; }
    .filter-row > * { flex: 1 1 160px; }
    .filter-row .compact { flex: 0 0 140px; }
    .toolbar.compact { gap: 8px; }
    button, .button-like {
      border: 0;
      border-radius: 999px;
      padding: 10px 16px;
      font: inherit;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      text-decoration: none;
      white-space: normal;
      overflow-wrap: anywhere;
      text-align: center;
    }
    button:disabled, .button-like:has(input:disabled) { opacity: 0.65; cursor: default; }
    .primary {
      color: white;
      background: linear-gradient(135deg, var(--accent) 0%, #2d8b78 100%);
      box-shadow: 0 14px 30px rgba(13, 107, 99, 0.24);
    }
    .secondary, .ghost, .button-like.secondary {
      color: var(--text);
      background: rgba(255, 255, 255, 0.82);
      border: 1px solid var(--line);
    }
    .ghost { font-size: 13px; padding: 8px 14px; }
    .danger {
      color: white;
      background: linear-gradient(135deg, #8f2d2d 0%, #bc4b4b 100%);
    }
    .warning-button {
      color: #7a4d07;
      background: rgba(140, 95, 10, 0.12);
      border: 1px solid rgba(140, 95, 10, 0.18);
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
    .badge, .pill {
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 600;
    }
    .badge {
      gap: 8px;
      padding: 8px 12px;
      background: rgba(13, 107, 99, 0.1);
      color: var(--accent-strong);
    }
    .pill { padding: 5px 10px; font-size: 11px; font-weight: 700; }
    .pill.success { background: rgba(13, 107, 99, 0.12); color: var(--accent-strong); }
    .pill.muted { background: rgba(23, 33, 43, 0.07); color: var(--muted); }
    .pill.warning { background: rgba(140, 95, 10, 0.12); color: var(--warning); }
    pre {
      margin: 0;
      border-radius: 18px;
      padding: 18px;
      min-height: 0;
      max-height: 420px;
      overflow: auto;
      background: #0f1722;
      color: #d7f8f0;
      font-family: var(--mono);
      font-size: 12px;
      line-height: 1.6;
      white-space: pre-wrap;
      word-break: break-word;
    }
    .detail-panel pre { min-height: 260px; background: #121826; }
    .empty { padding: 18px; border-style: dashed; font-size: 13px; }
    .table-wrap {
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.58);
    }
    table {
      width: 100%;
      border-collapse: collapse;
      min-width: 880px;
    }
    th, td {
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
      font-size: 13px;
    }
    th {
      position: sticky;
      top: 0;
      z-index: 1;
      background: rgba(244, 248, 250, 0.95);
      font-size: 12px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    tr:last-child td { border-bottom: 0; }
    .row-title {
      font-weight: 700;
      color: var(--text);
      margin-bottom: 4px;
      word-break: break-word;
      overflow-wrap: anywhere;
    }
    .row-subtitle {
      color: var(--muted);
      font-size: 12px;
      word-break: break-word;
      overflow-wrap: anywhere;
    }
    .checkbox-cell {
      width: 40px;
    }
    .checkbox-cell input {
      width: 16px;
      height: 16px;
    }
    .row-actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      align-items: stretch;
    }
    .row-actions > button {
      max-width: 100%;
    }
    .table-meta {
      font-size: 12px;
      margin-bottom: 10px;
    }
    .candidate-status {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      margin-top: 6px;
      color: var(--muted);
    }
    .reason-list {
      margin-top: 6px;
      font-size: 12px;
      color: var(--warning);
      line-height: 1.55;
    }
    .detail-summary {
      margin: 14px 0 16px;
      display: grid;
      gap: 14px;
    }
    .summary-card {
      border: 1px solid var(--line);
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.62);
      padding: 14px 16px;
    }
    .summary-title {
      margin: 0 0 10px;
      font-size: 14px;
      font-weight: 700;
      color: var(--text);
    }
    .summary-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 10px;
    }
    .summary-item {
      padding: 10px 12px;
      border-radius: 14px;
      background: rgba(15, 23, 34, 0.04);
      border: 1px solid rgba(15, 23, 34, 0.06);
      min-width: 0;
    }
    .summary-label {
      display: block;
      margin-bottom: 6px;
      font-size: 11px;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      color: var(--muted);
    }
    .summary-value {
      font-size: 13px;
      line-height: 1.65;
      color: var(--text);
      word-break: break-word;
    }
    .summary-list {
      display: grid;
      gap: 8px;
    }
    .field-rule {
      padding: 12px 14px;
      border-radius: 16px;
      background: rgba(13, 107, 99, 0.06);
      border: 1px solid rgba(13, 107, 99, 0.12);
    }
    .field-rule-header {
      display: flex;
      gap: 8px;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      margin-bottom: 8px;
    }
    .field-rule-name {
      font-size: 14px;
      font-weight: 700;
      color: var(--accent-strong);
      word-break: break-word;
    }
    .token-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 6px;
    }
    .token {
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 5px 10px;
      font-size: 12px;
      line-height: 1.4;
      border: 1px solid rgba(15, 23, 34, 0.08);
      background: rgba(255, 255, 255, 0.86);
      color: var(--text);
      word-break: break-word;
      overflow-wrap: anywhere;
      white-space: normal;
    }
    .token.warning {
      color: var(--warning);
      background: rgba(140, 95, 10, 0.08);
      border-color: rgba(140, 95, 10, 0.14);
    }
    .progress-panel {
      margin-top: 16px;
      padding: 14px 16px;
      border-radius: 18px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.58);
    }
    .progress-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
      margin-bottom: 10px;
    }
    .progress-title {
      margin: 0;
      font-size: 14px;
      font-weight: 700;
    }
    .progress-hint {
      font-size: 12px;
      color: var(--muted);
    }
    .progress-list {
      display: grid;
      gap: 10px;
    }
    .progress-item {
      display: grid;
      grid-template-columns: 14px minmax(0, 1fr);
      gap: 10px;
      align-items: start;
      min-width: 0;
    }
    .progress-dot {
      width: 14px;
      height: 14px;
      border-radius: 999px;
      margin-top: 4px;
      background: rgba(23, 33, 43, 0.16);
      box-shadow: inset 0 0 0 3px rgba(255, 255, 255, 0.65);
    }
    .progress-dot.loading { background: rgba(140, 95, 10, 0.9); }
    .progress-dot.success { background: rgba(13, 107, 99, 0.88); }
    .progress-dot.error { background: rgba(143, 45, 45, 0.88); }
    .progress-body {
      min-width: 0;
      padding-bottom: 10px;
      border-bottom: 1px dashed rgba(23, 33, 43, 0.12);
    }
    .progress-item:last-child .progress-body {
      border-bottom: 0;
      padding-bottom: 0;
    }
    .progress-label {
      font-size: 13px;
      font-weight: 700;
      line-height: 1.5;
      word-break: break-word;
      overflow-wrap: anywhere;
    }
    .progress-meta {
      margin-top: 2px;
      font-size: 12px;
      color: var(--muted);
      word-break: break-word;
      overflow-wrap: anywhere;
      line-height: 1.6;
    }
    .hidden { display: none !important; }
    .modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(15, 23, 34, 0.4);
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
      z-index: 40;
    }
    .modal {
      width: min(520px, 100%);
      background: rgba(255, 255, 255, 0.96);
      border: 1px solid var(--line);
      border-radius: 24px;
      box-shadow: 0 32px 80px rgba(15, 23, 34, 0.22);
      padding: 22px 22px 18px;
    }
    .modal h3 {
      margin: 0 0 10px;
      font-size: 18px;
    }
    .modal p {
      margin: 0 0 14px;
      color: var(--muted);
      line-height: 1.65;
      font-size: 14px;
    }
    .modal .actions {
      margin-top: 14px;
      justify-content: flex-end;
    }
    @media (max-width: 1080px) {
      .hero, .workspace, .library-grid { grid-template-columns: 1fr; }
      .detail-panel pre { min-height: 360px; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div class="panel hero-copy">
        <h1>混合网页解析器</h1>
        <p class="subtitle">输入 URL、用户需求和网页源码，系统优先命中正式模板；无法命中或校验失败时回退到 LLM，并把可复用的抽取方法沉淀为候选模板与正式模板。</p>
      </div>
      <div class="panel hero-meta">
        <div class="stat"><span class="stat-label">核心接口</span><span class="stat-value">POST /extract</span></div>
        <div class="stat"><span class="stat-label">模板管理</span><span class="stat-value">分页、筛选、批量删除</span></div>
        <div class="stat"><span class="stat-label">当前策略</span><span class="stat-value">模板优先，LLM 兜底，支持人工治理</span></div>
      </div>
    </section>

    <section class="workspace">
      <div class="panel form-panel">
        <h2 class="section-title">解析输入</h2>
        <div class="field">
          <label for="url">原始 URL</label>
          <input id="url" type="text" placeholder="https://example.com/article/123" />
        </div>
        <div class="field">
          <label for="prompt">抽取需求</label>
          <textarea id="prompt">提取页面中与用户需求最相关的结构化信息，并尽量输出中文字段和值。</textarea>
        </div>
        <div class="field">
          <label for="html">网页源码</label>
          <textarea id="html" class="html-box" placeholder="直接粘贴 HTML，或导入本地 HTML 文件。"></textarea>
        </div>
        <div class="actions">
          <button class="primary" id="extractBtn" type="button">开始解析</button>
          <label class="button-like secondary upload" id="uploadButton">导入 HTML 文件<input id="fileInput" type="file" accept=".html,.htm,text/html" /></label>
          <button class="secondary" id="sampleBtn" type="button">填充示例</button>
          <button class="secondary" id="clearBtn" type="button">清空</button>
        </div>
        <div class="hint">该界面不会主动抓取远程 URL。你需要提供实际网页源码，服务才会进行模板匹配、LLM 抽取和模板固化。</div>
      </div>

      <div class="workspace-side">
        <div class="panel result-panel">
          <div class="result-toolbar">
            <h2 class="section-title" style="margin: 0;">解析结果</h2>
            <div class="badge" id="statusBadge">等待执行</div>
          </div>
          <div class="status" id="statusLine"></div>
          <pre id="resultBox">{
  "message": "执行后会在这里显示 JSON 结果。"
}</pre>
          <div class="progress-panel">
            <div class="progress-header">
              <h3 class="progress-title">解析进度</h3>
              <div class="progress-hint" id="progressHint">等待开始</div>
            </div>
            <div class="progress-list" id="progressList">
              <div class="empty">导入 HTML、发起解析后，这里会按时间顺序展示当前执行路径。</div>
            </div>
          </div>
        </div>

        <div class="panel detail-panel">
          <div class="result-toolbar">
            <h2 class="section-title" style="margin: 0;">详情</h2>
            <div class="badge" id="detailBadge">未选择</div>
          </div>
          <div class="status" id="detailStatus">点击表格中的详情按钮查看模板或候选模板内容。</div>
          <div class="detail-summary" id="detailSummary">
            <div class="empty">这里会优先展示模板的规则定位、指纹、后处理和可晋升性摘要。</div>
          </div>
          <pre id="detailBox">{
  "message": "详情会显示在这里。"
}</pre>
        </div>
      </div>
    </section>

    <section class="library-grid">
      <div class="panel library-panel">
        <div class="result-toolbar">
          <h2 class="section-title" style="margin: 0;">正式模板</h2>
          <div class="toolbar compact">
            <button class="ghost" id="refreshTemplatesBtn" type="button">刷新模板</button>
            <button class="danger" id="deleteSelectedTemplatesBtn" type="button">删除选中</button>
          </div>
        </div>
        <div class="mini-note">这里展示已经可以直接复用的正式模板，适合做批量网页解析。</div>
        <div class="filter-row">
          <input id="templateSearch" type="text" placeholder="搜索 template_id / site_id / template_key" />
          <select id="templateStatusFilter" class="compact">
            <option value="">全部状态</option>
            <option value="active">active</option>
            <option value="draft">draft</option>
            <option value="deprecated">deprecated</option>
            <option value="archived">archived</option>
          </select>
          <select id="templatePageSize" class="compact">
            <option value="5">5 / 页</option>
            <option value="10" selected>10 / 页</option>
            <option value="20">20 / 页</option>
          </select>
        </div>
        <div class="table-meta" id="templateMeta"></div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th class="checkbox-cell"><input id="selectAllTemplates" type="checkbox" /></th>
                <th>模板</th>
                <th>站点 / 场景</th>
                <th>状态</th>
                <th>版本</th>
                <th>字段</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody id="templatesTableBody"></tbody>
          </table>
        </div>
        <div class="pager" style="margin-top: 12px;">
          <button class="ghost" id="templatePrevBtn" type="button">上一页</button>
          <div class="mini-note" id="templatePagerText"></div>
          <button class="ghost" id="templateNextBtn" type="button">下一页</button>
        </div>
      </div>

      <div class="panel library-panel">
        <div class="result-toolbar">
          <h2 class="section-title" style="margin: 0;">候选模板</h2>
          <div class="toolbar compact">
            <button class="ghost" id="refreshCandidatesBtn" type="button">刷新候选</button>
          </div>
        </div>
        <div class="mini-note">候选模板保留首次 LLM 成功抽取后的分析结果与 DSL 草案。只有生成了可执行规则的候选模板，才能晋升为正式模板。</div>
        <div class="filter-row">
          <input id="candidateSearch" type="text" placeholder="搜索 candidate_id / site_id / source_url" />
          <select id="candidatePageSize" class="compact">
            <option value="5">5 / 页</option>
            <option value="10" selected>10 / 页</option>
            <option value="20">20 / 页</option>
          </select>
        </div>
        <div class="table-meta" id="candidateMeta"></div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>候选模板</th>
                <th>站点 / 场景</th>
                <th>可晋升性</th>
                <th>字段</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody id="candidatesTableBody"></tbody>
          </table>
        </div>
        <div class="pager" style="margin-top: 12px;">
          <button class="ghost" id="candidatePrevBtn" type="button">上一页</button>
          <div class="mini-note" id="candidatePagerText"></div>
          <button class="ghost" id="candidateNextBtn" type="button">下一页</button>
        </div>
      </div>
    </section>
  </div>

  <div class="modal-backdrop hidden" id="modalBackdrop">
    <div class="modal">
      <h3 id="modalTitle">操作确认</h3>
      <p id="modalMessage"></p>
      <div class="field hidden" id="modalInputWrap">
        <label for="modalInput">输入内容</label>
        <input id="modalInput" type="text" />
      </div>
      <div class="actions">
        <button class="ghost" id="modalCancelBtn" type="button">取消</button>
        <button class="primary" id="modalConfirmBtn" type="button">确认</button>
      </div>
    </div>
  </div>

  <script>
    const state = {
      templates: [],
      candidates: [],
      selectedTemplateIds: new Set(),
      templatePage: 1,
      candidatePage: 1,
      progressEvents: [],
      importedFileName: ""
    };

    const urlInput = document.getElementById("url");
    const promptInput = document.getElementById("prompt");
    const htmlInput = document.getElementById("html");
    const extractBtn = document.getElementById("extractBtn");
    const sampleBtn = document.getElementById("sampleBtn");
    const clearBtn = document.getElementById("clearBtn");
    const fileInput = document.getElementById("fileInput");
    const resultBox = document.getElementById("resultBox");
    const statusLine = document.getElementById("statusLine");
    const statusBadge = document.getElementById("statusBadge");
    const progressList = document.getElementById("progressList");
    const progressHint = document.getElementById("progressHint");
    const detailBox = document.getElementById("detailBox");
    const detailSummary = document.getElementById("detailSummary");
    const detailStatus = document.getElementById("detailStatus");
    const detailBadge = document.getElementById("detailBadge");
    const refreshTemplatesBtn = document.getElementById("refreshTemplatesBtn");
    const refreshCandidatesBtn = document.getElementById("refreshCandidatesBtn");
    const deleteSelectedTemplatesBtn = document.getElementById("deleteSelectedTemplatesBtn");
    const templateSearch = document.getElementById("templateSearch");
    const templateStatusFilter = document.getElementById("templateStatusFilter");
    const templatePageSize = document.getElementById("templatePageSize");
    const templateMeta = document.getElementById("templateMeta");
    const templatesTableBody = document.getElementById("templatesTableBody");
    const templatePagerText = document.getElementById("templatePagerText");
    const templatePrevBtn = document.getElementById("templatePrevBtn");
    const templateNextBtn = document.getElementById("templateNextBtn");
    const selectAllTemplates = document.getElementById("selectAllTemplates");
    const candidateSearch = document.getElementById("candidateSearch");
    const candidatePageSize = document.getElementById("candidatePageSize");
    const candidateMeta = document.getElementById("candidateMeta");
    const candidatesTableBody = document.getElementById("candidatesTableBody");
    const candidatePagerText = document.getElementById("candidatePagerText");
    const candidatePrevBtn = document.getElementById("candidatePrevBtn");
    const candidateNextBtn = document.getElementById("candidateNextBtn");
    const modalBackdrop = document.getElementById("modalBackdrop");
    const modalTitle = document.getElementById("modalTitle");
    const modalMessage = document.getElementById("modalMessage");
    const modalInputWrap = document.getElementById("modalInputWrap");
    const modalInput = document.getElementById("modalInput");
    const modalCancelBtn = document.getElementById("modalCancelBtn");
    const modalConfirmBtn = document.getElementById("modalConfirmBtn");
    let activeDialogResolver = null;

    function setStatus(text, tone) {
      statusLine.textContent = text;
      if (tone === "loading") {
        statusBadge.textContent = "执行中";
        statusBadge.style.background = "rgba(140, 95, 10, 0.12)";
        statusBadge.style.color = "#8c5f0a";
        return;
      }
      if (tone === "error") {
        statusBadge.textContent = "失败";
        statusBadge.style.background = "rgba(143, 45, 45, 0.12)";
        statusBadge.style.color = "#8f2d2d";
        return;
      }
      if (tone === "success") {
        statusBadge.textContent = "成功";
        statusBadge.style.background = "rgba(13, 107, 99, 0.12)";
        statusBadge.style.color = "#094840";
        return;
      }
      statusBadge.textContent = "等待执行";
      statusBadge.style.background = "rgba(13, 107, 99, 0.1)";
      statusBadge.style.color = "#094840";
    }

    function formatProgressTime(date = new Date()) {
      return date.toLocaleTimeString("zh-CN", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
      });
    }

    function renderProgress() {
      if (!state.progressEvents.length) {
        progressHint.textContent = "等待开始";
        progressList.innerHTML = '<div class="empty">导入 HTML、发起解析后，这里会按时间顺序展示当前执行路径。</div>';
        return;
      }
      const last = state.progressEvents[state.progressEvents.length - 1];
      progressHint.textContent = `${state.progressEvents.length} 个节点`;
      progressList.innerHTML = state.progressEvents.map((item) => `
        <div class="progress-item">
          <div class="progress-dot ${escapeHtml(item.tone || "")}"></div>
          <div class="progress-body">
            <div class="progress-label">${escapeHtml(item.label || "-")}</div>
            <div class="progress-meta">${escapeHtml(item.detail || "-")} · ${escapeHtml(item.time || "")}</div>
          </div>
        </div>
      `).join("");
      if (last?.detail) {
        progressHint.textContent = last.detail;
      }
    }

    function resetProgress() {
      state.progressEvents = [];
      renderProgress();
    }

    function pushProgress(label, detail, tone = "") {
      state.progressEvents.push({
        label,
        detail,
        tone,
        time: formatProgressTime()
      });
      state.progressEvents = state.progressEvents.slice(-8);
      renderProgress();
    }

    function setDetail(label, payload, message, summaryHtml) {
      detailBadge.textContent = label;
      detailStatus.textContent = message || "";
      detailSummary.innerHTML = summaryHtml || '<div class="empty">当前没有可展示的规则定位摘要。</div>';
      detailBox.textContent = JSON.stringify(payload, null, 2);
    }

    function closeDialog(result) {
      modalBackdrop.classList.add("hidden");
      if (activeDialogResolver) {
        activeDialogResolver(result);
        activeDialogResolver = null;
      }
    }

    function openDialog({ title, message, confirmText = "确认", cancelText = "取消", input = false, defaultValue = "" }) {
      modalTitle.textContent = title || "操作确认";
      modalMessage.textContent = message || "";
      modalConfirmBtn.textContent = confirmText;
      modalCancelBtn.textContent = cancelText;
      modalInputWrap.classList.toggle("hidden", !input);
      modalInput.value = defaultValue || "";
      modalBackdrop.classList.remove("hidden");
      if (input) setTimeout(() => modalInput.focus(), 10);
      return new Promise((resolve) => {
        activeDialogResolver = resolve;
      });
    }

    async function askConfirm(title, message, confirmText) {
      const result = await openDialog({ title, message, confirmText: confirmText || "确认" });
      return result?.confirmed === true;
    }

    async function askInput(title, message, defaultValue) {
      const result = await openDialog({ title, message, input: true, defaultValue: defaultValue || "", confirmText: "继续" });
      if (!result?.confirmed) return null;
      return result.value ?? "";
    }

    async function requestJson(url, options) {
      const response = await fetch(url, options);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
      return data;
    }

    async function requestNoContent(url, options) {
      const response = await fetch(url, options);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
      return data;
    }

    function escapeHtml(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
    }

    function renderTokenList(values, tone) {
      if (!Array.isArray(values) || !values.length) {
        return '<span class="token">-</span>';
      }
      return values
        .map((value) => `<span class="token ${tone || ""}">${escapeHtml(value)}</span>`)
        .join("");
    }

    function renderSummaryItem(label, value) {
      return `
        <div class="summary-item">
          <span class="summary-label">${escapeHtml(label)}</span>
          <div class="summary-value">${value || "-"}</div>
        </div>
      `;
    }

    function formatSelector(selector) {
      if (!selector || typeof selector !== "object") return "-";
      const attr = selector.attr && selector.attr !== "text" ? ` @${selector.attr}` : "";
      const many = selector.many ? " [many]" : "";
      return `${selector.kind || "unknown"}: ${selector.value || "-"}${attr}${many}`;
    }

    function formatPostprocess(step) {
      if (!step || typeof step !== "object") return "-";
      const args = step.args && Object.keys(step.args).length
        ? ` ${escapeHtml(JSON.stringify(step.args))}`
        : "";
      return `${escapeHtml(step.op || "unknown")}${args}`;
    }

    function findFieldAnalysis(analysis, fieldName) {
      const items = analysis && Array.isArray(analysis.field_analyses) ? analysis.field_analyses : [];
      return items.find((item) => item.field_name === fieldName) || null;
    }

    function renderPlanCard(plan, analysis, title) {
      const fields = plan && Array.isArray(plan.fields) ? plan.fields : [];
      if (!fields.length) {
        return `
          <div class="summary-card">
            <div class="summary-title">${escapeHtml(title)}</div>
            <div class="empty">当前没有生成可执行的字段级 DSL 规则。</div>
          </div>
        `;
      }
      const items = fields.map((field) => {
        const fieldAnalysis = findFieldAnalysis(analysis, field.field_name);
        const selectors = Array.isArray(field.selectors) ? field.selectors : [];
        const steps = Array.isArray(field.postprocess) ? field.postprocess : [];
        const fallback = field.fallback_value == null ? "-" : escapeHtml(JSON.stringify(field.fallback_value));
        return `
          <div class="field-rule">
            <div class="field-rule-header">
              <div class="field-rule-name">${escapeHtml(field.field_name || "-")}</div>
              <span class="pill ${fieldAnalysis?.deterministic_feasibility === "low" ? "warning" : "success"}">
                ${escapeHtml(fieldAnalysis?.deterministic_feasibility || "rule")}
              </span>
            </div>
            <div class="summary-grid">
              ${renderSummaryItem("定位选择器", `<div class="token-row">${renderTokenList(selectors.map(formatSelector))}</div>`)}
              ${renderSummaryItem("后处理", `<div class="token-row">${renderTokenList(steps.map(formatPostprocess))}</div>`)}
              ${renderSummaryItem("锚点提示", `<div class="token-row">${renderTokenList(fieldAnalysis?.likely_anchors || [])}</div>`)}
              ${renderSummaryItem("回退值", fallback)}
            </div>
          </div>
        `;
      }).join("");
      return `
        <div class="summary-card">
          <div class="summary-title">${escapeHtml(title)}</div>
          <div class="summary-list">${items}</div>
        </div>
      `;
    }

    function renderAnalysisCard(analysis) {
      if (!analysis) {
        return "";
      }
      return `
        <div class="summary-card">
          <div class="summary-title">模板分析</div>
          <div class="summary-grid">
            ${renderSummaryItem("分析摘要", escapeHtml(analysis.summary || "-"))}
            ${renderSummaryItem("页面线索", `<div class="token-row">${renderTokenList(analysis.page_cues || [])}</div>`)}
            ${renderSummaryItem("需回退字段", `<div class="token-row">${renderTokenList(analysis.fallback_fields || [], "warning")}</div>`)}
          </div>
        </div>
      `;
    }

    function renderFingerprintCard(fingerprint) {
      if (!fingerprint) {
        return "";
      }
      return `
        <div class="summary-card">
          <div class="summary-title">页面指纹</div>
          <div class="summary-grid">
            ${renderSummaryItem("DOM 签名", escapeHtml(fingerprint.dom_signature || "-"))}
            ${renderSummaryItem("标题锚点", `<div class="token-row">${renderTokenList(fingerprint.headings || [])}</div>`)}
            ${renderSummaryItem("关键 ID", `<div class="token-row">${renderTokenList(fingerprint.key_ids || [])}</div>`)}
            ${renderSummaryItem("关键 Class", `<div class="token-row">${renderTokenList(fingerprint.key_classes || [])}</div>`)}
          </div>
        </div>
      `;
    }

    function renderPromotionCard(check) {
      if (!check) {
        return "";
      }
      const reasons = Array.isArray(check.reasons) ? check.reasons : [];
      return `
        <div class="summary-card">
          <div class="summary-title">晋升检查</div>
          <div class="summary-grid">
            ${renderSummaryItem("可晋升", check.promotable ? '<span class="pill success">可晋升</span>' : '<span class="pill warning">不可晋升</span>')}
            ${renderSummaryItem("字段规则", check.has_plan ? '<span class="pill success">已生成</span>' : '<span class="pill warning">缺失</span>')}
            ${renderSummaryItem("已抽字段", String(check.extracted_field_count ?? 0))}
            ${renderSummaryItem("冲突模板", escapeHtml(check.existing_template_id || "-"))}
            ${renderSummaryItem("不可晋升原因", `<div class="token-row">${renderTokenList(reasons, "warning")}</div>`)}
          </div>
        </div>
      `;
    }

    function buildDetailSummary(payload) {
      if (!payload || typeof payload !== "object") {
        return '<div class="empty">当前没有可展示的规则定位摘要。</div>';
      }
      const blocks = [];
      if (payload.fingerprint) {
        blocks.push(renderFingerprintCard(payload.fingerprint));
      }
      if (payload.analysis) {
        blocks.push(renderAnalysisCard(payload.analysis));
      }
      if (payload.extraction_plan) {
        blocks.push(renderPlanCard(payload.extraction_plan, payload.analysis, "正式模板规则定位"));
      }
      if (payload.proposed_plan) {
        blocks.push(renderPlanCard(payload.proposed_plan, payload.analysis, "候选模板规则定位"));
      }
      if (payload.promotion_check) {
        blocks.push(renderPromotionCard(payload.promotion_check));
      }
      if (!blocks.length) {
        return '<div class="empty">当前详情对象不包含模板规则、候选规则或页面指纹。</div>';
      }
      return blocks.join("");
    }

    function pushResponseProgress(data) {
      if (!data || typeof data !== "object") {
        return;
      }
      const debugTrace = data.debug_trace || {};
      if (data.extractor_type === "deterministic") {
        pushProgress(
          "命中正式模板",
          data.template_id ? `直接使用模板 ${data.template_id}` : "直接使用本地正式模板规则",
          "success"
        );
      } else if (data.extractor_type === "hybrid") {
        pushProgress(
          "模板校验后回退到 LLM",
          data.template_id ? `模板 ${data.template_id} 未完全通过校验，已自动切换到 LLM` : "模板未通过校验，已自动切换到 LLM",
          "loading"
        );
      } else if (data.extractor_type === "llm") {
        pushProgress(
          "已调用 LLM",
          "当前页面未命中可直接复用的正式模板，已走 LLM 抽取流程",
          "loading"
        );
      }

      if (data.drift_detected) {
        pushProgress("检测到模板漂移", "页面结构与历史模板存在偏移，系统已启动回退处理", "error");
      }
      if (debugTrace.template_candidate_path) {
        pushProgress("已生成候选模板", "当前抽取样本已沉淀为候选模板，便于后续晋升固化", "success");
      }
      if (debugTrace.solidified_template_id) {
        pushProgress("已自动固化模板", `生成正式模板 ${debugTrace.solidified_template_id}`, "success");
      }
      if (data.status === "failed") {
        pushProgress("解析失败", "服务已返回失败状态，请查看结果 JSON 和详情区域", "error");
        return;
      }
      pushProgress(
        "解析完成",
        data.page_type ? `页面类型：${data.page_type}` : "已返回结构化结果",
        "success"
      );
    }

    function paginate(items, page, pageSize) {
      const totalPages = Math.max(1, Math.ceil(items.length / pageSize));
      const safePage = Math.min(Math.max(1, page), totalPages);
      const start = (safePage - 1) * pageSize;
      return {
        items: items.slice(start, start + pageSize),
        page: safePage,
        totalPages
      };
    }

    function getFilteredTemplates() {
      const search = templateSearch.value.trim().toLowerCase();
      const status = templateStatusFilter.value;
      return state.templates.filter((item) => {
        if (status && item.lifecycle_status !== status) return false;
        if (!search) return true;
        const haystack = [item.template_id, item.site_id, item.template_key, item.scenario, item.page_type]
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
      const pageSize = Number(templatePageSize.value || 10);
      const view = paginate(filtered, state.templatePage, pageSize);
      state.templatePage = view.page;
      templateMeta.textContent = `共 ${filtered.length} 个模板，已选 ${state.selectedTemplateIds.size} 个。`;
      templatePagerText.textContent = `第 ${view.page} / ${view.totalPages} 页`;
      templatePrevBtn.disabled = view.page <= 1;
      templateNextBtn.disabled = view.page >= view.totalPages;

      if (!filtered.length) {
        templatesTableBody.innerHTML = '<tr><td colspan="7"><div class="empty">没有符合条件的模板。</div></td></tr>';
        selectAllTemplates.checked = false;
        return;
      }

      templatesTableBody.innerHTML = view.items.map((item) => {
        const selected = state.selectedTemplateIds.has(item.template_id) ? "checked" : "";
        const requiredFields = Array.isArray(item.required_fields) ? item.required_fields.join(", ") : "";
        const statusClass = item.active ? "success" : item.lifecycle_status === "archived" ? "warning" : "muted";
        return `
          <tr>
            <td class="checkbox-cell"><input type="checkbox" data-template-checkbox="${escapeHtml(item.template_id)}" ${selected} /></td>
            <td>
              <div class="row-title">${escapeHtml(item.template_id)}</div>
              <div class="row-subtitle">${escapeHtml(item.template_key || "-")}</div>
            </td>
            <td>
              <div>${escapeHtml(item.site_id)}</div>
              <div class="row-subtitle">${escapeHtml(item.scenario)}</div>
            </td>
            <td><span class="pill ${statusClass}">${escapeHtml(item.lifecycle_status)}</span></td>
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

      templatesTableBody.querySelectorAll("[data-template-checkbox]").forEach((checkbox) => {
        checkbox.addEventListener("change", () => {
          if (checkbox.checked) {
            state.selectedTemplateIds.add(checkbox.dataset.templateCheckbox);
          } else {
            state.selectedTemplateIds.delete(checkbox.dataset.templateCheckbox);
          }
          renderTemplates();
        });
      });
      templatesTableBody.querySelectorAll("[data-template-detail]").forEach((button) => {
        button.addEventListener("click", () => showTemplateDetail(button.dataset.templateDetail));
      });
      templatesTableBody.querySelectorAll("[data-template-delete]").forEach((button) => {
        button.addEventListener("click", () => deleteTemplate(button.dataset.templateDelete));
      });

      const visibleIds = view.items.map((item) => item.template_id);
      selectAllTemplates.checked = visibleIds.length > 0 && visibleIds.every((id) => state.selectedTemplateIds.has(id));
    }

    function renderCandidates() {
      const filtered = getFilteredCandidates();
      const pageSize = Number(candidatePageSize.value || 10);
      const view = paginate(filtered, state.candidatePage, pageSize);
      state.candidatePage = view.page;
      candidateMeta.textContent = `共 ${filtered.length} 个候选模板。`;
      candidatePagerText.textContent = `第 ${view.page} / ${view.totalPages} 页`;
      candidatePrevBtn.disabled = view.page <= 1;
      candidateNextBtn.disabled = view.page >= view.totalPages;

      if (!filtered.length) {
        candidatesTableBody.innerHTML = '<tr><td colspan="5"><div class="empty">没有符合条件的候选模板。</div></td></tr>';
        return;
      }

      candidatesTableBody.innerHTML = view.items.map((item) => {
        const extractedFields = Array.isArray(item.extracted_fields) ? item.extracted_fields.join(", ") : "";
        const check = item.promotion_check || {};
        const promotable = Boolean(check.promotable);
        const reasons = Array.isArray(check.reasons) ? check.reasons : [];
        const reasonText = reasons.slice(0, 2).map((reason) => `<div>${escapeHtml(reason)}</div>`).join("");
        const statusPill = promotable
          ? '<span class="pill success">可晋升</span>'
          : '<span class="pill warning">不可晋升</span>';
        return `
          <tr>
            <td>
              <div class="row-title">${escapeHtml(item.candidate_id)}</div>
              <div class="row-subtitle">${escapeHtml(item.source_url || "-")}</div>
            </td>
            <td>
              <div>${escapeHtml(item.site_id)}</div>
              <div class="row-subtitle">${escapeHtml(item.scenario)}</div>
            </td>
            <td>
              ${statusPill}
              ${reasonText ? `<div class="reason-list">${reasonText}</div>` : '<div class="candidate-status">已具备正式模板固化条件</div>'}
            </td>
            <td>${escapeHtml(extractedFields || "-")}</td>
            <td>
              <div class="row-actions">
                <button class="ghost" type="button" data-candidate-detail="${escapeHtml(item.candidate_id)}">详情</button>
                <button class="secondary" type="button" data-candidate-promote="${escapeHtml(item.candidate_id)}" ${promotable ? "" : "disabled"}>晋升</button>
                <button class="warning-button" type="button" data-candidate-delete="${escapeHtml(item.candidate_id)}">删除</button>
              </div>
            </td>
          </tr>
        `;
      }).join("");

      candidatesTableBody.querySelectorAll("[data-candidate-detail]").forEach((button) => {
        button.addEventListener("click", () => showCandidateDetail(button.dataset.candidateDetail));
      });
      candidatesTableBody.querySelectorAll("[data-candidate-promote]").forEach((button) => {
        button.addEventListener("click", () => promoteCandidate(button.dataset.candidatePromote));
      });
      candidatesTableBody.querySelectorAll("[data-candidate-delete]").forEach((button) => {
        button.addEventListener("click", () => deleteCandidate(button.dataset.candidateDelete));
      });
    }

    async function loadTemplates() {
      try {
        const payload = await requestJson("/templates");
        state.templates = payload.templates || [];
        state.selectedTemplateIds.forEach((id) => {
          if (!state.templates.find((item) => item.template_id === id)) {
            state.selectedTemplateIds.delete(id);
          }
        });
        renderTemplates();
      } catch (error) {
        templatesTableBody.innerHTML = `<tr><td colspan="7"><div class="empty">模板加载失败: ${escapeHtml(String(error))}</div></td></tr>`;
      }
    }

    async function loadCandidates() {
      try {
        const payload = await requestJson("/template-candidates");
        state.candidates = payload.candidates || [];
        renderCandidates();
      } catch (error) {
        candidatesTableBody.innerHTML = `<tr><td colspan="5"><div class="empty">候选模板加载失败: ${escapeHtml(String(error))}</div></td></tr>`;
      }
    }

    async function showTemplateDetail(templateId) {
      try {
        const payload = await requestJson(`/templates/${encodeURIComponent(templateId)}`);
        setDetail(`模板 ${templateId}`, payload, "这是正式模板的完整 manifest。", buildDetailSummary(payload));
      } catch (error) {
        setDetail("模板详情失败", { error: String(error) }, "无法读取模板详情。");
      }
    }

    async function showCandidateDetail(candidateId) {
      try {
        const payload = await requestJson(`/template-candidates/${encodeURIComponent(candidateId)}`);
        setDetail(`候选 ${candidateId}`, payload, "这是候选模板的分析结果与 DSL 草案。", buildDetailSummary(payload));
      } catch (error) {
        setDetail("候选详情失败", { error: String(error) }, "无法读取候选模板详情。");
      }
    }

    async function deleteTemplate(templateId) {
      if (!await askConfirm("删除模板", `确认删除模板 ${templateId} 吗？`, "删除")) return;
      try {
        const payload = await requestNoContent(`/templates/${encodeURIComponent(templateId)}`, { method: "DELETE" });
        state.selectedTemplateIds.delete(templateId);
        setDetail(`删除 ${templateId}`, payload, "模板已删除。");
        await loadTemplates();
      } catch (error) {
        setDetail("模板删除失败", { error: String(error) }, "无法删除模板。");
      }
    }

    async function deleteSelectedTemplates() {
      const templateIds = Array.from(state.selectedTemplateIds);
      if (!templateIds.length) {
        setDetail("批量删除", { message: "未选择模板" }, "请先勾选需要删除的模板。");
        return;
      }
      if (!await askConfirm("批量删除模板", `确认删除选中的 ${templateIds.length} 个模板吗？`, "删除")) return;
      try {
        const payload = await requestJson("/templates/delete-batch", {
          method: "POST",
          headers: { "Content-Type": "application/json; charset=utf-8" },
          body: JSON.stringify({ template_ids: templateIds })
        });
        state.selectedTemplateIds.clear();
        setDetail("批量删除模板", payload, "选中的模板已删除。");
        await loadTemplates();
      } catch (error) {
        setDetail("批量删除失败", { error: String(error) }, "无法批量删除模板。");
      }
    }

    async function deleteCandidate(candidateId) {
      if (!await askConfirm("删除候选模板", `确认删除候选模板 ${candidateId} 吗？`, "删除")) return;
      try {
        const payload = await requestNoContent(`/template-candidates/${encodeURIComponent(candidateId)}`, { method: "DELETE" });
        setDetail(`删除候选 ${candidateId}`, payload, "候选模板已删除。");
        await loadCandidates();
      } catch (error) {
        setDetail("候选模板删除失败", { error: String(error) }, "无法删除候选模板。");
      }
    }

    async function promoteCandidate(candidateId) {
      const templateKeyInput = await askInput(
        "晋升候选模板",
        "请输入模板谱系标识 template_key。留空则按站点、场景、页面类型和结构指纹自动生成。",
        ""
      );
      if (templateKeyInput === null) return;
      try {
        const payload = await requestJson(`/template-candidates/${encodeURIComponent(candidateId)}/promote`, {
          method: "POST",
          headers: { "Content-Type": "application/json; charset=utf-8" },
          body: JSON.stringify({
            template_key: templateKeyInput.trim() || undefined,
            deactivate_previous_versions: true
          })
        });
        setDetail(`晋升 ${candidateId}`, payload, "候选模板已晋升为正式模板。");
        await Promise.all([loadTemplates(), loadCandidates()]);
      } catch (error) {
        setDetail("候选晋升失败", { error: String(error) }, "候选模板当前不满足晋升条件，请先查看右侧详情或表格中的不可晋升原因。");
      }
    }

    sampleBtn.addEventListener("click", () => {
      urlInput.value = "https://example.com/article/123";
      promptInput.value = "提取页面中的标题、摘要、作者、发布时间和正文要点。";
      htmlInput.value = "<html><head><title>示例页面</title><meta name=\\"description\\" content=\\"这是一个示例摘要\\"></head><body><main><h1>示例标题</h1><article><p>这里是正文。</p></article></main></body></html>";
      state.importedFileName = "";
      resetProgress();
      pushProgress("已填充示例数据", "已写入示例 URL、需求和 HTML，可直接开始解析", "success");
    });

    clearBtn.addEventListener("click", () => {
      urlInput.value = "";
      htmlInput.value = "";
      promptInput.value = "提取页面中与用户需求最相关的结构化信息，并尽量输出中文字段和值。";
      state.importedFileName = "";
      resultBox.textContent = JSON.stringify({ message: "执行后会在这里显示 JSON 结果。" }, null, 2);
      setStatus("", "idle");
      resetProgress();
    });

    fileInput.addEventListener("change", async (event) => {
      const [file] = event.target.files;
      if (!file) return;
      htmlInput.value = await file.text();
      state.importedFileName = file.name;
      setStatus(`已导入文件: ${file.name}`, "success");
      resetProgress();
      pushProgress("已导入 HTML 文件", `${file.name} · ${Math.max(1, Math.round(file.size / 1024))} KB`, "success");
    });

    extractBtn.addEventListener("click", async () => {
      const payload = {
        url: urlInput.value.trim(),
        user_prompt: promptInput.value.trim(),
        raw_html: htmlInput.value
      };
      if (!payload.raw_html.trim()) {
        setStatus("请先提供网页源码。", "error");
        pushProgress("缺少网页源码", "请先粘贴 HTML 或导入本地 HTML 文件", "error");
        return;
      }
      resetProgress();
      if (state.importedFileName) {
        pushProgress("输入源已就绪", `导入文件：${state.importedFileName}`, "success");
      } else {
        pushProgress("输入源已就绪", `已提供 ${payload.raw_html.length} 个字符的网页源码`, "success");
      }
      if (payload.url) {
        pushProgress("页面来源", payload.url, "");
      }
      pushProgress("开始解析", "正在请求 /extract 接口", "loading");
      setStatus("正在调用 /extract ...", "loading");
      extractBtn.disabled = true;
      try {
        const response = await fetch("/extract", {
          method: "POST",
          headers: { "Content-Type": "application/json; charset=utf-8" },
          body: JSON.stringify(payload)
        });
        const data = await response.json();
        resultBox.textContent = JSON.stringify(data, null, 2);
        pushProgress("服务已返回响应", `HTTP ${response.status}`, response.ok ? "success" : "error");
        if (!response.ok) {
          setStatus(`请求失败: HTTP ${response.status}`, "error");
          pushProgress("请求失败", String(data.error || `HTTP ${response.status}`), "error");
          return;
        }
        pushResponseProgress(data);
        setStatus("解析完成。", data.status === "failed" ? "error" : "success");
        await Promise.all([loadTemplates(), loadCandidates()]);
      } catch (error) {
        resultBox.textContent = JSON.stringify({ error: String(error) }, null, 2);
        setStatus("请求异常，请检查服务日志。", "error");
        pushProgress("请求异常", String(error), "error");
      } finally {
        extractBtn.disabled = false;
      }
    });

    [templateSearch, templateStatusFilter, templatePageSize].forEach((node) => {
      node.addEventListener("input", () => {
        state.templatePage = 1;
        renderTemplates();
      });
      node.addEventListener("change", () => {
        state.templatePage = 1;
        renderTemplates();
      });
    });

    [candidateSearch, candidatePageSize].forEach((node) => {
      node.addEventListener("input", () => {
        state.candidatePage = 1;
        renderCandidates();
      });
      node.addEventListener("change", () => {
        state.candidatePage = 1;
        renderCandidates();
      });
    });

    templatePrevBtn.addEventListener("click", () => {
      state.templatePage -= 1;
      renderTemplates();
    });
    templateNextBtn.addEventListener("click", () => {
      state.templatePage += 1;
      renderTemplates();
    });
    candidatePrevBtn.addEventListener("click", () => {
      state.candidatePage -= 1;
      renderCandidates();
    });
    candidateNextBtn.addEventListener("click", () => {
      state.candidatePage += 1;
      renderCandidates();
    });
    selectAllTemplates.addEventListener("change", () => {
      const filtered = getFilteredTemplates();
      const pageSize = Number(templatePageSize.value || 10);
      const view = paginate(filtered, state.templatePage, pageSize);
      view.items.forEach((item) => {
        if (selectAllTemplates.checked) {
          state.selectedTemplateIds.add(item.template_id);
        } else {
          state.selectedTemplateIds.delete(item.template_id);
        }
      });
      renderTemplates();
    });

    deleteSelectedTemplatesBtn.addEventListener("click", deleteSelectedTemplates);
    refreshTemplatesBtn.addEventListener("click", loadTemplates);
    refreshCandidatesBtn.addEventListener("click", loadCandidates);
    modalCancelBtn.addEventListener("click", () => closeDialog({ confirmed: false }));
    modalConfirmBtn.addEventListener("click", () => {
      closeDialog({ confirmed: true, value: modalInput.value });
    });
    modalBackdrop.addEventListener("click", (event) => {
      if (event.target === modalBackdrop) {
        closeDialog({ confirmed: false });
      }
    });

    loadTemplates();
    loadCandidates();
  </script>
</body>
</html>
"""
