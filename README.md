# 混合网页解析器

这是一个只专注于“网页解析”的项目，不负责爬虫抓取。

它的输入是：

- `url`
- `raw_html`
- `user_prompt`

它的输出是：

- 结构化抽取结果
- 命中的模板信息
- 校验结果
- 调试链路信息

项目的核心目标是支持两类解析路径：

- 首次遇到的页面模板，优先走 LLM 理解和抽取
- 已经识别并固化过的页面模板，优先走确定性解析规则

当确定性解析失败、字段缺失、校验不通过或模板发生漂移时，系统会自动回退到 LLM 抽取。

## 适用场景

- 你已经拿到了网页源码，希望做结构化解析
- 同一个站点下有很多不同页面类型，希望后续逐步固化模板
- 希望把解析服务迁移到别的机器继续使用

当前内置了两个中国医药信息查询平台页面模板：

- `dayi / disease_detail`
- `dayi / qa_detail`

## 项目结构

```text
config/
  app_config.template.json     配置模板
  templates/                   已固化模板元数据
docs/
  requirements.md              中文需求文档
  architecture.md              中文架构设计
src/hybrid_extractor/
  controllers/                 接口编排层
  services/                    服务层
  templates/                   内置模板解析器
  extractors/                  LLM 回退抽取器
  engine.py                    解析主流程
tests/                         自动化测试
local_medical_html_extraction.py
```

## 安装

先进入项目根目录：

```powershell
cd G:\code\Extractor\scrap-ai-extractor
```

安装运行依赖：

```powershell
pip install -e .
```

如果你还要跑测试：

```powershell
pip install -e .[dev]
```

## 配置

仓库里只保留模板配置文件，不保留真实密钥。

你需要先复制一份本地配置：

```powershell
Copy-Item .\config\app_config.template.json .\config\app_config.json
```

然后编辑 `config/app_config.json`，填入你自己的 `DeepSeek API Key`。

示例：

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

- `config/app_config.json` 已加入 `.gitignore`，不会被提交到 GitHub
- 当前 `ScrapeGraphAI` 的 `DeepSeek` 封装内部固定使用官方地址，`base_url` 先保留在配置里做兼容字段
- 如果你设置了环境变量 `DEEPSEEK_API_KEY`，它会覆盖配置文件中的 `api_key`

## 怎么使用

### 1. 直接解析本地 HTML

这是你现在最直接的使用方式。

```powershell
python .\local_medical_html_extraction.py `
  --html-path "E:\Documents\Downloads\气血不足的病因_气血不足的症状_气血不足怎么治疗_气血不足的注意事项_中国医药信息查询平台.html" `
  --url "https://www.dayi.org.cn/symptom/xxx" `
  --prompt "提取疾病基本信息、病因、症状、诊断、治疗、日常注意事项和预防"
```

如果不传 `--prompt`，默认会使用医疗疾病页抽取提示。

如果想把结果保存到文件：

```powershell
python .\local_medical_html_extraction.py `
  --html-path "E:\Documents\Downloads\气血不足的病因_气血不足的症状_气血不足怎么治疗_气血不足的注意事项_中国医药信息查询平台.html" `
  --output-file ".\result.json"
```

### 2. 使用安装后的 CLI

```powershell
hybrid-web-extractor `
  --html-path "E:\Documents\Downloads\气血不足的病因_气血不足的症状_气血不足怎么治疗_气血不足的注意事项_中国医药信息查询平台.html" `
  --url "https://www.dayi.org.cn/symptom/xxx" `
  --prompt "提取疾病基本信息、病因、症状、诊断、治疗、日常注意事项和预防"
```

### 3. 作为本地 API 服务使用

启动服务：

```powershell
@'
from hybrid_extractor.api_server import run_server
run_server()
'@ | python -
```

默认监听地址：

- `http://127.0.0.1:8000`

启动后，直接在浏览器打开：

- `http://127.0.0.1:8000/`

即可使用内置的简洁网页界面，填写 URL、Prompt 和 HTML 源码后直接发起解析。

可用接口：

- `POST /extract`
- `GET /templates`
- `GET /health`

示例请求：

```powershell
$body = @{
  url = "https://www.dayi.org.cn/symptom/xxx"
  raw_html = [System.IO.File]::ReadAllText("E:\Documents\Downloads\气血不足的病因_气血不足的症状_气血不足怎么治疗_气血不足的注意事项_中国医药信息查询平台.html")
  user_prompt = "提取疾病基本信息、病因、症状、诊断、治疗、日常注意事项和预防"
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/extract" `
  -Method Post `
  -ContentType "application/json; charset=utf-8" `
  -Body $body
```

查看当前已加载模板：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/templates" -Method Get
```

## 输出结果怎么看

返回结果里比较重要的字段有：

- `data`：真正的结构化结果
- `template_id`：命中的模板 ID
- `extractor_type`：`deterministic`、`llm` 或 `hybrid`
- `validation_report`：字段覆盖率和校验结果
- `debug_trace`：分类结果、指纹、模板匹配和提示词版本等调试信息

如果是未知模板且 LLM 回退成功，系统会额外产出候选模板文件：

- `data/template_candidates/`

候选模板里当前会保留两阶段中间结果：

- `analysis`：字段锚点、字段形态、可确定性分析
- `proposed_plan`：根据分析生成的 DSL 规则计划

如果是已知模板且解析成功，系统会更新或保存模板清单：

- `data/template_store/`

## 当前实现说明

### 内部提示词策略

系统把提示词分成两层：

- 用户提示词：只关注业务目标
- 系统内部提示词：只负责输出约束、字段稳定性、证据约束和模板固化约束

这样做的目的是：

- 让调用方接口保持稳定
- 后续可以独立升级内部提示词
- 方便把模板固化能力逐步做强

### 模板固化的两阶段设计

当前运行时模板固化采用两阶段：

1. 先做模板分析
2. 再生成 DSL 计划

第一版里这两个阶段已经有明确的数据结构和持久化格式，后面可以继续接入真正的 `LLM analysis -> LLM DSL synthesis`。

## 测试

运行测试：

```powershell
pytest -q
```

## 文档

- [需求文档](G:\code\Extractor\scrap-ai-extractor\docs\requirements.md)
- [架构设计](G:\code\Extractor\scrap-ai-extractor\docs\architecture.md)
