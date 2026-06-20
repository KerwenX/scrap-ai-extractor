# Java 模板执行组件接入说明

这套 Java 代码只负责一件事：

- 读取本项目生成好的正式模板 JSON
- 基于模板执行 HTML 结构化抽取

它不包含：

- LLM 调用
- 模板生成
- 候选模板固化

也就是说，模板的生产仍然在当前 Python 项目里完成，而 Java 侧只负责“消费模板并执行”。

## 1. 适用场景

适合下面这类使用方式：

1. Python 项目负责首次解析、LLM 回退、模板沉淀
2. 运行中产出正式模板 JSON
3. Java 项目直接复制本目录下的关键类
4. Java 项目加载模板 JSON + HTML，执行确定性解析

## 2. 代码文件

建议复制这些文件到你的 Java 工程中：

- [TemplateContract.java](G:\code\Extractor\scrap-ai-extractor\docs\java\TemplateContract.java)
- [DeclarativeTemplateEngine.java](G:\code\Extractor\scrap-ai-extractor\docs\java\DeclarativeTemplateEngine.java)
- [TemplateManifestRepository.java](G:\code\Extractor\scrap-ai-extractor\docs\java\TemplateManifestRepository.java)
- [HtmlTemplateExtractor.java](G:\code\Extractor\scrap-ai-extractor\docs\java\HtmlTemplateExtractor.java)
- [CachedTemplateExtractionService.java](G:\code\Extractor\scrap-ai-extractor\docs\java\CachedTemplateExtractionService.java)

这些文件默认不带 package，方便你直接复制。接入正式工程后，你可以自行补上 package。

推荐的职责理解如下：

- `TemplateContract`
  - 模板 JSON 对应的数据契约
  - 包含 `TemplateManifest`、`ExtractionPlan`、`FieldRule`、`ExtractionResult` 等对象
- `DeclarativeTemplateEngine`
  - 负责执行声明式 DSL
  - 负责 selector 解析和 postprocess 算子执行
- `TemplateManifestRepository`
  - 负责模板加载、模板选择、页面指纹生成、指纹相似度比较
- `HtmlTemplateExtractor`
  - 面向业务调用方的主入口
  - 屏蔽底层执行细节，直接提供“按模板执行”“按模板 ID 执行”“输入 url + html 自动匹配模板执行”等接口
- `CachedTemplateExtractionService`
  - 面向生产使用的模板缓存服务
  - 负责把模板目录加载到内存，并在后续请求中持续复用

## 3. 依赖

建议最少引入两个依赖：

```xml
<dependency>
  <groupId>org.jsoup</groupId>
  <artifactId>jsoup</artifactId>
  <version>1.18.1</version>
</dependency>

<dependency>
  <groupId>com.fasterxml.jackson.core</groupId>
  <artifactId>jackson-databind</artifactId>
  <version>2.18.2</version>
</dependency>
```

建议编译参数：

```xml
<maven.compiler.source>1.8</maven.compiler.source>
<maven.compiler.target>1.8</maven.compiler.target>
```

## 4. 主要能力

Java 版运行时当前支持：

- 按模板 JSON 执行字段抽取
- 直接输入 `url + html` 执行模板匹配与抽取
- 支持模板目录加载后长期驻留内存
- 支持手动刷新模板缓存
- 支持 `css` / `id` / `meta` / `text_pattern` / `section_tab` / `code`
- 支持模板后处理算子
- 支持按 `template_id` 直接执行
- 支持按 `site_id + scenario + fingerprint` 自动挑选最佳模板
- 支持注册自定义 `code handler`

## 5. 快速接入步骤

建议按下面的顺序接入：

1. 复制 Java 文件到你的项目里
2. 给这些类补上你自己的 package
3. 引入 `jsoup` 和 `jackson-databind`
4. 把 Python 项目导出的正式模板 JSON 放到你的资源目录或本地文件目录
5. 在业务代码里创建 `HtmlTemplateExtractor`
6. 选择一种调用模式执行抽取

最小接入通常只需要下面三步：

1. 准备 URL
2. 准备 HTML 字符串
3. 调用 `CachedTemplateExtractionService.extract(url, html)` 或 `extract(request)`

## 6. 主入口使用说明

### 6.1 `HtmlTemplateExtractor`

这是推荐直接给业务层使用的入口类。

它提供几类常用方法：

- `extract(String url, String html, Collection<TemplateManifest> manifests)`
  - 最直接的业务入口
  - 你只需要提供 URL、HTML 和模板集合
- `extract(TemplateContract.ExtractionRequest request, Collection<TemplateManifest> manifests)`
  - 更推荐的入口
  - 便于后续扩展 `siteId`、`scenario`、`preferredTemplateId`

- `extract(String html, TemplateContract.TemplateManifest manifest)`
  - 已经拿到模板对象时使用
- `extract(String html, String manifestJson)`
  - 直接传模板 JSON 文本时使用
- `extract(Path htmlPath, Path manifestPath)`
  - 直接传 HTML 文件和模板文件路径时使用
- `extractByTemplateId(String html, Collection<TemplateManifest> manifests, String templateId)`
  - 内存里已加载多个模板，并且知道目标模板 ID 时使用
- `findBestManifest(TemplateContract.ExtractionRequest request, Collection<TemplateManifest> manifests)`
  - 使用请求对象先找最佳模板时使用
- `findBestManifest(String html, Collection<TemplateManifest> manifests, String siteId, String scenario)`
  - 需要先从模板列表里自动挑选最优模板时使用
- `extractBestMatch(String html, Collection<TemplateManifest> manifests, String siteId, String scenario)`
  - 让组件自动匹配模板并执行时使用
- `registerCodeHandler(...)`
  - 当模板中存在 `kind = code` 的 selector 时，用于注册对应处理器

### 6.2 `CachedTemplateExtractionService`

如果你不希望每次请求都重新从模板目录读取 JSON，推荐直接使用这个类。

它的职责是：

- 启动时一次性加载模板目录
- 把模板列表缓存在内存中
- 后续所有请求直接复用缓存模板
- 当模板目录有更新时，由你显式调用 `refresh()` 重新加载

常用方法包括：

- `refresh()`
- `getCachedManifests()`
- `size()`
- `extract(String url, String html)`
- `extract(Path htmlPath, String url)` 不提供，当前是 `extract(String url, Path htmlPath)`
- `extract(ExtractionRequest request)`
- `extractByTemplateId(String html, String templateId)`
- `findBestManifest(String html, String siteId, String scenario)`
- `findBestManifest(ExtractionRequest request)`
- `findTemplateById(String templateId)`
- `registerCodeHandler(...)`

### 6.3 `TemplateManifestRepository`

这个类更偏底层，适合用于：

- 批量加载模板目录
- 手动管理模板缓存
- 手动做模板命中分析
- 单独做页面指纹生成和比对

常用方法包括：

- `loadManifest(Path path)`
- `loadManifests(Path directory)`
- `findByTemplateId(...)`
- `findBestActiveManifest(...)`
- `buildFingerprint(Document document)`
- `compareFingerprints(left, right)`
- `resolveSiteId(request)`

### 6.4 `DeclarativeTemplateEngine`

这个类一般不建议业务层直接使用，除非你要：

- 单独测试某一份 DSL
- 单独扩展算子或 code handler
- 在更低层封装自己的执行链路

### 6.5 `TemplateContract.ExtractionRequest`

如果你希望入口更稳定，推荐直接用请求对象。

当前请求对象支持这些字段：

- `url`
- `html`
- `siteId`
- `scenario`
- `preferredTemplateId`

其中：

- `url` 和 `html` 是最基本输入
- `siteId` 可选；不传时会优先尝试从 URL host 自动推断
- `scenario` 可选；传了会用于缩小模板匹配范围
- `preferredTemplateId` 可选；传了会优先按该模板执行

### 6.6 `TemplateContract.ExtractionExecutionResult`

如果你走的是“`url + html` 自动匹配模板”的主入口，返回值建议使用执行结果对象。

它包含：

- `request`
- `matchedManifest`
- `fingerprint`
- `matchScore`
- `extractionResult`

## 7. 已支持的后处理算子

当前 Java 版与 Python 版保持一致，支持：

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

## 8. 使用示例

### 8.1 直接按模板文件执行

```java
HtmlTemplateExtractor extractor = new HtmlTemplateExtractor();
TemplateContract.ExtractionResult result = extractor.extract(
    java.nio.file.Paths.get("page.html"),
    java.nio.file.Paths.get("paper_detail_v1.json")
);

System.out.println(result.data);
```

### 8.2 直接传 `url + html` 自动匹配模板并抽取

```java
CachedTemplateExtractionService service =
    new CachedTemplateExtractionService(java.nio.file.Paths.get("template_store"));
String url = "https://example.com/article/123";
String html = new String(
    java.nio.file.Files.readAllBytes(java.nio.file.Paths.get("page.html")),
    java.nio.charset.StandardCharsets.UTF_8
);

TemplateContract.ExtractionExecutionResult result =
    service.extract(url, html);

if (result.matchedManifest != null) {
    System.out.println(result.matchedManifest.templateId);
    System.out.println(result.matchScore);
}
System.out.println(result.extractionResult.data);
```

### 8.3 使用请求对象执行

```java
CachedTemplateExtractionService service =
    new CachedTemplateExtractionService(java.nio.file.Paths.get("template_store"));

TemplateContract.ExtractionRequest request = new TemplateContract.ExtractionRequest();
request.url = "https://example.com/article/123";
request.html = new String(
    java.nio.file.Files.readAllBytes(java.nio.file.Paths.get("page.html")),
    java.nio.charset.StandardCharsets.UTF_8
);
request.scenario = "article_detail";

TemplateContract.ExtractionExecutionResult result = service.extract(request);
System.out.println(result.extractionResult.data);
```

### 8.4 模板缓存服务手动刷新

```java
CachedTemplateExtractionService service =
    new CachedTemplateExtractionService(java.nio.file.Paths.get("template_store"));

System.out.println(service.size());

// 当模板目录有新增或替换时，手动刷新一次缓存
service.refresh();

System.out.println(service.size());
```

### 8.5 先加载模板，再反复执行

```java
CachedTemplateExtractionService service =
    new CachedTemplateExtractionService(java.nio.file.Paths.get("template_store"));

String html = new String(
    java.nio.file.Files.readAllBytes(java.nio.file.Paths.get("page.html")),
    java.nio.charset.StandardCharsets.UTF_8
);

TemplateManifestRepository.ManifestSelection selection =
    service.findBestManifest(html, "example.com", "article_detail");

if (selection != null) {
    TemplateContract.ExtractionResult result =
        service.extractByTemplateId(html, selection.manifest.templateId);
    System.out.println(selection.manifest.templateId);
    System.out.println(result.data);
}
```

### 8.6 直接传入模板 JSON 字符串

```java
HtmlTemplateExtractor extractor = new HtmlTemplateExtractor();
String html = "<html><body><h1>示例标题</h1></body></html>";
String manifestJson = "{...}";

TemplateContract.ExtractionResult result = extractor.extract(html, manifestJson);
System.out.println(result.data);
```

### 8.7 注册自定义 code 算子

```java
CachedTemplateExtractionService service =
    new CachedTemplateExtractionService(java.nio.file.Paths.get("template_store"));

service.registerCodeHandler("extract_custom_blocks", (document, fieldRule, selectorRule) -> {
    List<String> values = new ArrayList<>();
    for (Element element : document.select(".custom-block")) {
        values.add(element.text());
    }
    return values;
});
```

## 9. 在业务工程中的推荐封装方式

如果你不想让业务代码直接接触底层细节，建议在自己的工程里再包一层服务，例如：

- `ArticleExtractionService`
- `TemplateDrivenHtmlParser`
- `PageStructuredDataService`

这层服务负责：

- 根据业务场景加载模板目录
- 维护模板缓存
- 根据 `url + html` 直接调 `extract(...)`
- 输出业务自己的结果对象

这样你后续即使替换模板目录、补充 code handler、增加校验逻辑，也不会影响上层业务代码。

## 10. 设计原则

Java 版运行时刻意保持轻量：

- 不引入服务框架
- 不耦合数据库
- 不耦合 HTTP 层
- 不引入 LLM

这样你可以在任何 Java 工程里，把它当成一个本地模板执行组件使用。

## 11. 边界说明

如果模板里只使用声明式 DSL 和标准后处理算子，Java 侧通常不需要改代码。

只有出现了新的“通用处理范式”时，才建议统一扩展一次 `DeclarativeTemplateEngine`，而不是为某个站点单独写补丁逻辑。
