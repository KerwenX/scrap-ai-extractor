# 混合网页解析器

这是一个只专注于“网页解析”的项目，不负责爬虫抓取。

输入：
- `url`
- `raw_html`
- `user_prompt`

输出：
- 结构化抽取结果
- 命中的正式模板信息
- 校验结果
- 调试链路信息

项目目标是把“首次依赖 LLM 的抽取”逐步沉淀成“可复用、可迁移、可版本化”的正式模板 `JSON + DSL`。

## 核心能力

- 首次遇到的新页面：优先走 LLM 抽取。
- LLM 抽取成功后：自动生成候选模板，并在条件满足时固化为正式模板。
- 已存在正式模板的页面：优先走确定性模板解析。
- 模板失效、字段缺失、校验失败时：自动回退到 LLM。
- 批量解析：只走正式模板，不调用 LLM，并把结果写入 JSONL。

## 项目结构

```text
config/
  app_config.template.json
  templates/
data/
  template_store/
  template_candidates/
  batch_results/
docs/
  architecture.md
  template-design.md
  java-runtime.md
scripts/
  run_ui.ps1
  stop_ui.ps1
  benchmark_template_reuse.py
src/hybrid_extractor/
  controllers/
  services/
  templates/
  extractors/
  engine.py
  rule_runtime.py
  template_registry.py
  web_ui.py
tests/
local_medical_html_extraction.py
```

## 安装

```powershell
cd G:\code\Extractor\scrap-ai-extractor
pip install -e .
```

如果需要运行测试：

```powershell
pip install -e .[dev]
```

## 配置

先复制配置模板：

```powershell
Copy-Item .\config\app_config.template.json .\config\app_config.json
```

然后编辑 `config/app_config.json`：

```json
{
  "llm": {
    "provider": "deepseek",
    "api_key": "YOUR_DEEPSEEK_API_KEY",
    "base_url": "https://api.deepseek.com",
    "model": "deepseek-v4-pro",
    "reasoning_effort": "high",
    "thinking_enabled": true,
    "max_tokens": 128000
  }
}
```

说明：
- `config/app_config.json` 已加入 `.gitignore`
- 如果设置了环境变量 `DEEPSEEK_API_KEY`，会覆盖配置文件中的 `api_key`

## 使用方式

### 1. 单条自动解析

```powershell
python .\local_medical_html_extraction.py `
  --html-path "E:\Documents\Downloads\页面.html" `
  --url "https://example.com/page" `
  --prompt "提取页面中的结构化信息"
```

说明：
- 这是默认模式。
- 会先尝试命中正式模板。
- 未命中或模板失效时，允许回退到 LLM。

### 2. 单条仅模板解析

```powershell
python .\local_medical_html_extraction.py `
  --html-path "E:\Documents\Downloads\页面.html" `
  --url "https://example.com/page" `
  --prompt "提取页面中的结构化信息" `
  --template-only
```

说明：
- 该模式要求必须提供 `--url`
- 若没有命中正式模板，会直接返回失败
- 不会调用 LLM

### 3. 批量模板解析

先准备一个 `jsonl` 文件，每行一条记录，例如：

```json
{"url":"https://example.com/paper/1","html_path":"E:\\pages\\paper1.html"}
{"url":"https://example.com/paper/2","html_path":"E:\\pages\\paper2.html"}
```

兼容已有字段：
- `html_path`
- `file_path`

执行命令：

```powershell
python .\local_medical_html_extraction.py `
  --batch-jsonl "G:\code\AI coding\20260619-test\url_to_file_mapping.jsonl" `
  --prompt "提取论文页面中的结构化信息" `
  --output-jsonl ".\data\batch_results\paper-results.jsonl"
```

说明：
- 批量模式只走正式模板
- 每条记录都必须包含 `url`
- 输出结果 JSONL 中一定会保留 `url`

### 4. 启动本地 Web UI

```powershell
.\scripts\run_ui.ps1
```

默认地址：
- UI: `http://127.0.0.1:8000/`
- Health: `http://127.0.0.1:8000/health`

常用脚本：

```powershell
.\scripts\run_ui.ps1
.\scripts\run_ui.ps1 -Status
.\scripts\run_ui.ps1 -Stop
.\scripts\stop_ui.ps1
```

如果你修改了界面代码但浏览器里还是旧页面，通常是旧的 `8000` 端口进程还在运行。先执行：

```powershell
.\scripts\run_ui.ps1 -Stop
.\scripts\run_ui.ps1
```

## 如何判断本次走的是模板还是 LLM

看返回结果里的：

- `extractor_type`
  - `deterministic`：走正式模板
  - `hybrid`：模板尝试后回退到 LLM
  - `llm`：直接走 LLM
  - `none`：模板专用模式下未命中模板

还可以看：
- `template_id`
- `debug_trace.template_match`
- `debug_trace.drift_report`
- `debug_trace.run_mode`

## API

核心接口：
- `POST /extract`
- `POST /extract/batch`
- `GET /health`

模板管理接口：
- `GET /templates`
- `GET /templates/{template_id}`
- `POST /templates/{template_id}/activate`
- `POST /templates/{template_id}/deactivate`
- `POST /templates/{template_id}/status`
- `DELETE /templates/{template_id}`
- `POST /templates/delete-batch`
- `GET /template-candidates`
- `GET /template-candidates/{candidate_id}`
- `POST /template-candidates/{candidate_id}/promote`
- `DELETE /template-candidates/{candidate_id}`

### `/extract` 请求示例

```json
{
  "url": "https://example.com/page",
  "raw_html": "<html>...</html>",
  "user_prompt": "提取页面中的结构化信息"
}
```

### `/extract/batch` 请求示例

```json
{
  "jsonl_content": "{\"url\":\"https://example.com/1\",\"html_path\":\"E:\\\\pages\\\\1.html\"}",
  "user_prompt": "提取结构化信息",
  "output_jsonl_path": "G:\\code\\Extractor\\scrap-ai-extractor\\data\\batch_results\\result.jsonl"
}
```

也支持传入：
- `jsonl_path`

## 测试

```powershell
pytest -q
python -m compileall src tests
```

当前本地验证结果：
- `pytest -q`：`41 passed`

## 文档

- [模板设计说明](./docs/template-design.md)
- [架构设计](./docs/architecture.md)
- [Java 运行时说明](./docs/java-runtime.md)
