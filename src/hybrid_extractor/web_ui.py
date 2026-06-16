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
      --bg: linear-gradient(135deg, #f5efe5 0%, #e9f2f1 55%, #dce6f4 100%);
      --panel: rgba(255, 255, 255, 0.82);
      --text: #17202a;
      --muted: #5b6570;
      --line: rgba(23, 32, 42, 0.12);
      --accent: #0c6d62;
      --accent-strong: #084d45;
      --shadow: 0 24px 60px rgba(25, 35, 45, 0.14);
      --radius: 22px;
      --mono: "Cascadia Code", "SFMono-Regular", Consolas, monospace;
      --sans: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: var(--sans);
      color: var(--text);
      background: var(--bg);
      min-height: 100vh;
    }
    .shell {
      max-width: 1240px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }
    .hero {
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 18px;
      margin-bottom: 18px;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      backdrop-filter: blur(10px);
    }
    .hero-copy {
      padding: 28px;
      position: relative;
      overflow: hidden;
    }
    .hero-copy::after {
      content: "";
      position: absolute;
      inset: auto -40px -40px auto;
      width: 180px;
      height: 180px;
      background: radial-gradient(circle, rgba(12,109,98,0.24), rgba(12,109,98,0));
    }
    h1 {
      margin: 0 0 12px;
      font-size: clamp(28px, 4vw, 46px);
      line-height: 1.04;
      letter-spacing: -0.03em;
    }
    .subtitle {
      margin: 0;
      color: var(--muted);
      font-size: 15px;
      line-height: 1.7;
      max-width: 56ch;
    }
    .hero-meta {
      padding: 24px;
      display: grid;
      gap: 14px;
      align-content: center;
    }
    .stat {
      padding: 14px 16px;
      border: 1px solid var(--line);
      border-radius: 16px;
      background: rgba(255,255,255,0.55);
    }
    .stat-label {
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 6px;
    }
    .stat-value {
      font-size: 15px;
      font-weight: 600;
    }
    .grid {
      display: grid;
      grid-template-columns: minmax(320px, 440px) minmax(0, 1fr);
      gap: 18px;
      align-items: start;
    }
    .form-panel, .result-panel {
      padding: 22px;
    }
    .section-title {
      margin: 0 0 16px;
      font-size: 18px;
      font-weight: 700;
    }
    .field {
      margin-bottom: 14px;
    }
    label {
      display: block;
      margin-bottom: 8px;
      font-size: 13px;
      color: var(--muted);
    }
    input[type="text"], textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 12px 14px;
      font: inherit;
      background: rgba(255,255,255,0.8);
      color: var(--text);
      transition: border-color 140ms ease, box-shadow 140ms ease, transform 140ms ease;
    }
    input[type="text"]:focus, textarea:focus {
      outline: none;
      border-color: rgba(12,109,98,0.5);
      box-shadow: 0 0 0 4px rgba(12,109,98,0.12);
      transform: translateY(-1px);
    }
    textarea {
      min-height: 130px;
      resize: vertical;
    }
    .html-box {
      min-height: 240px;
      font-family: var(--mono);
      font-size: 12px;
      line-height: 1.55;
    }
    .actions {
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
      margin-top: 18px;
    }
    button {
      border: 0;
      border-radius: 999px;
      padding: 12px 18px;
      font: inherit;
      cursor: pointer;
      transition: transform 140ms ease, opacity 140ms ease, box-shadow 140ms ease;
    }
    button:hover { transform: translateY(-1px); }
    .primary {
      background: linear-gradient(135deg, var(--accent) 0%, #2f907b 100%);
      color: white;
      box-shadow: 0 12px 28px rgba(12,109,98,0.28);
    }
    .secondary {
      background: rgba(255,255,255,0.8);
      color: var(--text);
      border: 1px solid var(--line);
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
    .status {
      min-height: 20px;
      color: var(--muted);
      font-size: 13px;
    }
    .result-toolbar {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: center;
      margin-bottom: 12px;
      flex-wrap: wrap;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(12,109,98,0.1);
      color: var(--accent-strong);
      font-size: 12px;
      font-weight: 600;
    }
    pre {
      margin: 0;
      padding: 18px;
      border-radius: 18px;
      background: #101822;
      color: #dcf8f2;
      overflow: auto;
      min-height: 520px;
      font-family: var(--mono);
      font-size: 12px;
      line-height: 1.6;
      border: 1px solid rgba(255,255,255,0.05);
    }
    .hint {
      margin-top: 12px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.6;
    }
    @media (max-width: 920px) {
      .hero, .grid { grid-template-columns: 1fr; }
      pre { min-height: 360px; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div class="panel hero-copy">
        <h1>混合网页解析器</h1>
        <p class="subtitle">
          输入 URL、Prompt 和网页源码，系统会优先尝试正式模板，再在必要时回退到 LLM，
          并将可复用的解析方法固化成正式模板。
        </p>
      </div>
      <div class="panel hero-meta">
        <div class="stat">
          <span class="stat-label">接口地址</span>
          <span class="stat-value">POST /extract</span>
        </div>
        <div class="stat">
          <span class="stat-label">模板查看</span>
          <span class="stat-value">GET /templates</span>
        </div>
        <div class="stat">
          <span class="stat-label">当前目标</span>
          <span class="stat-value">通用解析、模板复用、自动固化</span>
        </div>
      </div>
    </section>

    <section class="grid">
      <div class="panel form-panel">
        <h2 class="section-title">解析输入</h2>
        <div class="field">
          <label for="url">原始 URL</label>
          <input id="url" type="text" placeholder="https://example.com/article/123" />
        </div>
        <div class="field">
          <label for="prompt">抽取需求</label>
          <textarea id="prompt">提取页面中与用户需求最相关的结构化信息，并尽量输出中文。</textarea>
        </div>
        <div class="field">
          <label for="html">网页源码</label>
          <textarea id="html" class="html-box" placeholder="可直接粘贴 HTML，或使用下方按钮导入本地 HTML 文件。"></textarea>
        </div>
        <div class="actions">
          <button class="primary" id="extractBtn">开始解析</button>
          <label class="secondary upload">
            导入 HTML 文件
            <input id="fileInput" type="file" accept=".html,.htm,text/html" />
          </label>
          <button class="secondary" id="sampleBtn" type="button">填充示例</button>
          <button class="secondary" id="clearBtn" type="button">清空</button>
        </div>
        <div class="hint">
          本页面不会自动抓取远程 URL，仍然需要你提供网页源码。导入本地 HTML 文件时，会在浏览器里读取文件内容并发给后端。
        </div>
      </div>

      <div class="panel result-panel">
        <div class="result-toolbar">
          <h2 class="section-title" style="margin: 0;">解析结果</h2>
          <div class="badge" id="statusBadge">等待执行</div>
        </div>
        <div class="status" id="statusLine"></div>
        <pre id="resultBox">{\n  "message": "执行后会在这里显示 JSON 结果。"\n}</pre>
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

    function setStatus(text, tone) {
      statusLine.textContent = text;
      statusBadge.textContent = tone === "loading" ? "执行中" : tone === "error" ? "失败" : tone === "success" ? "成功" : "等待执行";
      statusBadge.style.background = tone === "error"
        ? "rgba(166, 42, 42, 0.12)"
        : tone === "success"
          ? "rgba(12,109,98,0.12)"
          : "rgba(12,109,98,0.1)";
      statusBadge.style.color = tone === "error" ? "#8b1f1f" : "#084d45";
    }

    sampleBtn.addEventListener("click", () => {
      urlInput.value = "https://example.com/article/123";
      promptInput.value = "提取页面中与用户需求最相关的结构化信息，并尽量输出中文。";
      htmlInput.value = "<html><head><title>示例页面</title><meta name=\\"description\\" content=\\"这是一个示例摘要\\"></head><body><h1>示例标题</h1><article><p>这里是正文。</p></article></body></html>";
    });

    clearBtn.addEventListener("click", () => {
      urlInput.value = "";
      htmlInput.value = "";
      resultBox.textContent = "{\\n  \\"message\\": \\"执行后会在这里显示 JSON 结果。\\"\\n}";
      setStatus("", "idle");
    });

    fileInput.addEventListener("change", async (event) => {
      const [file] = event.target.files;
      if (!file) return;
      htmlInput.value = await file.text();
      setStatus(`已导入文件：${file.name}`, "success");
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
          setStatus(`请求失败：HTTP ${response.status}`, "error");
          return;
        }
        setStatus("解析完成。", data.status === "failed" ? "error" : "success");
      } catch (error) {
        resultBox.textContent = JSON.stringify({ error: String(error) }, null, 2);
        setStatus("请求异常，请检查服务端日志。", "error");
      } finally {
        extractBtn.disabled = false;
      }
    });
  </script>
</body>
</html>
"""
