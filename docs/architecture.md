# 架构设计

## 1. 设计目标

本项目采用分层架构，目标是支持以下能力：

- 已知模板低成本、高性能解析
- 未知模板可通过 LLM 快速完成抽取
- 模板规则可持久化、可迁移、可继续固化
- 解析逻辑与接口逻辑分离

这里的“模板”不是只针对单个页面，而是针对同站点下同类页面场景的结构模式。

## 2. 核心设计模式

### Strategy

不同的解析路径通过统一接口抽象：

- 确定性模板解析器
- LLM 回退抽取器

### Registry

模板注册中心负责：

- 管理已知模板
- 根据分类和页面指纹匹配模板
- 选择合适的解析器

### Orchestrator

`HybridExtractionEngine` 负责总流程编排：

- 预处理
- 意图识别
- 分类
- 模板匹配
- 确定性解析
- 校验
- LLM 回退
- 候选模板持久化

### Value Object

请求、响应、模板、规则、校验报告等统一建模，保证接口稳定。

## 3. 分层结构

### controllers

负责接口编排，不直接承载核心解析逻辑。

当前包括：

- `ExtractionController`

### services

负责服务级逻辑和持久化协调。

当前包括：

- `ExtractionService`
- `TemplateService`

### engine

负责解析主流程，是整个系统的核心编排器。

### templates

存放确定性模板解析器。

当前包括：

- `DayiDiseaseTemplateParser`
- `DayiQATemplateParser`
- `GenericRuleTemplateParser`

### extractors

存放回退抽取器。

当前主要是：

- `ScrapeGraphFallbackExtractor`

### config

负责路径常量和应用配置加载。

### docs / data / config

- `config/templates/`：内置模板定义
- `data/template_store/`：运行期已固化模板
- `data/template_candidates/`：运行期候选模板

## 4. 运行流程

```text
Request(url, raw_html, user_prompt)
  -> HTML 预处理
  -> 意图识别
  -> 页面分类
  -> 页面指纹生成
  -> 模板匹配
      -> 命中模板 -> 确定性解析 -> 校验
          -> 校验通过 -> 返回
          -> 校验失败 -> LLM 回退
      -> 未命中模板 -> LLM 回退
  -> LLM 结果校验
  -> 生成候选模板
  -> 返回结果
```

## 5. 模板匹配机制

模板匹配当前综合以下因素：

- `site_id`
- `scenario`
- 页面指纹相似度

如果已有模板指纹与当前页面足够接近，则优先复用该模板。

## 6. 声明式 DSL

项目当前已经支持声明式字段规则。

字段选择器类型包括：

- `css`
- `id`
- `meta`
- `text_pattern`
- `section_tab`
- `code`

后处理步骤包括：

- `strip`
- `strip_cn_punctuation`
- `split_cn_list`
- `unique`
- `first_non_empty_line`

这使模板可以文件化迁移，而不必完全依赖代码型解析器。

## 7. LLM 提示词架构

项目把提示词拆成两层：

### 外层：用户业务需求

调用方只需要描述：

- 要抽什么
- 结果希望是什么结构

### 内层：系统提示词契约

系统内部维护简洁但严格的提示词约束，用于控制：

- 只输出 JSON
- 尽量基于页面证据
- 字段命名保持稳定
- 为模板固化保留中间分析结果

相关逻辑位于：

- `src/hybrid_extractor/prompts.py`

## 8. 模板固化两阶段设计

当 LLM 回退成功时，系统不只保存最终 DSL，而是保存两阶段产物。

### 第一阶段：analysis

用于描述：

- 字段值类型
- 可能的 DOM 锚点
- 重复区块
- 哪些字段适合确定性抽取
- 哪些字段仍应保留 LLM 回退

### 第二阶段：proposed_plan

用于描述：

- 可执行的 DSL 规则
- 适用字段
- 后处理步骤

这使后续模板审核和规则固化更可控。

## 9. 配置设计

### 仓库内文件

- `config/app_config.template.json`

### 本地文件

- `config/app_config.json`

真实密钥只应该放在本地配置文件或环境变量中，不应该进入版本库。

当前配置加载优先级为：

1. 环境变量
2. `config/app_config.json`
3. 代码默认值

## 10. 可迁移性设计

为了让这套解析能力可以迁移到别的机器上继续使用，项目把运行期产物尽量落成文件：

- 模板 manifest
- 模板候选
- 声明式 DSL 计划

后续只要复制项目代码、模板文件和本地配置，就可以在另一台机器上继续运行。
