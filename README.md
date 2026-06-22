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

## 当前核心策略

### 1. 不再从 HTML 推断 URL

当前系统**不会**再从 HTML 内容里扫描 `http://...` 或 `https://...` 来推断站点。

原因很简单：

- HTML 里的 URL 很多是脚本、SVG、静态资源、第三方链接
- 它们不能代表当前页面真实来源
- 用这些噪声 URL 反推站点，会导致模板匹配被严重干扰

现在的规则是：

- 如果传了 `url`，站点识别只看这个 `url`
- 如果没传 `url`，站点记为 `unknown`

### 2. 无 URL 时不再直接失败

如果没有传 `url`：

- 系统不会再尝试从 HTML 猜站点
- 也不会直接放弃模板匹配
- 而是对正式模板库做运行时 DSL 评分匹配

也就是说：

- 有 URL：先按站点和 URL pattern 缩小范围，再评分
- 无 URL：直接对正式模板做评分匹配

### 3. 只有真正命中过旧模板，才允许升级旧模板

当前模板闭环已经收紧：

- 如果本次请求先命中了旧模板，但抽取校验失败，随后 LLM fallback 成功
  - 这时允许把候选模板升级到该旧模板家族
- 如果本次请求**根本没有命中任何旧模板**
  - 那么 LLM fallback 成功后，只能创建新模板
  - 不允许再去覆盖现有模板家族

这避免了过去那种反直觉情况：

- 运行时没命中旧模板
- 结果却拿新页面去覆盖旧模板版本

### 4. 模板最终是否命中，取决于“运行结果”

模板不是靠 URL 或指纹直接拍板的，而是：

1. 先做候选召回
2. 再把候选模板真正跑到当前 HTML 上
3. 按抽取效果评分
4. 选择得分最高且通过门槛的模板

主要评分因子：

- `required_hit_rate`
- `selector_hit_rate`
- `fingerprint_score`
- `classification_affinity`
- `site_affinity`
- `url_pattern_affinity`

所以 URL 的作用只是“帮助检索模板”，不是最终决定用哪个模板。

### 5. 模板匹配已改为“两阶段”

当前不会再对召回到的所有模板都执行完整 DSL 抽取。

匹配流程现在是：

1. 先按 `site / url_pattern_hash / scenario / fingerprint` 做索引召回
2. 先计算便宜分数
3. 只对 Top-K 候选执行真正的模板抽取评分
4. 高置信命中时提前结束，不再继续扫描剩余模板

这使大规模模板仓下的匹配复杂度明显下降。

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
  java/
scripts/
  run_ui.ps1
  stop_ui.ps1
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

## 模板资产同步约定

- `data/template_store/`：当前本地正式模板仓，会随项目代码一起提交到 GitHub
- `data/template_candidates/`：运行期候选模板，不默认作为稳定交付资产
- `config/templates/`：仓库内置模板样例，可通过配置决定是否参与运行时加载

当前约定是：

- 正式模板以 `data/template_store/` 为主
- 正式模板按站点分目录存储，例如 `data/template_store/m_dayi_org_cn/...`
- 以后同步 GitHub 时，本地正式模板会一并同步
- 废弃版本如果仍保留在本地模板仓中，也会作为历史模板一并保留，方便回溯

## 安装

```powershell
cd G:\code\Extractor\scrap-ai-extractor
pip install -e .
```

如果需要运行测试：

```powershell
pip install -e .[dev]
```

## 依赖说明

当前项目的 LLM fallback 仍然依赖 `scrapegraphai`：

- Python 依赖声明见 [pyproject.toml](G:\code\Extractor\scrap-ai-extractor\pyproject.toml)
- 运行时代码入口见 [src/hybrid_extractor/extractors/llm.py](G:\code\Extractor\scrap-ai-extractor\src\hybrid_extractor\extractors\llm.py)

当前本机环境里，`scrapegraphai` 实际是从本地目录 [Scrapegraph-ai](G:\code\Extractor\scrap-ai-extractor\Scrapegraph-ai) 加载的，而不是完全独立于仓库目录运行。

这意味着：

- 现在**不能直接删除** `Scrapegraph-ai/`
- 如果后续要删除它，必须先把 LLM fallback 改成只依赖已安装包，或者完成对该能力的替换

参考关系说明：

- 本项目专注“网页解析与模板化抽取”
- `Scrapegraph-ai` 目前只作为 LLM 抽取底座依赖被引用

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

- 这是默认模式
- 会先尝试命中正式模板
- 未命中或模板校验失败时，允许回退到 LLM

### 2. 单条仅模板解析

```powershell
python .\local_medical_html_extraction.py `
  --html-path "E:\Documents\Downloads\页面.html" `
  --prompt "提取页面中的结构化信息" `
  --template-only
```

说明：

- 该模式**可以不传 URL**
- 如果传了 URL，会优先按 URL pattern 缩小模板检索范围
- 如果没传 URL，会直接对正式模板库做评分匹配
- 该模式不会调用 LLM

### 3. 批量模板解析

先准备一个 `jsonl` 文件，每行一条记录，例如：

```json
{"url":"https://example.com/paper/1","html_path":"E:\\pages\\paper1.html"}
{"url":"https://example.com/paper/2","html_path":"E:\\pages\\paper2.html"}
```

兼容字段：

- `html_path`
- `file_path`

执行：

```powershell
python .\local_medical_html_extraction.py `
  --batch-jsonl "G:\code\AI coding\20260619-test\url_to_file_mapping.jsonl" `
  --prompt "提取论文页面中的结构化信息" `
  --output-jsonl ".\data\batch_results\paper-results.jsonl"
```

说明：

- 批量模式只走正式模板
- 每条记录建议提供 `url`
- 输出结果 JSONL 中会保留 `url`
- 批量返回体不再携带全部 `results`，只返回统计信息和少量成功/失败样本
- 可以通过 `max_workers` 启用多进程模板解析

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

## 如何判断本次走的是模板还是 LLM

看返回结果中的：

- `extractor_type`
  - `deterministic`：走正式模板
  - `hybrid`：先命中模板，但校验失败后回退到 LLM
  - `llm`：未命中模板，直接走 LLM
  - `none`：`template_only` 模式下未命中任何模板

还可以看：

- `template_id`
- `debug_trace.template_match`
- `debug_trace.drift_report`
- `debug_trace.run_mode`

## AJCASS 论文页现状

当前 `erj.ajcass.com` 的论文详情页，已经沉淀为正式模板：

- `ajcass_com_detail_page_detail_page_c5d7b04b_v3`

这个模板当前可稳定抽取：

- `标题`
- `作者`
- `摘要`
- `关键词`
- `发表时间`
- `稿件来源`
- `期刊`

并且已经验证可以复用到以下同站点论文页：

- `中国专利的经济价值：测度、特征及有效性.html`
- `外资开放式创新有助于“稳外资”目标的实现吗？——基于内外资价值链生产关联视角.html`
- `新分类模式下的转移支付财力均等化效应再评估.html`

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

## 测试

```powershell
pytest -q
python -m compileall src tests
```

当前本地验证结果：

- `pytest -q`：通过
- `python -m compileall src tests`：通过
- Java 运行时 `mvn -q test`：通过

## 文档

- [模板设计说明](./docs/template-design.md)
- [架构设计](./docs/architecture.md)
- [Java 运行时说明](./docs/java-runtime.md)
  - 包含跨机器抽取失败时的 Java 诊断类说明
