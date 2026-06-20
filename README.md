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

项目目标是把“首次依赖 LLM 的抽取”逐步沉淀为“可复用、可迁移、可版本化”的正式模板 JSON + DSL。

## 核心能力

- 首次遇到的新页面：优先走 LLM 抽取。
- LLM 抽取成功后：自动生成候选模板，并在条件满足时自动固化为正式模板。
- 已存在正式模板的页面：优先走确定性模板解析。
- 模板失效、字段缺失、校验失败时：自动回退到 LLM。
- 当既有模板命中但覆盖不足，而本次 LLM 候选更完整时：自动升级既有模板，而不是裂变出一套新的模板族。
- 模板以文件形式落盘，可直接迁移到别的机器，不依赖数据库状态。

## 当前模板闭环

当前模板系统已经收敛到三种动作：

- `create`：不存在同指纹正式模板，直接创建新模板。
- `upgrade`：存在同指纹正式模板，但当前候选规则覆盖更完整，自动生成新版本并停用旧版本。
- `reuse`：既有模板已经覆盖当前候选，不再重复晋升。

这解决了之前“抽取时走了 LLM，但候选又因为已有正式模板而无法晋升”的逻辑断裂问题。

## 命中策略

正式 DSL 模板的命中不再只依赖指纹，而是综合以下信号评分：

- `fingerprint_score`
- `selector_hit_rate`
- `required_hit_rate`
- `classification_affinity`

策略顺序：

1. 先按 `site_id` 过滤。
2. 再看 `scenario / page_type` 亲和度。
3. 对 DSL 模板逐个试跑，统计运行时字段命中情况。
4. 最后结合指纹相似度得出综合得分，选择得分最高的模板。

这比“只看 DOM 指纹”更适合同站点下多页面类型并存的场景。

## 项目结构

```text
config/
  app_config.template.json
  templates/
data/
  template_store/
  template_candidates/
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

### 1. 直接解析本地 HTML

```powershell
python .\local_medical_html_extraction.py `
  --html-path "E:\Documents\Downloads\页面.html" `
  --url "https://example.com/page" `
  --prompt "提取页面中的结构化信息"
```

### 2. 启动本地 Web UI

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

如果你修改了界面代码，但浏览器仍然显示旧页面，通常是旧的 `8000` 端口进程还在运行。先执行：

```powershell
.\scripts\run_ui.ps1 -Stop
.\scripts\run_ui.ps1
```

### 3. 模板复用基准测试

如果本地有 `G:\code\AI coding\20260619-test\url_to_file_mapping.jsonl`，可以直接运行：

```powershell
python .\scripts\benchmark_template_reuse.py
```

也可以自定义：

```powershell
python .\scripts\benchmark_template_reuse.py `
  --mapping-path "G:\code\AI coding\20260619-test\url_to_file_mapping.jsonl" `
  --site "erj.ajcass.com" `
  --limit 20
```

## 如何判断本次走的是模板还是 LLM

看返回结果里的：

- `extractor_type`
  - `deterministic`：走正式模板
  - `hybrid`：模板尝试后回退到 LLM
  - `llm`：直接走 LLM

还可以看：

- `template_id`
- `debug_trace.template_match`
- `debug_trace.drift_report`

## API

核心接口：

- `POST /extract`
- `GET /health`

模板管理接口：

- `GET /templates`
- `GET /templates/{template_id}`
- `POST /templates/{template_id}/activate`
- `POST /templates/{template_id}/deactivate`
- `POST /templates/{template_id}/status`
- `GET /template-candidates`
- `GET /template-candidates/{candidate_id}`
- `POST /template-candidates/{candidate_id}/promote`
- `DELETE /template-candidates/{candidate_id}`
- `POST /templates/delete-batch`

## 测试

```powershell
pytest -q
python -m compileall src tests
```

当前本地验证结果：

- `pytest -q`：`39 passed`
- 医生详情页真实样本：已命中正式模板，`extractor_type=deterministic`，字段覆盖率 `1.0`

## 文档

- [模板设计说明](./docs/template-design.md)
- [架构设计](./docs/architecture.md)
- [Java 运行时说明](./docs/java-runtime.md)
