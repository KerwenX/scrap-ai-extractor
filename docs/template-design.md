# 模板设计说明

## 1. 模板的定位

本项目里的“模板”不是手写站点 parser，也不是某个页面的一次性脚本。

模板的本质是：

- 某一类页面结构的可执行抽取方案
- 可落盘的 JSON 资产
- 可版本化、可迁移、可复用的 DSL 规则集合

LLM 负责第一次理解页面，模板负责把这次理解沉淀成后续可直接复用的确定性能力。

## 2. 为什么不用手写站点 parser

如果继续堆手写 parser，很快会出现这些问题：

- 同站点页面一多，代码里会充满 `if/else`
- 规则升级必须改代码、发版、回滚
- 规则难以迁移到别的机器或别的语言项目
- LLM 首次成功抽取之后，无法自然沉淀为后续复用能力

因此当前方向是：

- 核心代码尽量不写页面定制逻辑
- 抽取规则尽量沉淀到模板 JSON + DSL
- 通用能力沉淀到运行时算子和匹配策略

## 3. 模板分层

### 3.1 正式模板

正式模板对应 `TemplateManifest`，用于直接运行。

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
- `template_id` 表示模板家族下的具体版本

### 3.2 候选模板

候选模板对应 `TemplateCandidate`，用于记录一次 LLM 成功抽取后的中间结果。

关键字段：

- `fingerprint`
- `extracted_fields`
- `sample_data`
- `analysis`
- `proposed_plan`

候选模板不是最终模板，但它提供了固化所需的证据。

## 4. 模板家族，而不是页面样本

如果模板直接绑定某一个页面指纹，结果会是：

- 同结构不同内容页面无法复用
- 每个页面都会生成自己的模板
- 模板数量快速膨胀

所以当前策略是：

- `template_key` 以站点、场景、页面类型、URL 模式摘要为主
- DOM 指纹主要作为匹配证据和版本演化证据
- 指纹不再直接决定“是否属于全新模板家族”

## 5. 模板命中策略

模板命中不能只靠指纹。

当前 DSL 模板命中采用综合评分：

1. 先按 `site_id` 过滤
2. 再看 `scenario / page_type` 亲和度
3. 对模板逐个试跑
4. 统计运行时命中效果
5. 最后结合指纹相似度综合打分

关键评分项：

- `fingerprint_score`
- `selector_hit_rate`
- `required_hit_rate`
- `classification_affinity`
- `match_score`

这让系统能在“同站点、多相似页面模板并存”的情况下更稳定地选择正确模板。

## 6. 模板闭环

当前模板闭环已经收敛到三种动作：

- `create`
  - 没有同指纹正式模板，直接创建新模板
- `upgrade`
  - 有同指纹正式模板，但当前候选规则覆盖更完整，生成新版本并停用旧版本
- `reuse`
  - 既有模板已经覆盖当前候选规则，不再重复晋升

这避免了之前那种反直觉场景：

- 运行时没复用好旧模板，走了 LLM
- 但候选模板又因为“已有正式模板”而无法晋升

现在如果候选更强，系统会自动升级旧模板，而不是简单报“不可晋升”。

## 7. DSL 的职责边界

当前 DSL 负责两部分：

### 7.1 字段定位

选择器类型包括：

- `css`
- `id`
- `meta`
- `text_pattern`
- `section_tab`
- `label_value`
- `code`

其中 `label_value` 用来处理这类常见结构：

```html
<tr><td>作者</td><td>张三</td></tr>
<tr><td>医院</td><td>北京协和医院</td></tr>
```

这类定位方式具有明显的跨页面复用价值，不属于站点定制逻辑。

### 7.2 轻量后处理

后处理算子包括：

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

- 页面级规则放模板里
- 通用处理模式放运行时算子里
- 业务代码尽量不为具体站点改逻辑

## 8. 自动固化策略

自动固化不是“LLM 一成功就直接发版模板”，而是有门槛：

- 候选必须有 `proposed_plan`
- `proposed_plan` 必须真的包含可执行字段规则
- `required_fields` 必须与 DSL 可覆盖字段基本一致
- 同指纹已有正式模板时，优先判断是 `reuse` 还是 `upgrade`

另外，历史模板里如果 `required_fields` 明显大于 DSL 真实可执行字段，系统会自动做一次规范化，避免“模板刚固化就因为自校验失败而回退”。

## 9. 为什么模板适合迁移

模板当前以文件形式落盘在：

- `config/templates/`
- `data/template_store/`
- `data/template_candidates/`

这意味着迁移时只需要带上：

- 代码
- 配置
- 模板文件

而不需要依赖某个数据库里的隐式状态。

这也是后续给 Java 运行时做轻量模板消费器的基础。

## 10. 一句话总结

模板不是某个页面的临时解析脚本，而是某类页面结构化抽取方法的版本化资产。
