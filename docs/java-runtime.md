# Java 模板运行时说明

## 1. 目标

这套 Java 代码只负责一件事：

- 读取 Python 主项目已经生成好的正式模板 JSON
- 基于模板执行 HTML 结构化抽取

它不包含：

- LLM 调用
- 模板生成
- 候选模板晋升

也就是说：

1. Python 项目负责首轮抽取、模板固化、模板升级
2. Java 项目负责消费正式模板、匹配模板、执行抽取

## 2. 当前同步到 Java 的关键策略

Java 运行时当前应与 Python 主逻辑保持一致，尤其是这几条：

### 2.1 不从 HTML 推断 URL

Java 运行时不应该从 HTML 中扫描 `http(s)://...` 来反推站点。

原因与 Python 一样：

- HTML 里的 URL 可能是脚本、SVG、第三方资源
- 会把页面错误归类到完全无关的站点

Java 端应只信任真实输入的 `url`。

### 2.2 无 URL 时允许全库模板匹配

当 `url` 缺失时：

- 不要直接失败
- 不要猜站点
- 而是直接对正式模板做运行时评分匹配

### 2.3 只有命中过旧模板，才允许升级旧模板

Java 运行时本身不负责升级模板，但它消费的模板体系必须基于这个规则：

- 命中过旧模板后 fallback 成功，才允许升级旧模板
- 没命中过旧模板，不应该把新页面算作旧模板的新版本

## 3. 需要复制到 Java 项目的文件

如果你要在别的 Maven / Spring Boot 项目中直接消费模板，建议复制这些文件：

- [TemplateContract.java](./java/TemplateContract.java)
- [DeclarativeTemplateEngine.java](./java/DeclarativeTemplateEngine.java)
- [TemplateManifestRepository.java](./java/TemplateManifestRepository.java)
- [HtmlTemplateExtractor.java](./java/HtmlTemplateExtractor.java)
- [CachedTemplateExtractionService.java](./java/CachedTemplateExtractionService.java)
- [TemplateExtractionApi.java](./java/TemplateExtractionApi.java)
- [TemplateRuntimeDiagnostics.java](./java/TemplateRuntimeDiagnostics.java)

## 4. Maven 依赖

```xml
<dependency>
  <groupId>org.jsoup</groupId>
  <artifactId>jsoup</artifactId>
  <version>1.17.2</version>
</dependency>

<dependency>
  <groupId>com.fasterxml.jackson.core</groupId>
  <artifactId>jackson-databind</artifactId>
  <version>2.17.2</version>
</dependency>
```

Java 版本按 1.8：

```xml
<properties>
  <maven.compiler.source>1.8</maven.compiler.source>
  <maven.compiler.target>1.8</maven.compiler.target>
</properties>
```

## 5. 模板目录建议

### 5.1 生产环境推荐：外部目录

推荐直接传入一个外部模板目录：

```java
Path templateDir = Paths.get("D:/app/template_store");
TemplateExtractionApi api = TemplateExtractionApi.fromDirectory(templateDir);
```

正式模板现在推荐按站点分目录，例如：

```text
D:/app/template_store/
  m_dayi_org_cn/
    dayi_org_cn_article_detail_article_page_f83933ac_v1.json
  erj_ajcass_com/
    ajcass_com_detail_page_detail_page_c5d7b04b_v3.json
```

Java 运行时会递归扫描 `template_store/` 下的子目录，不要求所有模板平铺在同一层。

优点：

- 模板可热更新
- 不需要重新打包 jar
- Python 侧生成新模板后，直接同步目录即可

### 5.2 开发环境：resources

开发期可以把模板放在：

```text
src/main/resources/template_store/
```

本地直接运行时可这样读：

```java
Path templateDir = Paths.get("src/main/resources/template_store");
TemplateExtractionApi api = TemplateExtractionApi.fromDirectory(templateDir);
```

但生产环境不建议长期依赖这种路径。

## 6. `data` 和 `template_store` 的关系

Java 运行时已经兼容两种初始化方式：

```java
new CachedTemplateExtractionService(Paths.get("G:\\code\\Extractor\\scrap-ai-extractor\\data"));
```

或：

```java
new CachedTemplateExtractionService(Paths.get("G:\\code\\Extractor\\scrap-ai-extractor\\data\\template_store"));
```

如果传的是 `data`，并且下面存在 `template_store`，运行时会自动切换到 `data/template_store`。

## 7. 模板匹配逻辑

Java 端当前模板匹配应该遵循这套顺序：

1. 读取所有 `active` 正式模板
2. 如果有 URL：
   - 解析站点
   - 优先按 `url_pattern_hash` 排序
3. 如果没 URL：
   - 不做 HTML 站点猜测
   - 允许全库评分匹配
4. 对候选模板执行 DSL
5. 根据字段命中率、必填命中率、指纹、站点、URL pattern 等综合打分
6. 选择得分最高模板

也就是说：

- URL 负责缩小候选范围
- 页面结构和字段命中率决定最终使用哪个模板

## 8. 推荐直接使用的主入口

推荐业务方直接使用：

- `TemplateExtractionApi`

而不是让业务代码直接依赖一堆底层实现类。

### 8.1 常用接口

- `fromDirectory(Path templateDirectory)`
- `reloadTemplates()`
- `getLoadedTemplateCount()`
- `listTemplates()`
- `getTemplate(String templateId)`
- `extract(String url, String html)`
- `extract(String url, Path htmlPath)`
- `extract(ExtractionRequest request)`
- `findBestTemplate(String url, String html)`
- `findBestTemplate(ExtractionRequest request)`
- `extractByTemplateId(String html, String templateId)`
- `extractByTemplate(String html, TemplateManifest manifest)`
- `extractByTemplateFile(Path htmlPath, Path manifestPath)`

## 9. 使用示例

### 9.1 最常见：传入 URL + HTML

```java
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

public class Demo {
    public static void main(String[] args) throws Exception {
        Path templateDir = Paths.get("G:\\code\\Extractor\\scrap-ai-extractor\\data");
        TemplateExtractionApi api = TemplateExtractionApi.fromDirectory(templateDir);

        String url = "https://erj.ajcass.com/#/issue?id=123010&year=2026&issue=5&title=%E6%9C%80%E6%96%B0%E7%9B%AE%E5%BD%95";
        String html = new String(
                Files.readAllBytes(Paths.get("E:\\Documents\\Downloads\\新分类模式下的转移支付财力均等化效应再评估.html")),
                StandardCharsets.UTF_8
        );

        TemplateContract.ExtractionExecutionResult result = api.extract(url, html);
        System.out.println(result.matchedManifest == null ? null : result.matchedManifest.templateId);
        System.out.println(result.matchScore);
        System.out.println(result.extractionResult.data);
    }
}
```

### 9.2 不传 URL，直接扫正式模板库

```java
TemplateContract.ExtractionExecutionResult result = api.extract(
        "",
        html
);
```

适用场景：

- 本地 HTML 文件缺失来源 URL
- 你只想验证模板库里有没有模板能直接匹配这份页面

### 9.3 只找最佳模板，不执行抽取

```java
TemplateManifestRepository.ManifestSelection selection = api.findBestTemplate(url, html);
if (selection != null) {
    System.out.println(selection.manifest.templateId);
    System.out.println(selection.score);
}
```

### 9.4 指定模板直接抽取

```java
TemplateContract.ExtractionResult result =
        api.extractByTemplateId(html, "ajcass_com_detail_page_detail_page_c5d7b04b_v3");
System.out.println(result.data);
```

### 9.5 刷新模板目录缓存

```java
api.reloadTemplates();
System.out.println(api.getLoadedTemplateCount());
```

## 10. 跨机器失败时如何诊断

如果你遇到下面这种情况：

- 本机 Java 程序可以抽取成功
- 另一台机器代码、模板、HTML、Java 8 看起来都一致
- 但另一台机器抽取失败或返回空结果

优先不要猜，先跑诊断类：

- [TemplateRuntimeDiagnostics.java](./java/TemplateRuntimeDiagnostics.java)

### 10.1 诊断类作用

它会一次性打印这些信息：

- Java 版本、操作系统、默认字符集、工作目录
- 模板目录是否存在、HTML 文件是否存在
- HTML 字节长度、文本长度、SHA-256、前 300 个字符预览
- 实际加载到的模板数量与模板列表
- 自动匹配到的模板 ID 与分数
- 自动抽取结果
- 指定模板直抽结果

这能快速区分四类问题：

1. 模板根本没加载到
2. 自动匹配失败，但指定模板其实可以抽
3. HTML 读取编码不对，导致中文/结构信号失真
4. 另一台机器实际运行的依赖、工作目录、输入文件并不一致

### 10.2 运行方式

```java
java TemplateRuntimeDiagnostics <templateDir> <htmlPath> [url] [templateId]
```

示例：

```java
java TemplateRuntimeDiagnostics ^
  G:\code\Extractor\scrap-ai-extractor\data ^
  E:\Documents\Downloads\新分类模式下的转移支付财力均等化效应再评估.html ^
  "https://erj.ajcass.com/#/issue?id=123010&year=2026&issue=5" ^
  ajcass_com_detail_page_detail_page_c5d7b04b_v3
```

### 10.3 怎么看结果

如果输出表现为：

- `loadedTemplateCount=0`
  - 说明模板目录没加载对，先检查路径、打包方式、resources 读取方式

- `matchedTemplateId=null`，但“指定模板直抽”有结果
  - 说明问题在模板命中层，不在模板执行层

- “指定模板直抽”也为空
  - 说明问题更可能在 HTML 读取、编码、模板内容、依赖版本

- 两台机器 `html.sha256` 不一致
  - 说明你以为是同一份 HTML，但实际输入已经不同

- 两台机器 `loadedTemplates=` 不一致
  - 说明模板仓并没有真正同步一致

### 10.4 最常见的真实原因

按优先级，最值得先查的是：

1. 模板目录路径不一致，另一台机器没有真正读到模板仓
2. HTML 文件编码不同，却统一按 `UTF-8` 读取
3. 运行的不是同一份 class / jar
4. `jsoup` / `jackson` 版本不一致
5. 另一台机器工作目录不同，导致相对路径读取错位

## 11. AJCASS 论文页实测情况

当前 `erj.ajcass.com` 同站点论文页，已经可复用：

- `ajcass_com_detail_page_detail_page_c5d7b04b_v3`

实测可命中：

- `中国专利的经济价值：测度、特征及有效性.html`
- `外资开放式创新有助于“稳外资”目标的实现吗？——基于内外资价值链生产关联视角.html`
- `新分类模式下的转移支付财力均等化效应再评估.html`

可抽取字段包括：

- `标题`
- `作者`
- `摘要`
- `关键词`
- `发表时间`
- `稿件来源`
- `期刊`

## 12. Spring Boot 建议封装

推荐在业务工程里再包一层自己的服务，例如：

- `TemplateParsingService`
- `StructuredPageExtractionService`
- `TemplateDrivenExtractionFacade`

例如：

```java
@Service
public class TemplateParsingService {
    private final TemplateExtractionApi api;

    public TemplateParsingService() throws Exception {
        this.api = TemplateExtractionApi.fromDirectory(
                java.nio.file.Paths.get("D:/app/template_store")
        );
    }

    public java.util.Map<String, Object> extract(String url, String html) {
        TemplateContract.ExtractionExecutionResult result = api.extract(url, html);
        return result.extractionResult.data;
    }
}
```

## 13. 生产使用建议

推荐最终落地方式：

1. Python 项目负责模板生产和模板升级
2. Java 项目只消费正式模板
3. 模板目录外置
4. Java 服务启动时加载模板目录
5. 模板更新后调用 `reloadTemplates()`

这是最轻量、最稳定、最容易迁移的方案。
