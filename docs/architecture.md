# 架构设计

## 1. 设计目标

系统只做网页解析，不做抓取。

核心目标：

- 已知模板时，优先走低成本、可复现的确定性解析
- 未知模板时，允许 LLM 首次理解页面并完成抽取
- 首次成功结果要能沉淀成后续可复用模板
- 模板要能跨机器、跨服务、跨语言复用

## 2. 分层结构

### controllers

负责接口编排，不直接承载核心抽取逻辑。

### services

负责模板存储、状态管理、候选模板管理等服务逻辑。

关键类：

- `TemplateService`

### engine

负责一次抽取请求的主流程编排。

关键类：

- `HybridExtractionEngine`

### registry

负责模板选择。

关键类：

- `TemplateRegistry`

### templates

负责模板执行。

当前重点是：

- `GenericRuleTemplateParser`

### runtime

负责执行正式模板里的 DSL 规则。

关键类：

- `RuleRuntime`

### extractors

负责兜底抽取能力。

当前主要是：

- `ScrapeGraphFallbackExtractor`

## 3. 主流程

一次请求的处理顺序：

1. 清洗 HTML
2. 解析 DOM
3. 页面分类
4. 生成页面指纹
5. 模板注册中心挑选最优模板
6. 如果命中模板，则执行 DSL
7. 校验结果
8. 校验失败或模板不命中时，回退到 LLM
9. LLM 成功后生成候选模板
10. 满足条件时自动固化为正式模板

## 4. 模板匹配设计

正式 DSL 模板的选择不再只依赖指纹。

当前策略：

1. 先按 `site_id` 过滤
2. 再看 `scenario/page_type` 亲和度
3. 对候选模板逐个试跑
4. 统计：
   - `selector_hit_rate`
   - `required_hit_rate`
5. 再结合 `fingerprint_score`
6. 计算 `match_score`
7. 选最高分模板

这样做的原因是：

- 指纹只能说明“像不像”
- 运行时命中率才能说明“能不能真正抽出来”

## 5. DSL 运行时设计

模板 DSL 的目标不是表达所有逻辑，而是表达最常见、最可复用的抽取规则。

当前选择器：

- `css`
- `id`
- `meta`
- `text_pattern`
- `section_tab`
- `label_value`
- `code`

当前通用后处理：

- `strip`
- `strip_cn_punctuation`
- `split_cn_list`
- `unique`
- `first_non_empty_line`
- `regex_extract`
- `regex_replace`
- `join`
- `filter_empty`
- `normalize_whitespace`
- `to_int`
- `to_float`

## 6. 模板资产设计

模板资产分三类目录：

- `config/templates/`
  - 仓库内置模板
- `data/template_store/`
  - 运行期正式模板
- `data/template_candidates/`
  - 运行期候选模板

这使模板天然具备：

- 可迁移
- 可审查
- 可版本化
- 可回放

## 7. 为什么避免页面定制逻辑

如果不断为某个站点、某个栏目写特殊 parser，系统会退化成脚本仓库。

当前架构明确要求：

- 页面差异优先由模板 JSON + DSL 承担
- 通用抽取能力沉淀为运行时选择器或算子
- 核心代码只做通用基础设施，不写页面定制

## 8. 当前工程优化点

本轮已经完成的关键优化：

- 模板家族 key 不再绑定单页 DOM 签名
- DSL 模板支持基于运行时命中率选择最优模板
- 新增 `label_value` 相对定位器
- 模板加载增加缓存
- 修复“回填指纹时覆盖掉原 DSL 模板”的问题

## 9. 后续演进方向

下一步建议继续加强：

- 候选模板生成时的通用字段定位能力
- 多样本模板固化验证
- 更细的模板评分与漂移检测
- 模板对比、灰度、回滚能力
- Java 等轻量运行时的模板消费能力
