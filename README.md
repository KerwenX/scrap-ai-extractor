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

项目目标是把“首次依赖 LLM 的抽取”逐步沉淀成“可复用、可迁移、可版本化”的正式模板 JSON + DSL。

## 核心能力

- 首次遇到的新页面：优先走 LLM 抽取。
- LLM 抽取成功后：自动生成候选模板，并在条件满足时自动固化为正式模板。
- 已存在正式模板的页面：优先走确定性模板解析。
- 模板失效、字段缺失、校验失败时：自动回退到 LLM。
- 模板是文件资产，可直接迁移到别的机器，不依赖数据库状态。

## 当前模板策略

当前模板系统已经收敛到“模板家族复用”：

- 首次 LLM 成功后，固化的是模板家族，不是单个页面样本。
- 同站点页面会先进入候选模板集合，再综合判断命中哪个模板。
- 正式 DSL 模板的命中不再只依赖指纹，而是依赖“运行时字段命中率 + 必填字段覆盖率 + 指纹 + 分类亲和度”综合评分。

当前匹配大致分四层：

1. 先按 `site_id` 过滤，只在同站点内选模板。
2. 再看 `scenario/page_type` 亲和度，作为先验加分，不再是唯一硬门槛。
3. 对同站点 DSL 模板逐个试跑，统计：
   - `selector_hit_rate`
   - `required_hit_rate`
4. 再结合 `fingerprint_score` 做综合评分，最终选择得分最高的模板。

其中：

- 当 `selector_hit_rate >= 0.85` 且 `required_hit_rate >= 0.85` 时，会被视为强匹配。
- 如果多个模板都能命中，则选择综合得分最高的那个。

这比“只看指纹”更稳，尤其适合同站点下有多个相近页面模板的场景。

## 通用定位器

除了原有的 `css / id / meta / text_pattern / section_tab` 之外，当前 DSL 新增了：

- `label_value`

它用于处理这类常见结构：

```html
<tr><td>作者</td><td>张三</td></tr>
<tr><td>期刊</td><td>经济研究</td></tr>
```

也就是“标签在左、值在右”的结构。

这类页面在论文、医生、商品、资讯详情页里都很常见。加入这个定位器后，模板固化时不再强依赖值节点必须有唯一 `id/class`，模板可复用性会明显更强。

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

### 3. 本地模板复用基准

如果你本地有 `G:\code\AI coding\20260619-test\url_to_file_mapping.jsonl`，可以直接运行：

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

这个脚本会：

- 读取本地 `url -> html` 映射
- 自动挑选同站点论文页样本
- 从首个样本页构建一个基准模板
- 跑整批页面，统计模板复用命中率和覆盖率

## 如何判断这次是走模板还是走 LLM

看返回结果里的：

- `extractor_type`
  - `deterministic`：走正式模板
  - `hybrid`：模板尝试后回退了 LLM
  - `llm`：直接走 LLM

还可以看：

- `template_id`
- `debug_trace.template_match`
- `debug_trace.drift_report`

其中 `debug_trace.template_match` 现在会带上：

- `match_score`
- `fingerprint_score`
- `selector_hit_rate`
- `required_hit_rate`
- `classification_affinity`

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

## 测试

```powershell
pytest -q
python -m compileall src tests
```

## 文档

- [模板设计说明](G:\code\Extractor\scrap-ai-extractor\docs\template-design.md)
- [架构设计](G:\code\Extractor\scrap-ai-extractor\docs\architecture.md)
- [Java 运行时说明](G:\code\Extractor\scrap-ai-extractor\docs\java-runtime.md)
