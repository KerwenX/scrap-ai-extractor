# 架构设计

## 1. 架构目标

MVP 采用分层架构，确保后续可以演进到多模板、多站点和多页面场景。

这里的“场景”强调同一站点内的不同页面类型，例如：

- 疾病详情页
- 医疗问答页
- 药品详情页
- 医生详情页

## 2. 核心设计模式

- `Strategy`
  - 模板解析器、LLM 回退抽取器都以接口形式组织
- `Registry`
  - 模板注册中心负责模板识别和解析器分发
- `Classifier`
  - 页面分类器负责先识别站点与页面场景，再进入模板匹配
- `Orchestrator`
  - `HybridExtractionEngine` 负责执行流程编排
- `Value Object`
  - 请求、响应、模板元数据、校验报告统一建模

## 3. 运行流程

```text
Request(url, raw_html, prompt)
  -> HTML 预处理
  -> 站点 / 场景分类
  -> 意图识别
  -> 模板匹配
  -> 已知模板? -> 确定性解析
       -> 校验通过 -> 返回
       -> 校验失败 -> LLM 回退
  -> 未知模板 -> LLM 回退
  -> 校验
  -> 输出结果与调试信息
```

## 4. 模块划分

### `models.py`

定义请求、响应、校验结果、字段证据等模型。

### `preprocessing.py`

负责 HTML 清洗、标题/描述提取和文本标准化。

### `intent.py`

负责将自然语言 prompt 解析成内部抽取意图。

### `classification.py`

负责站点识别和页面场景识别。

### `fingerprinting.py`

负责生成页面指纹，用于判断当前页面是否可以复用已固化模板。

### `services/template_service.py`

负责模板 manifest 和候选模板的本地持久化。由于它们是 JSON 文件，因此可以直接迁移到其他机器使用。

### `controllers/extraction_controller.py`

负责 API / CLI 入口层的请求编排，保持 controller 与 service 分离。

### `templates/`

存放模板解析器。当前提供：

- `DayiDiseaseTemplateParser`
- `DayiQATemplateParser`

### `extractors/llm.py`

负责 LLM 回退抽取。

### `engine.py`

负责执行编排、失败回退、置信度和最终响应组装。

### `logging_utils.py`

负责控制台和文件日志初始化。

## 5. 模板规则

模板规则单独放在 `config/templates/` 下。这样做的好处：

- 规则和业务代码分离
- 后续支持模板版本化和热更新
- 便于引入审核流

此外，运行期还会用 `data/template_store/` 和 `data/template_candidates/` 来保存：

- 已固化模板 manifest
- LLM 成功回退后的候选模板

后者用于后续人工审核和规则固化。

## 6. 漂移检测

MVP 中漂移检测使用轻量策略：

- 确定性解析命中模板但缺少关键字段
- 字段覆盖率低于阈值
- 校验未通过

后续可引入：

- DOM 指纹对比
- 模板成功率监控
- 自动候选规则生成
