# 混合网页解析器

这是一个只专注于网页解析的项目，不负责爬虫抓取。

系统输入：

- `url`
- `raw_html`
- `user_prompt`

系统输出：

- 结构化抽取结果
- 命中的正式模板信息
- 校验结果
- 调试链路信息

核心目标：

- 首次遇到的网页模板，优先走 LLM 理解、字段识别和抽取。
- 已识别并固化的网页模板，优先走正式模板 JSON + DSL 的确定性解析。
- 当模板失效、字段缺失或校验失败时，自动回退到 LLM，并沉淀新的候选模板。

## 当前特性

- 不依赖爬虫，只处理你已经拿到的网页源码。
- 支持用户通过自然语言定义抽取目标。
- 正式模板优先，LLM 兜底。
- 首次 LLM 成功抽取后，自动生成候选模板。
- 候选模板保留两阶段中间结果：
  - `analysis`
  - `proposed_plan`
- 成功固化后，下一次相同模板页面可以直接命中正式模板。
- 提供本地 Web UI，可直接测试抽取、查看模板、查看候选模板、启停模板。

## 项目结构

```text
config/
  app_config.template.json     配置模板
  templates/                   内置正式模板
docs/
  requirements.md              中文需求文档
  architecture.md              中文架构设计
src/hybrid_extractor/
  controllers/                 接口编排
  services/                    服务层
  extractors/                  LLM 回退抽取器
  templates/                   模板适配器
  engine.py                    解析主流程
  rule_runtime.py              DSL 运行时
  web_ui.py                    本地 Web UI
tests/                         自动化测试
local_medical_html_extraction.py
```

## 安装

```powershell
cd G:\code\Extractor\scrap-ai-extractor
pip install -e .
```

如果还要运行测试：

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
    "api_key": "你的真实 DeepSeek API Key",
    "base_url": "https://api.deepseek.com",
    "model": "deepseek-v4-pro",
    "reasoning_effort": "high",
    "thinking_enabled": true,
    "max_tokens": 128000
  }
}
```

说明：

- `config/app_config.json` 已加入 `.gitignore`。
- 如果设置了 `DEEPSEEK_API_KEY` 环境变量，它会覆盖配置文件中的 `api_key`。

## 使用方式

### 1. 直接解析本地 HTML

```powershell
python .\local_medical_html_extraction.py `
  --html-path "E:\Documents\Downloads\页面.html" `
  --url "https://example.com/page" `
  --prompt "提取页面中与用户需求最相关的结构化信息"
```

保存结果：

```powershell
python .\local_medical_html_extraction.py `
  --html-path "E:\Documents\Downloads\页面.html" `
  --output-file ".\result.json"
```

### 2. 使用安装后的 CLI

```powershell
hybrid-web-extractor `
  --html-path "E:\Documents\Downloads\页面.html" `
  --url "https://example.com/page" `
  --prompt "提取页面中的标题、摘要、作者、发布时间和正文要点"
```

### 3. 启动本地 API 服务

```powershell
@'
from hybrid_extractor.api_server import run_server
run_server()
'@ | python -
```

默认地址：

- `http://127.0.0.1:8000`

本地 Web UI：

- `http://127.0.0.1:8000/`

## API

核心接口：

- `POST /extract`
- `GET /health`

模板管理接口：

- `GET /templates`
- `GET /templates/{template_id}`
- `POST /templates/{template_id}/activate`
- `POST /templates/{template_id}/deactivate`
- `GET /template-candidates`
- `GET /template-candidates/{candidate_id}`

### `POST /extract` 示例

```powershell
$body = @{
  url = "https://example.com/page"
  raw_html = [System.IO.File]::ReadAllText("E:\Documents\Downloads\页面.html")
  user_prompt = "提取页面中的标题、摘要、作者、发布时间和正文要点"
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/extract" `
  -Method Post `
  -ContentType "application/json; charset=utf-8" `
  -Body $body
```

## 输出结果说明

关键字段：

- `data`：结构化结果
- `template_id`：命中的模板 ID
- `extractor_type`：`deterministic`、`llm` 或 `hybrid`
- `validation_report`：字段覆盖率和校验结果
- `debug_trace`：分类结果、指纹、模板匹配和调试信息

如果是未知模板且 LLM 回退成功，会产出候选模板文件：

- `data/template_candidates/`

如果候选模板满足固化条件，会自动生成正式模板：

- `data/template_store/`

## 当前实现策略

提示词分层：

- 用户提示词只关注业务目标。
- 系统内部提示词只负责输出约束、字段稳定性和模板固化约束。

模板固化两阶段：

1. 先做模板分析
2. 再生成 DSL 计划

主路径策略：

- 正式模板 manifest 命中
- `GenericRuleTemplateParser` 执行 DSL
- 校验失败时回退到 LLM

legacy 手写站点 parser 不再参与默认匹配主路径。

## 测试

```powershell
pytest -q
```

## 文档

- [需求文档](G:\code\Extractor\scrap-ai-extractor\docs\requirements.md)
- [架构设计](G:\code\Extractor\scrap-ai-extractor\docs\architecture.md)
