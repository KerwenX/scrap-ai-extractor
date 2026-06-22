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

## 10. AJCASS 论文页实测情况

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

## 11. Spring Boot 建议封装

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

## 12. 生产使用建议

推荐最终落地方式：

1. Python 项目负责模板生产和模板升级
2. Java 项目只消费正式模板
3. 模板目录外置
4. Java 服务启动时加载模板目录
5. 模板更新后调用 `reloadTemplates()`

这是最轻量、最稳定、最容易迁移的方案。
