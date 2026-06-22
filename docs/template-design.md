# 模板设计说明

## 1. 模板是什么

这里的“模板”不是手写站点 parser，也不是一次性的页面脚本。

模板的本质是：

- 某一类页面结构的可执行抽取方法
- 可落盘的 JSON 资产
- 可版本化、可迁移、可复用的 DSL 规则集合

LLM 负责第一次理解页面，模板负责把这次理解沉淀成后续可直接复用的确定性能力。

## 2. 为什么不用手写站点 parser

继续堆手写 parser，会很快出现这些问题：

- 同站点页面一多，代码里就会充满 `if/else`
- 规则升级必须改代码、发版、回滚
- 规则难以迁移到别的机器或别的语言项目
- LLM 首次抽取成功后，无法自然沉淀成通用资产

所以当前方向是：

- 核心代码尽量不写页面定制逻辑
- 抽取规则尽量沉淀到模板 `JSON + DSL`
- 通用能力沉淀到运行时算子和匹配策略

## 3. 模板分层

### 3.1 正式模板

正式模板对应 `TemplateManifest`，用于运行时直接匹配和执行。

关键字段：

- `template_id`
- `template_key`
- `site_id`
- `scenario`
- `page_type`
- `version`
- `lifecycle_status`
- `fingerprint`
- `required_fields`
- `extraction_plan`

其中：

- `template_key` 表示模板家族
- `template_id` 表示某个模板家族下的具体版本

### 3.2 候选模板

候选模板对应 `TemplateCandidate`，记录一次 LLM 成功抽取后的中间结果。

关键字段：

- `fingerprint`
- `extracted_fields`
- `sample_data`
- `analysis`
- `proposed_plan`
- `matched_template_id`

其中 `matched_template_id` 很关键：

- 如果它有值，说明这次 LLM fallback 是从一个已命中的旧模板退回出来的
- 这类候选才有资格升级旧模板家族
- 如果它为空，则说明本次请求根本没有命中旧模板，只能创建新模板

## 4. 模板命名策略

模板命名不能只靠标题，也不能直接绑定某一个页面。

当前推荐思路：

- `template_key` 以站点、场景、页面类型、URL 结构摘要、结构签名为主
- `template_id = template_key + version`

这样可以同时满足两类需求：

1. 同结构页面优先复用同一模板家族
2. 没命中旧模板的新页面，不会误覆盖现有模板家族

## 5. 模板命中策略

模板命中不只看 URL，也不只看 DOM 指纹。

当前正式模板命中采用：

1. 候选召回
2. DSL 实际执行
3. 运行时评分
4. 最终选择最高分模板

核心评分项：

- `required_hit_rate`
- `selector_hit_rate`
- `fingerprint_score`
- `classification_affinity`
- `site_affinity`
- `url_pattern_affinity`

这比“只看指纹”更稳，因为它直接面向“这套模板到底能不能抽出值”。

## 6. URL 在模板命中的作用

当前系统中，URL 只是模板检索加速器，不是最终决定器。

### 有 URL 时

- 用 URL 提取站点
- 用 URL 计算 `url_pattern_hash`
- 缩小候选模板范围

### 没 URL 时

- 不再从 HTML 推断 URL
- 不再用 HTML 里的外链、脚本、SVG URL 猜站点
- 直接做全库模板运行时评分匹配

因此当前行为是：

- `run_mode=auto`
  - 可以不传 URL
  - 未命中模板时可回退到 LLM
- `run_mode=template_only`
  - 也可以不传 URL
  - 但不会调用 LLM
  - 会直接做全库模板匹配

## 7. DSL 的职责边界

### 7.1 字段定位

当前 DSL 支持的选择器包括：

- `css`
- `id`
- `meta`
- `text_pattern`
- `section_tab`
- `label_value`
- `all_label_values`
- `all_sections`
- `code`

其中：

- `label_value` 适合定位“标签-值”型页面结构
- `all_label_values` 适合批量收集标签字段
- `all_sections` 适合批量收集标题分段内容

### 7.2 通用后处理

当前支持：

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

原则是：

- 页面级规则放模板
- 通用处理模式放运行时算子
- 业务代码尽量不为具体站点改逻辑

## 8. 为什么“无命中不升级”很重要

这是这轮架构收敛的关键点。

旧问题是：

- 运行时根本没命中旧模板
- 结果 LLM 成功后，又把当前页面拿去升级旧模板家族

这会造成逻辑悖论：

- 既然旧模板没有命中，为什么还能说明这是同一模板家族？

所以现在的规则是：

- 命中过旧模板，才允许升级旧模板
- 没命中过旧模板，就只能创建新模板

这样模板闭环才自洽。

## 9. AJCASS 论文页案例

`erj.ajcass.com` 的论文详情页，过去出现过：

- 同站点同结构页面仍频繁走 LLM
- 还不断生成 `v1 / v2 / v3`
- 模板字段规则却并不稳定

当前已经收敛到稳定模板：

- `ajcass_com_detail_page_detail_page_c5d7b04b_v3`

这个模板不再依赖某个页面级面包屑文案，而是使用稳定容器：

- `.content-right .title`
- `.content-right .time`
- `.content-right .message`

再配合正则拆出：

- `标题`
- `作者`
- `摘要`
- `关键词`
- `发表时间`
- `稿件来源`
- `期刊`

这样模板复用的是“页面结构”，而不是“某一篇文章的局部文案”。

## 10. 模板迁移能力

模板当前以文件形式落盘在：

- `config/templates/`
- `data/template_store/`
- `data/template_candidates/`

这意味着迁移时只需要带上：

- 代码
- 配置
- 模板文件

而不依赖某个数据库里的隐式状态。

这也是后续 Java 运行时消费模板的基础。
