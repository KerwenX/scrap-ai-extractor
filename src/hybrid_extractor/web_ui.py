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
      --bg: linear-gradient(135deg, #f5efe6 0%, #eef4ef 45%, #e7edf6 100%);
      --panel: rgba(255, 255, 255, 0.9);
      --text: #18212b;
      --muted: #607080;
      --line: rgba(24, 33, 43, 0.12);
      --accent: #0f6e64;
      --accent-strong: #0b4d46;
      --danger: #a23d3d;
      --warning: #9a6a10;
      --radius: 22px;
      --shadow: 0 20px 48px rgba(18, 26, 34, 0.12);
      --mono: "Cascadia Code", Consolas, monospace;
      --sans: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: var(--sans);
      color: var(--text);
      background: var(--bg);
    }
    .shell {
      max-width: 1480px;
      margin: 0 auto;
      padding: 24px 18px 40px;
    }
    .hero {
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      gap: 18px;
      margin-bottom: 18px;
    }
    .workspace {
      display: grid;
      grid-template-columns: minmax(360px, 430px) minmax(0, 1fr);
      gap: 18px;
      align-items: start;
    }
    .stack {
      display: grid;
      gap: 18px;
      min-width: 0;
      align-content: start;
    }
    .library {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 18px;
      margin-top: 18px;
    }
    .panel {
      min-width: 0;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      backdrop-filter: blur(8px);
    }
    .pad { padding: 22px 24px; }
    h1, h2, h3 { margin: 0; }
    h1 {
      font-size: clamp(28px, 4vw, 46px);
      line-height: 1.05;
      letter-spacing: -0.04em;
      margin-bottom: 12px;
    }
    .subtitle {
      margin: 0;
      color: var(--muted);
      line-height: 1.75;
      max-width: 58ch;
      font-size: 15px;
    }
    .meta-grid {
      display: grid;
      gap: 12px;
      align-content: center;
    }
    .stat {
      padding: 14px 16px;
      border-radius: 18px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.68);
    }
    .stat small {
      display: block;
      color: var(--muted);
      margin-bottom: 6px;
      font-size: 12px;
    }
    .stat strong {
      font-size: 15px;
      font-weight: 700;
    }
    .section-title {
      margin-bottom: 16px;
      font-size: 18px;
      font-weight: 700;
    }
    .field { margin-bottom: 14px; }
    label {
      display: block;
      margin-bottom: 8px;
      font-size: 13px;
      color: var(--muted);
    }
    input[type="text"], textarea, select {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 12px 14px;
      background: rgba(255, 255, 255, 0.84);
      color: var(--text);
      font: inherit;
    }
    textarea {
      min-height: 140px;
      resize: vertical;
    }
    .html-box {
      min-height: 240px;
      font-family: var(--mono);
      font-size: 12px;
      line-height: 1.55;
    }
    .toolbar, .actions, .pager, .filters {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
    }
    .toolbar, .filters, .table-meta, .status-line { margin-bottom: 12px; }
    .actions { margin-top: 18px; }
    .spacer { flex: 1 1 auto; }
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
    button:disabled { opacity: 0.6; cursor: default; }
    .primary {
      color: white;
      background: linear-gradient(135deg, var(--accent) 0%, #2c8d78 100%);
      box-shadow: 0 14px 28px rgba(15, 110, 100, 0.22);
    }
    .secondary, .ghost, .button-like {
      color: var(--text);
      background: rgba(255,255,255,0.85);
      border: 1px solid var(--line);
    }
    .danger {
      color: white;
      background: linear-gradient(135deg, #903232 0%, #c65252 100%);
    }
    .warning-button {
      color: #7f5410;
      background: rgba(154, 106, 16, 0.1);
      border: 1px solid rgba(154, 106, 16, 0.18);
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
    }
    .pill {
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 5px 10px;
      font-size: 11px;
      font-weight: 700;
    }
    .pill.success { background: rgba(15, 110, 100, 0.12); color: var(--accent-strong); }
    .pill.warning { background: rgba(154, 106, 16, 0.12); color: var(--warning); }
    .pill.muted { background: rgba(24, 33, 43, 0.08); color: var(--muted); }
    .progress-list {
      display: grid;
      gap: 10px;
      margin: 0;
      padding: 0;
      list-style: none;
    }
    .progress-item {
      padding: 12px 14px;
      border-radius: 16px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.65);
    }
    .progress-item strong {
      display: block;
      margin-bottom: 4px;
      font-size: 13px;
    }
    .progress-item span {
      display: block;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.55;
      word-break: break-word;
    }
    .progress-item.success strong { color: var(--accent-strong); }
    .progress-item.error strong { color: var(--danger); }
    .progress-item.loading strong { color: #0a5c99; }
    pre {
      margin: 0;
      padding: 18px;
      border-radius: 18px;
      background: #0f1722;
      color: #d7f8f0;
      font-family: var(--mono);
      font-size: 12px;
      line-height: 1.6;
      white-space: pre-wrap;
      word-break: break-word;
      max-height: 440px;
      overflow: auto;
    }
    .detail-summary {
      margin-bottom: 14px;
      display: grid;
      gap: 12px;
    }
    .summary-card {
      padding: 14px 16px;
      border-radius: 16px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.72);
    }
    .summary-title {
      margin-bottom: 10px;
      font-size: 14px;
      font-weight: 700;
    }
    .summary-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 10px;
    }
    .summary-item {
      min-width: 0;
      padding: 10px 12px;
      border-radius: 14px;
      background: rgba(15, 23, 34, 0.04);
      border: 1px solid rgba(15, 23, 34, 0.06);
    }
    .summary-item small {
      display: block;
      margin-bottom: 6px;
      font-size: 11px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .summary-item div {
      font-size: 13px;
      line-height: 1.6;
      word-break: break-word;
    }
    .empty {
      padding: 18px;
      border-radius: 18px;
      border: 1px dashed var(--line);
      color: var(--muted);
      background: rgba(255,255,255,0.52);
      font-size: 13px;
    }
    .table-wrap {
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: rgba(255,255,255,0.6);
    }
    table {
      width: 100%;
      min-width: 920px;
      border-collapse: collapse;
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
      background: rgba(244, 248, 250, 0.96);
      color: var(--muted);
      text-transform: uppercase;
      font-size: 12px;
      letter-spacing: 0.04em;
      z-index: 1;
    }
    tr:last-child td { border-bottom: 0; }
    .row-title {
      font-weight: 700;
      margin-bottom: 4px;
      word-break: break-word;
    }
    .row-subtitle, .table-meta {
      color: var(--muted);
      font-size: 12px;
      word-break: break-word;
    }
    .row-actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    .checkbox-cell {
      width: 40px;
    }
    .reason-list {
      margin-top: 6px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.55;
    }
    .compact { width: auto; min-width: 120px; }
    @media (max-width: 1100px) {
      .hero, .workspace, .library { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div class="panel pad">
        <h1>混合网页解析器</h1>
        <p class="subtitle">输入 URL、网页源码和自然语言抽取需求。系统优先复用正式模板，命中失败时自动回退到 LLM，并将成功样本沉淀为候选模板或升级现有模板。</p>
      </div>
      <div class="panel pad">
        <div class="meta-grid">
          <div class="stat"><small>运行模式</small><strong>模板优先 / LLM 回退</strong></div>
          <div class="stat"><small>模板策略</small><strong>复用、升级、新建三态闭环</strong></div>
          <div class="stat"><small>调试视图</small><strong>展示模板命中、进度、候选与正式模板详情</strong></div>
        </div>
      </div>
    </section>

    <section class="workspace">
      <div class="panel pad">
        <h2 class="section-title">解析输入</h2>
        <div class="field">
          <label for="urlInput">URL</label>
          <input id="urlInput" type="text" placeholder="https://example.com/page/123" />
        </div>
        <div class="field">
          <label for="promptInput">抽取需求</label>
          <textarea id="promptInput">提取页面中与用户需求最相关的结构化信息，并尽量输出中文字段和中文值。</textarea>
        </div>
        <div class="field">
          <label for="htmlInput">网页源码</label>
          <textarea id="htmlInput" class="html-box" placeholder="粘贴 HTML，或点击下方导入本地 HTML 文件。"></textarea>
        </div>
        <div class="actions">
          <button id="extractBtn" class="primary" type="button">开始解析</button>
          <button id="sampleBtn" class="secondary" type="button">填充示例</button>
          <button id="clearBtn" class="ghost" type="button">清空</button>
          <label class="button-like upload secondary" for="fileInput">导入 HTML 文件
            <input id="fileInput" type="file" accept=".html,.htm,text/html" />
          </label>
        </div>
        <div id="statusLine" class="status-line"></div>
      </div>

      <div class="stack">
        <div class="panel pad">
          <div class="toolbar">
            <h2 class="section-title" style="margin-bottom:0;">解析进度</h2>
            <div class="spacer"></div>
            <button id="clearProgressBtn" class="ghost" type="button">清空进度</button>
          </div>
          <ul id="progressList" class="progress-list"></ul>
        </div>
        <div class="panel pad">
          <div class="toolbar">
            <h2 class="section-title" style="margin-bottom:0;">解析结果</h2>
          </div>
          <pre id="resultBox">{
  "message": "执行后会在这里显示 JSON 结果。"
}</pre>
        </div>
        <div class="panel pad">
          <div class="toolbar">
            <h2 id="detailTitle" class="section-title" style="margin-bottom:0;">详情面板</h2>
          </div>
          <div id="detailSummary" class="detail-summary">
            <div class="empty">这里会展示模板命中、页面指纹、候选规则和正式模板详情。</div>
          </div>
          <pre id="detailBox">{
  "message": "选择模板、候选或执行解析后，会在这里展示原始详情对象。"
}</pre>
        </div>
      </div>
    </section>

    <section class="library">
      <div class="panel pad">
        <div class="toolbar">
          <h2 class="section-title" style="margin-bottom:0;">正式模板</h2>
          <div class="spacer"></div>
          <button id="refreshTemplatesBtn" class="ghost" type="button">刷新</button>
          <button id="deleteSelectedTemplatesBtn" class="warning-button" type="button">删除选中</button>
        </div>
        <div class="filters">
          <input id="templateSearch" type="text" placeholder="搜索 template_id / site_id / template_key" />
          <select id="templateStatusFilter" class="compact">
            <option value="">全部状态</option>
            <option value="active">active</option>
            <option value="deprecated">deprecated</option>
            <option value="archived">archived</option>
            <option value="draft">draft</option>
          </select>
          <select id="templatePageSize" class="compact">
            <option value="5">5 / 页</option>
            <option value="10" selected>10 / 页</option>
            <option value="20">20 / 页</option>
          </select>
        </div>
        <div id="templateMeta" class="table-meta"></div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th class="checkbox-cell"><input id="selectAllTemplates" type="checkbox" /></th>
                <th>模板</th>
                <th>站点</th>
                <th>状态</th>
                <th>版本</th>
                <th>字段</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody id="templatesTableBody"></tbody>
          </table>
        </div>
        <div class="pager">
          <button id="templatePrevBtn" class="ghost" type="button">上一页</button>
          <div id="templatePagerText" class="table-meta"></div>
          <button id="templateNextBtn" class="ghost" type="button">下一页</button>
        </div>
      </div>

      <div class="panel pad">
        <div class="toolbar">
          <h2 class="section-title" style="margin-bottom:0;">候选模板</h2>
          <div class="spacer"></div>
          <button id="refreshCandidatesBtn" class="ghost" type="button">刷新</button>
        </div>
        <div class="filters">
          <input id="candidateSearch" type="text" placeholder="搜索 candidate_id / site_id / source_url" />
          <select id="candidatePageSize" class="compact">
            <option value="5">5 / 页</option>
            <option value="10" selected>10 / 页</option>
            <option value="20">20 / 页</option>
          </select>
        </div>
        <div id="candidateMeta" class="table-meta"></div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>候选模板</th>
                <th>站点 / 场景</th>
                <th>状态</th>
                <th>字段</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody id="candidatesTableBody"></tbody>
          </table>
        </div>
        <div class="pager">
          <button id="candidatePrevBtn" class="ghost" type="button">上一页</button>
          <div id="candidatePagerText" class="table-meta"></div>
          <button id="candidateNextBtn" class="ghost" type="button">下一页</button>
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
      importedFileName: ""
    };

    const urlInput = document.getElementById("urlInput");
    const promptInput = document.getElementById("promptInput");
    const htmlInput = document.getElementById("htmlInput");
    const fileInput = document.getElementById("fileInput");
    const extractBtn = document.getElementById("extractBtn");
    const sampleBtn = document.getElementById("sampleBtn");
    const clearBtn = document.getElementById("clearBtn");
    const clearProgressBtn = document.getElementById("clearProgressBtn");
    const statusLine = document.getElementById("statusLine");
    const progressList = document.getElementById("progressList");
    const resultBox = document.getElementById("resultBox");
    const detailTitle = document.getElementById("detailTitle");
    const detailSummary = document.getElementById("detailSummary");
    const detailBox = document.getElementById("detailBox");

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

    function escapeHtml(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }

    async function requestJson(url, options) {
      const response = await fetch(url, options);
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.error || payload.details || `HTTP ${response.status}`);
      }
      return payload;
    }

    async function requestNoContent(url, options) {
      const response = await fetch(url, options);
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.error || payload.details || `HTTP ${response.status}`);
      }
      return payload;
    }

    function setStatus(message, type = "idle") {
      statusLine.textContent = message || "";
      statusLine.style.color = type === "error" ? "var(--danger)" : type === "success" ? "var(--accent-strong)" : "var(--muted)";
    }

    function resetProgress() {
      progressList.innerHTML = "";
    }

    function pushProgress(title, detail, level = "success") {
      const li = document.createElement("li");
      li.className = `progress-item ${level}`;
      li.innerHTML = `<strong>${escapeHtml(title)}</strong><span>${escapeHtml(detail)}</span>`;
      progressList.prepend(li);
    }

    function renderSummaryItem(label, value) {
      return `<div class="summary-item"><small>${escapeHtml(label)}</small><div>${value}</div></div>`;
    }

    function renderTokenList(items, pillClass = "muted") {
      if (!Array.isArray(items) || !items.length) {
        return '<span class="pill muted">-</span>';
      }
      return items.map((item) => `<span class="pill ${pillClass}">${escapeHtml(item)}</span>`).join(" ");
    }

    function renderFingerprintCard(fingerprint) {
      if (!fingerprint) return "";
      return `
        <div class="summary-card">
          <div class="summary-title">页面指纹</div>
          <div class="summary-grid">
            ${renderSummaryItem("DOM 签名", escapeHtml(fingerprint.dom_signature || "-"))}
            ${renderSummaryItem("标题锚点", renderTokenList(fingerprint.headings || []))}
            ${renderSummaryItem("关键 ID", renderTokenList(fingerprint.key_ids || []))}
            ${renderSummaryItem("关键 Class", renderTokenList(fingerprint.key_classes || []))}
          </div>
        </div>
      `;
    }

    function renderPlanCard(plan, title) {
      if (!plan || !Array.isArray(plan.fields)) return "";
      return `
        <div class="summary-card">
          <div class="summary-title">${escapeHtml(title)}</div>
          <div class="summary-grid">
            ${plan.fields.map((field) => renderSummaryItem(
              field.field_name || "-",
              `${escapeHtml((field.selectors || []).map((selector) => `${selector.kind}:${selector.value}`).join(" | ") || "-")}`
            )).join("")}
          </div>
        </div>
      `;
    }

    function renderPromotionCard(check) {
      if (!check) return "";
      const reasons = Array.isArray(check.reasons) ? check.reasons : [];
      const actionLabel = check.action_label || (check.promotable ? "可晋升" : "不可晋升");
      const pill = check.promotable
        ? `<span class="pill success">${escapeHtml(actionLabel)}</span>`
        : check.action === "reuse"
          ? `<span class="pill muted">${escapeHtml(actionLabel)}</span>`
          : `<span class="pill warning">${escapeHtml(actionLabel)}</span>`;
      return `
        <div class="summary-card">
          <div class="summary-title">晋升检查</div>
          <div class="summary-grid">
            ${renderSummaryItem("当前动作", pill)}
            ${renderSummaryItem("字段规则", check.has_plan ? '<span class="pill success">已生成</span>' : '<span class="pill warning">缺失</span>')}
            ${renderSummaryItem("已抽字段", escapeHtml(String(check.extracted_field_count ?? 0)))}
            ${renderSummaryItem("候选规则数", escapeHtml(String(check.candidate_field_count ?? 0)))}
            ${renderSummaryItem("既有规则数", escapeHtml(String(check.existing_field_count ?? 0)))}
            ${renderSummaryItem("关联模板", escapeHtml(check.existing_template_id || "-"))}
            ${renderSummaryItem("说明", escapeHtml(check.detail || "-"))}
            ${renderSummaryItem("阻断原因", reasons.length ? renderTokenList(reasons, "warning") : "-")}
          </div>
        </div>
      `;
    }

    function buildDetailSummary(payload) {
      if (!payload || typeof payload !== "object") {
        return '<div class="empty">当前没有可展示的详情摘要。</div>';
      }
      const blocks = [];
      if (payload.fingerprint) blocks.push(renderFingerprintCard(payload.fingerprint));
      if (payload.promotion_check) blocks.push(renderPromotionCard(payload.promotion_check));
      if (payload.extraction_plan) blocks.push(renderPlanCard(payload.extraction_plan, "正式模板规则"));
      if (payload.proposed_plan) blocks.push(renderPlanCard(payload.proposed_plan, "候选模板规则"));
      if (!blocks.length) {
        return '<div class="empty">当前详情对象中没有可视化摘要信息。</div>';
      }
      return blocks.join("");
    }

    function setDetail(title, payload, summaryText = "", customSummaryHtml = "") {
      detailTitle.textContent = title;
      detailSummary.innerHTML = customSummaryHtml || `<div class="empty">${escapeHtml(summaryText || "无额外说明。")}</div>`;
      detailBox.textContent = JSON.stringify(payload, null, 2);
    }

    function pushResponseProgress(data) {
      if (!data || typeof data !== "object") return;
      const debugTrace = data.debug_trace || {};
      if (data.extractor_type === "deterministic") {
        pushProgress("命中正式模板", data.template_id ? `直接使用模板 ${data.template_id}` : "直接使用本地正式模板规则", "success");
      } else if (data.extractor_type === "hybrid") {
        pushProgress("模板校验后回退到 LLM", data.template_id ? `模板 ${data.template_id} 未完全通过校验，已自动切换到 LLM` : "模板未通过校验，已自动切换到 LLM", "loading");
      } else if (data.extractor_type === "llm") {
        pushProgress("已调用 LLM", "当前页面未命中可直接复用的正式模板，已进入 LLM 抽取流程", "loading");
      }
      if (data.drift_detected) {
        pushProgress("检测到模板漂移", "页面结构与历史模板存在偏移，系统已触发回退处理", "error");
      }
      if (debugTrace.template_candidate_path) {
        pushProgress("已生成候选模板", "当前成功样本已沉淀为候选模板，便于后续晋升或升级", "success");
      }
      if (debugTrace.solidified_template_id) {
        pushProgress("已固化模板", `生成正式模板 ${debugTrace.solidified_template_id}`, "success");
      }
      if (data.status === "failed") {
        pushProgress("解析失败", "服务返回失败状态，请查看结果 JSON 和详情面板", "error");
      } else {
        pushProgress("解析完成", data.page_type ? `页面类型：${data.page_type}` : "已返回结构化结果", "success");
      }
    }

    function paginate(items, page, pageSize) {
      const totalPages = Math.max(1, Math.ceil(items.length / pageSize));
      const safePage = Math.min(Math.max(1, page), totalPages);
      const start = (safePage - 1) * pageSize;
      return { items: items.slice(start, start + pageSize), page: safePage, totalPages };
    }

    function getFilteredTemplates() {
      const search = templateSearch.value.trim().toLowerCase();
      const status = templateStatusFilter.value;
      return state.templates.filter((item) => {
        if (status && item.lifecycle_status !== status) return false;
        if (!search) return true;
        const haystack = [item.template_id, item.site_id, item.template_key, item.scenario, item.page_type]
          .filter(Boolean).join(" ").toLowerCase();
        return haystack.includes(search);
      });
    }

    function getFilteredCandidates() {
      const search = candidateSearch.value.trim().toLowerCase();
      return state.candidates.filter((item) => {
        if (!search) return true;
        const haystack = [item.candidate_id, item.site_id, item.source_url, item.scenario]
          .filter(Boolean).join(" ").toLowerCase();
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
            <td><div class="row-title">${escapeHtml(item.template_id)}</div><div class="row-subtitle">${escapeHtml(item.template_key || "-")}</div></td>
            <td><div>${escapeHtml(item.site_id)}</div><div class="row-subtitle">${escapeHtml(item.scenario)}</div></td>
            <td><span class="pill ${statusClass}">${escapeHtml(item.lifecycle_status)}</span></td>
            <td>${escapeHtml(item.version || "-")}</td>
            <td>${escapeHtml(requiredFields || "-")}</td>
            <td><div class="row-actions">
              <button class="ghost" type="button" data-template-detail="${escapeHtml(item.template_id)}">详情</button>
              <button class="warning-button" type="button" data-template-delete="${escapeHtml(item.template_id)}">删除</button>
            </div></td>
          </tr>
        `;
      }).join("");

      templatesTableBody.querySelectorAll("[data-template-checkbox]").forEach((checkbox) => {
        checkbox.addEventListener("change", () => {
          if (checkbox.checked) state.selectedTemplateIds.add(checkbox.dataset.templateCheckbox);
          else state.selectedTemplateIds.delete(checkbox.dataset.templateCheckbox);
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
        const action = check.action || "blocked";
        const actionLabel = check.action_label || (promotable ? "可晋升" : "不可晋升");
        const statusPill = promotable
          ? `<span class="pill success">${escapeHtml(actionLabel)}</span>`
          : action === "reuse"
            ? `<span class="pill muted">${escapeHtml(actionLabel)}</span>`
            : `<span class="pill warning">${escapeHtml(actionLabel)}</span>`;
        const reasonParts = [];
        if (check.detail) reasonParts.push(`<div>${escapeHtml(check.detail)}</div>`);
        if (Array.isArray(check.reasons)) {
          reasonParts.push(...check.reasons.slice(0, 2).map((reason) => `<div>${escapeHtml(reason)}</div>`));
        }
        const actionButtonText = action === "upgrade" ? "升级" : "晋升";
        return `
          <tr>
            <td><div class="row-title">${escapeHtml(item.candidate_id)}</div><div class="row-subtitle">${escapeHtml(item.source_url || "-")}</div></td>
            <td><div>${escapeHtml(item.site_id)}</div><div class="row-subtitle">${escapeHtml(item.scenario)}</div></td>
            <td>${statusPill}${reasonParts.length ? `<div class="reason-list">${reasonParts.join("")}</div>` : '<div class="reason-list">已具备正式模板固化条件。</div>'}</td>
            <td>${escapeHtml(extractedFields || "-")}</td>
            <td><div class="row-actions">
              <button class="ghost" type="button" data-candidate-detail="${escapeHtml(item.candidate_id)}">详情</button>
              <button class="secondary" type="button" data-candidate-promote="${escapeHtml(item.candidate_id)}" ${promotable ? "" : "disabled"}>${escapeHtml(actionButtonText)}</button>
              <button class="warning-button" type="button" data-candidate-delete="${escapeHtml(item.candidate_id)}">删除</button>
            </div></td>
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
        setDetail(`模板 ${templateId}`, payload, "", buildDetailSummary(payload));
      } catch (error) {
        setDetail("模板详情失败", { error: String(error) }, "无法读取模板详情。");
      }
    }

    async function showCandidateDetail(candidateId) {
      try {
        const payload = await requestJson(`/template-candidates/${encodeURIComponent(candidateId)}`);
        setDetail(`候选 ${candidateId}`, payload, "", buildDetailSummary(payload));
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
      const templateKeyInput = window.prompt("请输入模板族标识 template_key。留空则自动沿用既有模板族或按页面特征生成。", "");
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
        setDetail(`晋升 ${candidateId}`, payload, "候选模板已固化为正式模板。", buildDetailSummary(payload));
        await Promise.all([loadTemplates(), loadCandidates()]);
      } catch (error) {
        setDetail("候选晋升失败", { error: String(error) }, "候选模板当前不满足晋升条件。");
      }
    }

    sampleBtn.addEventListener("click", () => {
      urlInput.value = "https://example.com/article/123";
      promptInput.value = "提取页面中的标题、摘要、作者、发布时间和正文要点。";
      htmlInput.value = "<html><head><title>示例页面</title><meta name=\\"description\\" content=\\"这是一个示例摘要\\"></head><body><main><h1>示例标题</h1><article><p>这里是正文。</p></article></main></body></html>";
      state.importedFileName = "";
      setStatus("已填充示例数据。", "success");
      resetProgress();
      pushProgress("已填充示例数据", "可直接点击开始解析。", "success");
    });

    clearBtn.addEventListener("click", () => {
      urlInput.value = "";
      htmlInput.value = "";
      promptInput.value = "提取页面中与用户需求最相关的结构化信息，并尽量输出中文字段和中文值。";
      state.importedFileName = "";
      resultBox.textContent = JSON.stringify({ message: "执行后会在这里显示 JSON 结果。" }, null, 2);
      setStatus("", "idle");
      resetProgress();
    });

    clearProgressBtn.addEventListener("click", () => resetProgress());

    fileInput.addEventListener("change", async (event) => {
      const [file] = event.target.files;
      if (!file) return;
      htmlInput.value = await file.text();
      state.importedFileName = file.name;
      setStatus(`已导入文件：${file.name}`, "success");
      resetProgress();
      pushProgress("已导入 HTML 文件", `${file.name} / ${Math.max(1, Math.round(file.size / 1024))} KB`, "success");
    });

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
      resetProgress();
      if (state.importedFileName) {
        pushProgress("输入源已就绪", `导入文件：${state.importedFileName}`, "success");
      } else {
        pushProgress("输入源已就绪", `已提供 ${payload.raw_html.length} 个字符的网页源码`, "success");
      }
      if (payload.url) {
        pushProgress("URL 已提供", payload.url, "success");
      } else {
        pushProgress("未提供 URL", "当前仅基于网页源码解析。", "loading");
      }
      pushProgress("开始解析", "已提交到服务端，正在判断模板命中与回退策略。", "loading");
      setStatus("解析中...", "idle");
      try {
        const response = await requestJson("/extract", {
          method: "POST",
          headers: { "Content-Type": "application/json; charset=utf-8" },
          body: JSON.stringify(payload)
        });
        resultBox.textContent = JSON.stringify(response, null, 2);
        setStatus(response.status === "success" ? "解析成功" : "解析失败", response.status === "success" ? "success" : "error");
        setDetail("本次解析详情", response.debug_trace || response, "", buildDetailSummary(response.debug_trace || response));
        pushResponseProgress(response);
        await Promise.all([loadTemplates(), loadCandidates()]);
      } catch (error) {
        const payload = { error: String(error) };
        resultBox.textContent = JSON.stringify(payload, null, 2);
        setStatus("解析失败", "error");
        setDetail("解析失败", payload, "服务端返回错误。");
        pushProgress("解析失败", String(error), "error");
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
      const pageSize = Number(templatePageSize.value || 10);
      const view = paginate(filtered, state.templatePage, pageSize);
      if (selectAllTemplates.checked) {
        view.items.forEach((item) => state.selectedTemplateIds.add(item.template_id));
      } else {
        view.items.forEach((item) => state.selectedTemplateIds.delete(item.template_id));
      }
      renderTemplates();
    });

    loadTemplates();
    loadCandidates();
  </script>
</body>
</html>
"""
