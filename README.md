# Hybrid Web Extractor

`Hybrid Web Extractor` 是一个面向网页结构化数据抽取的混合解析系统 MVP。

它的核心思路是：

- 首次遇到网页模板时，用 LLM 理解页面语义并完成抽取
- 已识别模板优先走固化的确定性解析器
- 确定性解析失败、字段缺失或校验不通过时，自动回退到 LLM
- 输出同时包含结构化结果、模板识别信息、校验报告和执行链路

当前版本聚焦单页 HTML 抽取，优先支持医疗疾病详情页。

## 功能

- 输入：`url + raw_html + 用户自然语言抽取需求`
- 模板识别：基于站点和 DOM 特征识别模板
- 确定性解析：对已知模板使用规则化解析器
- LLM 回退：对未知模板或规则失效页面自动回退
- 结果校验：基础结构校验、字段覆盖率校验、模板漂移信号输出
- 日志系统：控制台 + 文件日志

## 项目结构

```text
docs/                         需求与架构文档
config/templates/             模板规则定义
src/hybrid_extractor/         系统源码
tests/                        测试
local_medical_html_extraction.py
```

## 安装

```powershell
pip install -e .
```

如果要运行测试：

```powershell
pip install -e .[dev]
pytest
```

## 运行

针对本地 HTML 文件：

```powershell
python .\local_medical_html_extraction.py --html-path "E:\Documents\Downloads\气血不足的病因_气血不足的症状_气血不足怎么治疗_气血不足的注意事项_中国医药信息查询平台.html"
```

或者直接使用 CLI：

```powershell
hybrid-web-extractor --html-path "E:\Documents\Downloads\气血不足的病因_气血不足的症状_气血不足怎么治疗_气血不足的注意事项_中国医药信息查询平台.html" --url "https://www.dayi.org.cn/symptom/..." --prompt "提取疾病基本信息、病因、症状、诊断、治疗、日常注意事项和预防"
```

默认会在控制台输出 JSON 结果，也支持：

```powershell
hybrid-web-extractor ... --output-file result.json
```

## 当前范围

- 单页 HTML 输入
- 已知模板：`中国医药信息查询平台` 疾病详情页
- 未知模板：走 LLM 回退
- 模板规则更新与自动发布当前只保留接口和设计，不做自动上线

详细需求与设计见：

- [需求文档](G:\code\Extractor\scrap-ai-extractor\docs\requirements.md)
- [架构文档](G:\code\Extractor\scrap-ai-extractor\docs\architecture.md)
