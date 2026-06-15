# 需求文档

## 1. 背景

目标是构建一个面向网页数据抽取的混合解析系统。

系统只负责解析，不负责爬取。调用方需要自行提供：

- `url`
- `raw_html`
- 用户自然语言解析需求

系统输出结构化抽取结果，并在成本、性能、稳定性和可演进性之间取得平衡。

## 2. 产品目标

- 支持用户通过自然语言定义抽取目标
- 对首次出现的模板使用 LLM 进行语义理解和结构化抽取
- 对已识别模板优先使用确定性解析代码进行高效抽取
- 当固化解析器失效或字段缺失时，自动回退到 LLM
- 输出包含结果、质量校验和执行轨迹

## 3. 输入输出

### 输入

- `url`
- `raw_html`
- `user_prompt`
- 可选：`schema`

### 输出

- `data`
- `template_id`
- `extractor_type`
- `validation_report`
- `confidence`
- `drift_detected`
- `debug_trace`

## 4. MVP 范围

### 支持

- 单页 HTML 抽取
- 中文网页
- 同站点多页面场景的模板解析
- 医疗疾病详情页优先
- 模板识别
- 确定性解析 + LLM 回退
- 基础校验和日志

### 暂不支持

- 列表翻页抓取
- 登录态页面
- 自动发布新模板规则
- 多页面联动抽取

## 5. 功能需求

### 5.1 页面预处理

- 清理脚本、样式、SVG、iframe
- 提取页面标题、描述、主内容
- 保留 DOM 结构用于模板识别和规则抽取

### 5.2 意图理解

- 将自然语言抽取需求映射到内部抽取意图
- 对医疗疾病页识别基本字段需求

### 5.3 模板识别

- 识别站点和页面类型
- 为已知模板输出稳定 `template_id`

### 5.4 确定性解析

- 依据模板规则抽取字段
- 为每个字段记录命中规则和来源

### 5.5 LLM 回退

- 未命中模板时调用 LLM
- 校验失败时调用 LLM

### 5.6 结果校验

- 必填字段校验
- 字段类型校验
- 覆盖率校验
- 漂移信号输出

### 5.7 日志与可观测性

- 请求级日志
- 执行器选择日志
- 校验结果日志

## 6. 非功能需求

- 已知模板解析优先低成本
- 系统具备可测试性和可扩展性
- 模板和解析规则与业务代码分离
- 所有结果可追踪执行路径
## Template solidification contract

When LLM fallback succeeds and a page becomes a reusable template candidate, the system should preserve two runtime artifacts:

- template analysis: field shapes, likely anchors, repeatable sections, and weak deterministic candidates
- declarative DSL plan: reusable extraction rules generated from that analysis

This is a runtime requirement for future solidification, not only a documentation convention.
