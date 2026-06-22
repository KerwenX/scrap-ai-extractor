# 架构设计

## 1. 设计目标

系统只做网页解析，不做抓取。

核心目标：

- 已知模板时，优先走低成本、可复现的确定性解析
- 未知模板时，允许 LLM 首次理解页面并完成抽取
- 首次成功结果要能沉淀为后续可复用模板
- 模板要能跨机器、跨服务、跨语言复用

## 2. 分层结构

### controllers

负责 API 编排和输入输出转换，不承载核心抽取逻辑。

### services

负责模板存储、版本管理、候选模板管理、模板晋升逻辑。

关键类：

- `TemplateService`

### engine

负责一次抽取请求的主流程编排。

关键类：

- `HybridExtractionEngine`

### registry

负责正式模板匹配与评分选择。

关键类：

- `TemplateRegistry`

### templates

负责模板执行。

当前重点：

- `GenericRuleTemplateParser`

### runtime

负责执行正式模板中的 DSL 规则。

关键类：

- `RuleRuntime`

### extractors

负责 LLM fallback 抽取能力。

当前主要是：

- `ScrapeGraphFallbackExtractor`

## 3. 主流程

一次请求的处理顺序：

1. 清洗 HTML
2. 构建 DOM
3. 页面分类
4. 生成页面指纹
5. 正式模板匹配与评分
6. 如果命中模板，则执行 DSL
7. 校验抽取结果
8. 若校验失败或未命中模板，则回退到 LLM
9. LLM 成功后生成候选模板
10. 满足条件时固化为正式模板

## 4. 当前模板匹配算法

当前正式模板匹配不再是“静态 URL 命中”或“静态指纹命中”，而是：

### 有 URL 时

1. 根据 `url` 提取站点
2. 按 `site_id` 缩小模板范围
3. 按 `url_pattern_hash` 优先排序
4. 对候选模板逐个执行 DSL
5. 根据运行结果和指纹打分
6. 选择得分最高模板

### 无 URL 时

1. 不再从 HTML 猜 URL
2. 站点记为 `unknown`
3. 不做站点硬过滤
4. 直接对正式模板库执行 DSL 评分匹配
5. 选择得分最高模板

### 两阶段优化

当前实现已经从“候选模板全量执行”改为“两阶段匹配”：

1. 先用便宜特征召回候选模板
   - `site_family`
   - `url_pattern_hash`
   - `scenario`
   - `fingerprint.dom_signature`
2. 先计算 cheap score
3. 只对 Top-K 候选执行真正的 DSL 抽取评分
4. 高置信命中时 early exit

这一步是面向海量模板仓最关键的性能优化。

## 5. 为什么不再从 HTML 提取 URL

过去曾尝试在缺失 URL 时，从 HTML 内扫描第一个 `http(s)://...` 作为站点来源。

这个策略已经废弃，原因如下：

- HTML 中的 URL 可能来自 SVG、脚本、第三方资源、外链
- 它们不代表当前页面真实来源
- 会导致模板匹配第一层就走错站点

例如论文页中出现的 `http://www.w3.org/2000/svg`，就会把页面误判为 `w3.org`，从而把真正的站点模板全部过滤掉。

因此当前策略明确为：

- 只相信真实输入 `url`
- 不从 HTML 反推站点

## 6. 模板最终是否命中，靠什么决定

模板最终是否使用，不是由 URL 直接决定，而是由运行结果决定。

主要评分项：

- `required_hit_rate`
- `selector_hit_rate`
- `fingerprint_score`
- `classification_affinity`
- `site_affinity`
- `url_pattern_affinity`

也就是说：

- URL 负责帮助检索候选模板
- 页面结构和字段命中效果负责最终拍板

## 7. 模板晋升与替换策略

当前模板闭环已经收紧为三种动作：

- `create`
  - 当前请求没有命中任何旧模板
  - LLM fallback 成功后，创建新模板

- `upgrade`
  - 当前请求先命中了旧模板
  - 但旧模板抽取失败或覆盖能力不足
  - LLM fallback 成功后，允许升级该旧模板家族

- `reuse`
  - 当前请求命中了旧模板
  - 旧模板能力已足够
  - 不再重复升级

关键变化：

- **没有命中旧模板时，不允许再去覆盖旧模板**
- 这样可以避免“运行时没命中，却又升级旧模板”的自相矛盾

## 8. 为什么避免页面定制逻辑

如果不断为某个站点或某个栏目写特例 parser，系统最终会退化成脚本集合。

当前架构明确要求：

- 页面差异优先由模板 `JSON + DSL` 承担
- 通用抽取能力沉淀为运行时选择器和算子
- 核心代码只做通用基础设施

## 9. 模板资产

模板资产分三类：

- `config/templates/`
  - 仓库内置模板
- `data/template_store/`
  - 运行期正式模板
  - 建议按站点分目录组织
- `data/template_candidates/`
  - 运行期候选模板

这样做的好处：

- 可迁移
- 可审查
- 可版本化
- 可回滚

## 10. AJCASS 论文页的收敛结果

`erj.ajcass.com` 同站点论文页目前已经收敛到统一正式模板：

- `ajcass_com_detail_page_detail_page_c5d7b04b_v3`

该模板使用稳定容器而不是页面级文案锚点：

- `.content-right .title`
- `.content-right .time`
- `.content-right .message`

因此它可以稳定复用到同站点多篇论文详情页，而不是每篇都重新走 LLM。

## 11. 批量处理优化

批量模板解析当前已经改成：

- JSONL 流式读取
- JSONL 流式写出
- 默认不在返回体里保留全部结果
- 可选多进程模板解析
- worker 进程内模板库按冻结模式加载一次

## 12. 后续演进方向

建议继续加强：

- 多样本模板固化验证
- 模板评分诊断可视化
- 模板对比、灰度、回滚能力
- Java 等轻量运行时的持续同步
