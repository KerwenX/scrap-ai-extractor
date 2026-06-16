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
      max-width: 1380px;
      margin: 0 auto;
      padding: 28px 18px 40px;
    }
    .hero, .workspace, .lower-grid {
      display: grid;
      gap: 18px;
    }
    .hero { grid-template-columns: 1.3fr 0.9fr; margin-bottom: 18px; }
    .workspace { grid-template-columns: minmax(340px, 430px) minmax(0, 1fr); align-items: start; }
    .lower-grid { margin-top: 18px; grid-template-columns: minmax(0, 1.15fr) minmax(320px, 0.85fr); }
    .library-stack { display: grid; gap: 18px; }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      backdrop-filter: blur(10px);
    }
    .hero-copy, .hero-meta, .form-panel, .result-panel, .library-panel, .detail-panel { padding: 22px 28px; }
    .hero-copy {
      position: relative;
      overflow: hidden;
    }
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
    .stat, .card, .empty {
      border: 1px solid var(--line);
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.6);
    }
    .stat { padding: 14px 16px; }
    .stat-label, label, .status, .mini-note, .hint, .card-meta { color: var(--muted); }
    .stat-label { display: block; margin-bottom: 6px; font-size: 12px; }
    .stat-value { font-size: 15px; font-weight: 600; }
    .section-title { margin: 0 0 16px; font-size: 18px; font-weight: 700; }
    .field { margin-bottom: 14px; }
    label { display: block; margin-bottom: 8px; font-size: 13px; }
    input[type="text"], textarea {
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
    .actions, .toolbar, .result-toolbar {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
    }
    .result-toolbar { justify-content: space-between; margin-bottom: 12px; }
    .actions { margin-top: 18px; }
    button {
      border: 0;
      border-radius: 999px;
      padding: 10px 16px;
      font: inherit;
      cursor: pointer;
    }
    button:disabled { opacity: 0.65; cursor: default; }
    .primary {
      color: white;
      background: linear-gradient(135deg, var(--accent) 0%, #2d8b78 100%);
      box-shadow: 0 14px 30px rgba(13, 107, 99, 0.24);
    }
    .secondary, .ghost {
      color: var(--text);
      background: rgba(255, 255, 255, 0.8);
      border: 1px solid var(--line);
    }
    .ghost { font-size: 13px; padding: 8px 14px; }
    .danger {
      color: white;
      background: linear-gradient(135deg, #8f2d2d 0%, #bc4b4b 100%);
    }
    .upload { position: relative; overflow: hidden; display: inline-flex; align-items: center; }
    .upload input { position: absolute; inset: 0; opacity: 0; cursor: pointer; }
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
    .detail-panel pre { min-height: 500px; background: #121826; }
    .list-grid { display: grid; gap: 12px; }
    .card { padding: 14px; }
    .card-head {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: flex-start;
      margin-bottom: 10px;
    }
    .card-title { margin: 0; font-size: 15px; font-weight: 700; word-break: break-word; }
    .card-meta { display: grid; gap: 4px; font-size: 13px; margin-bottom: 12px; }
    .empty { padding: 18px; border-style: dashed; font-size: 13px; }
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
        <div class="stat"><span class="stat-label">模板管理</span><span class="stat-value">/templates · /template-candidates</span></div>
        <div class="stat"><span class="stat-label">当前策略</span><span class="stat-value">模板优先，LLM 兜底，支持人工晋升</span></div>
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
          <label class="secondary upload">导入 HTML 文件<input id="fileInput" type="file" accept=".html,.htm,text/html" /></label>
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
            <div class="toolbar"><button class="ghost" id="refreshTemplatesBtn" type="button">刷新模板</button></div>
          </div>
          <div class="mini-note">正式模板参与主路径匹配。停用后不会被命中。</div>
          <div class="list-grid" id="templatesList" style="margin-top: 14px;"></div>
        </div>

        <div class="panel library-panel">
          <div class="result-toolbar">
            <h2 class="section-title" style="margin: 0;">候选模板</h2>
            <div class="toolbar"><button class="ghost" id="refreshCandidatesBtn" type="button">刷新候选</button></div>
          </div>
          <div class="mini-note">候选模板保留首次 LLM 成功抽取后的分析结果与 DSL 草案，可人工晋升为正式模板。</div>
          <div class="list-grid" id="candidatesList" style="margin-top: 14px;"></div>
        </div>
      </div>

      <div class="panel detail-panel">
        <div class="result-toolbar">
          <h2 class="section-title" style="margin: 0;">模板详情</h2>
          <div class="badge" id="detailBadge">未选择</div>
        </div>
        <div class="status" id="detailStatus">点击左侧卡片查看模板或候选模板详情。</div>
        <pre id="detailBox">{
  "message": "模板详情会显示在这里。"
}</pre>
      </div>
    </section>
  </div>

  <script>
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
    const templatesList = document.getElementById("templatesList");
    const candidatesList = document.getElementById("candidatesList");
    const detailBox = document.getElementById("detailBox");
    const detailStatus = document.getElementById("detailStatus");
    const detailBadge = document.getElementById("detailBadge");
    const refreshTemplatesBtn = document.getElementById("refreshTemplatesBtn");
    const refreshCandidatesBtn = document.getElementById("refreshCandidatesBtn");

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

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
    }

    function renderTemplates(templates) {
      if (!templates.length) {
        templatesList.innerHTML = '<div class="empty">当前还没有可用的正式模板。</div>';
        return;
      }
      templatesList.innerHTML = templates.map((item) => {
        const activeLabel = item.active ? "启用中" : "已停用";
        const activeClass = item.active ? "success" : "muted";
        const requiredFields = Array.isArray(item.required_fields) ? item.required_fields.join(", ") : "";
        return `
          <div class="card">
            <div class="card-head">
              <div>
                <h3 class="card-title">${escapeHtml(item.template_id)}</h3>
                <div class="card-meta">
                  <span>${escapeHtml(item.site_id)} · ${escapeHtml(item.scenario)}</span>
                  <span>template_key: ${escapeHtml(item.template_key || "-")}</span>
                  <span>required_fields: ${escapeHtml(requiredFields || "-")}</span>
                </div>
              </div>
              <span class="pill ${activeClass}">${activeLabel}</span>
            </div>
            <div class="toolbar">
              <button class="ghost" type="button" data-template-detail="${escapeHtml(item.template_id)}">查看详情</button>
              <button class="${item.active ? "danger" : "secondary"}" type="button" data-template-toggle="${escapeHtml(item.template_id)}" data-next-state="${item.active ? "deactivate" : "activate"}">${item.active ? "停用" : "启用"}</button>
            </div>
          </div>
        `;
      }).join("");

      templatesList.querySelectorAll("[data-template-detail]").forEach((button) => {
        button.addEventListener("click", () => showTemplateDetail(button.dataset.templateDetail));
      });
      templatesList.querySelectorAll("[data-template-toggle]").forEach((button) => {
        button.addEventListener("click", () => toggleTemplate(button.dataset.templateToggle, button.dataset.nextState));
      });
    }

    function renderCandidates(candidates) {
      if (!candidates.length) {
        candidatesList.innerHTML = '<div class="empty">当前还没有候选模板。执行一次未知页面抽取后会自动产生。</div>';
        return;
      }
      candidatesList.innerHTML = candidates.map((item) => {
        const extractedFields = Array.isArray(item.extracted_fields) ? item.extracted_fields.join(", ") : "";
        return `
          <div class="card">
            <div class="card-head">
              <div>
                <h3 class="card-title">${escapeHtml(item.candidate_id)}</h3>
                <div class="card-meta">
                  <span>${escapeHtml(item.site_id)} · ${escapeHtml(item.scenario)}</span>
                  <span>source_url: ${escapeHtml(item.source_url || "-")}</span>
                  <span>fields: ${escapeHtml(extractedFields || "-")}</span>
                </div>
              </div>
              <span class="pill warning">候选</span>
            </div>
            <div class="toolbar">
              <button class="ghost" type="button" data-candidate-detail="${escapeHtml(item.candidate_id)}">查看详情</button>
              <button class="secondary" type="button" data-candidate-promote="${escapeHtml(item.candidate_id)}">晋升模板</button>
            </div>
          </div>
        `;
      }).join("");

      candidatesList.querySelectorAll("[data-candidate-detail]").forEach((button) => {
        button.addEventListener("click", () => showCandidateDetail(button.dataset.candidateDetail));
      });
      candidatesList.querySelectorAll("[data-candidate-promote]").forEach((button) => {
        button.addEventListener("click", () => promoteCandidate(button.dataset.candidatePromote));
      });
    }

    async function loadTemplates() {
      templatesList.innerHTML = '<div class="empty">正在加载正式模板...</div>';
      try {
        const payload = await requestJson("/templates");
        renderTemplates(payload.templates || []);
      } catch (error) {
        templatesList.innerHTML = `<div class="empty">模板加载失败: ${escapeHtml(String(error))}</div>`;
      }
    }

    async function loadCandidates() {
      candidatesList.innerHTML = '<div class="empty">正在加载候选模板...</div>';
      try {
        const payload = await requestJson("/template-candidates");
        renderCandidates(payload.candidates || []);
      } catch (error) {
        candidatesList.innerHTML = `<div class="empty">候选模板加载失败: ${escapeHtml(String(error))}</div>`;
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

    async function toggleTemplate(templateId, nextState) {
      try {
        const payload = await requestJson(`/templates/${encodeURIComponent(templateId)}/${nextState}`, {
          method: "POST",
          headers: { "Content-Type": "application/json; charset=utf-8" },
          body: "{}"
        });
        setDetail(`模板 ${templateId}`, payload, `模板已${nextState === "activate" ? "启用" : "停用"}。`);
        await loadTemplates();
      } catch (error) {
        setDetail("模板状态更新失败", { error: String(error) }, "无法更新模板状态。");
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

    refreshTemplatesBtn.addEventListener("click", loadTemplates);
    refreshCandidatesBtn.addEventListener("click", loadCandidates);
    loadTemplates();
    loadCandidates();
  </script>
</body>
</html>
"""
