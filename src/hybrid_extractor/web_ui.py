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
    .hero, .workspace, .lower-grid { display: grid; gap: 18px; }
    .hero { grid-template-columns: 1.3fr 0.9fr; margin-bottom: 18px; }
    .workspace { grid-template-columns: minmax(340px, 430px) minmax(0, 1fr); align-items: start; }
    .lower-grid { margin-top: 18px; grid-template-columns: minmax(0, 1.25fr) minmax(340px, 0.75fr); }
    .library-stack { display: grid; gap: 18px; }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      backdrop-filter: blur(10px);
    }
    .hero-copy, .hero-meta, .form-panel, .result-panel, .library-panel, .detail-panel { padding: 22px 28px; }
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
    .html-box { min-height: 260px; font-family: var(--mono); font-size: 12px; line-height: 1.55; }
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
      min-height: 360px;
      overflow: auto;
      background: #0f1722;
      color: #d7f8f0;
      font-family: var(--mono);
      font-size: 12px;
      line-height: 1.6;
    }
    .detail-panel pre { min-height: 620px; background: #121826; }
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
    }
    .row-subtitle {
      color: var(--muted);
      font-size: 12px;
      word-break: break-word;
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
    }
    .table-meta {
      font-size: 12px;
      margin-bottom: 10px;
    }
    .hidden { display: none !important; }
    @media (max-width: 1080px) {
      .hero, .workspace, .lower-grid { grid-template-columns: 1fr; }
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

      <div class="panel result-panel">
        <div class="result-toolbar">
          <h2 class="section-title" style="margin: 0;">解析结果</h2>
          <div class="badge" id="statusBadge">等待执行</div>
        </div>
        <div class="status" id="statusLine"></div>
        <pre id="resultBox">{
  "message": "执行后会在这里显示 JSON 结果。"
}</pre>
      </div>
    </section>

    <section class="lower-grid">
      <div class="library-stack">
        <div class="panel library-panel">
          <div class="result-toolbar">
            <h2 class="section-title" style="margin: 0;">正式模板</h2>
            <div class="toolbar compact">
              <button class="ghost" id="refreshTemplatesBtn" type="button">刷新模板</button>
              <button class="danger" id="deleteSelectedTemplatesBtn" type="button">删除选中</button>
            </div>
          </div>
          <div class="mini-note">模板列表支持搜索、筛选和分页，避免模板数量变大后整页铺开。</div>
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
          <div class="mini-note">候选模板保留首次 LLM 成功抽取后的分析结果与 DSL 草案。</div>
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
      </div>

      <div class="panel detail-panel">
        <div class="result-toolbar">
          <h2 class="section-title" style="margin: 0;">详情</h2>
          <div class="badge" id="detailBadge">未选择</div>
        </div>
        <div class="status" id="detailStatus">点击表格中的详情按钮查看模板或候选模板内容。</div>
        <pre id="detailBox">{
  "message": "详情会显示在这里。"
}</pre>
      </div>
    </section>
  </div>

  <script>
    const state = {
      templates: [],
      candidates: [],
      selectedTemplateIds: new Set(),
      templatePage: 1,
      candidatePage: 1
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
    const detailBox = document.getElementById("detailBox");
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

    function setDetail(label, payload, message) {
      detailBadge.textContent = label;
      detailStatus.textContent = message || "";
      detailBox.textContent = JSON.stringify(payload, null, 2);
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
        candidatesTableBody.innerHTML = '<tr><td colspan="4"><div class="empty">没有符合条件的候选模板。</div></td></tr>';
        return;
      }

      candidatesTableBody.innerHTML = view.items.map((item) => {
        const extractedFields = Array.isArray(item.extracted_fields) ? item.extracted_fields.join(", ") : "";
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
            <td>${escapeHtml(extractedFields || "-")}</td>
            <td>
              <div class="row-actions">
                <button class="ghost" type="button" data-candidate-detail="${escapeHtml(item.candidate_id)}">详情</button>
                <button class="secondary" type="button" data-candidate-promote="${escapeHtml(item.candidate_id)}">晋升</button>
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
        candidatesTableBody.innerHTML = `<tr><td colspan="4"><div class="empty">候选模板加载失败: ${escapeHtml(String(error))}</div></td></tr>`;
      }
    }

    async function showTemplateDetail(templateId) {
      try {
        const payload = await requestJson(`/templates/${encodeURIComponent(templateId)}`);
        setDetail(`模板 ${templateId}`, payload, "这是正式模板的完整 manifest。");
      } catch (error) {
        setDetail("模板详情失败", { error: String(error) }, "无法读取模板详情。");
      }
    }

    async function showCandidateDetail(candidateId) {
      try {
        const payload = await requestJson(`/template-candidates/${encodeURIComponent(candidateId)}`);
        setDetail(`候选 ${candidateId}`, payload, "这是候选模板的分析结果与 DSL 草案。");
      } catch (error) {
        setDetail("候选详情失败", { error: String(error) }, "无法读取候选模板详情。");
      }
    }

    async function deleteTemplate(templateId) {
      if (!window.confirm(`确认删除模板 ${templateId} 吗？`)) return;
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
      if (!window.confirm(`确认删除选中的 ${templateIds.length} 个模板吗？`)) return;
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
      if (!window.confirm(`确认删除候选模板 ${candidateId} 吗？`)) return;
      try {
        const payload = await requestNoContent(`/template-candidates/${encodeURIComponent(candidateId)}`, { method: "DELETE" });
        setDetail(`删除候选 ${candidateId}`, payload, "候选模板已删除。");
        await loadCandidates();
      } catch (error) {
        setDetail("候选模板删除失败", { error: String(error) }, "无法删除候选模板。");
      }
    }

    async function promoteCandidate(candidateId) {
      const templateKeyInput = window.prompt("请输入模板谱系标识 template_key（留空则按站点/场景自动生成）", "");
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
        setDetail("候选晋升失败", { error: String(error) }, "无法晋升候选模板。");
      }
    }

    sampleBtn.addEventListener("click", () => {
      urlInput.value = "https://example.com/article/123";
      promptInput.value = "提取页面中的标题、摘要、作者、发布时间和正文要点。";
      htmlInput.value = "<html><head><title>示例页面</title><meta name=\\"description\\" content=\\"这是一个示例摘要\\"></head><body><main><h1>示例标题</h1><article><p>这里是正文。</p></article></main></body></html>";
    });

    clearBtn.addEventListener("click", () => {
      urlInput.value = "";
      htmlInput.value = "";
      resultBox.textContent = JSON.stringify({ message: "执行后会在这里显示 JSON 结果。" }, null, 2);
      setStatus("", "idle");
    });

    fileInput.addEventListener("change", async (event) => {
      const [file] = event.target.files;
      if (!file) return;
      htmlInput.value = await file.text();
      setStatus(`已导入文件: ${file.name}`, "success");
    });

    extractBtn.addEventListener("click", async () => {
      const payload = {
        url: urlInput.value.trim(),
        user_prompt: promptInput.value.trim(),
        raw_html: htmlInput.value
      };
      if (!payload.raw_html.trim()) {
        setStatus("请先提供网页源码。", "error");
        return;
      }
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
        if (!response.ok) {
          setStatus(`请求失败: HTTP ${response.status}`, "error");
          return;
        }
        setStatus("解析完成。", data.status === "failed" ? "error" : "success");
        await Promise.all([loadTemplates(), loadCandidates()]);
      } catch (error) {
        resultBox.textContent = JSON.stringify({ error: String(error) }, null, 2);
        setStatus("请求异常，请检查服务日志。", "error");
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

    loadTemplates();
    loadCandidates();
  </script>
</body>
</html>
"""
