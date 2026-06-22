import java.io.IOException;
import java.nio.file.Path;
import java.util.Collection;

/**
 * 面向业务调用方的模板抽取 API 门面。
 *
 * <p>这个类的目标是屏蔽底层实现细节，让调用方只关心：
 * <ul>
 *   <li>模板目录放在哪里</li>
 *   <li>传入 url / html / templateId 等参数</li>
 *   <li>拿到匹配模板和抽取结果</li>
 * </ul>
 *
 * <p>适合直接放到 Maven / Spring Boot 项目中作为统一入口使用。
 */
public class TemplateExtractionApi {
    private final CachedTemplateExtractionService cachedService;

    /**
     * 使用模板目录创建 API。
     *
     * @param templateDirectory 模板目录，目录下应为多个模板 JSON 文件
     */
    public TemplateExtractionApi(Path templateDirectory) throws IOException {
        this.cachedService = new CachedTemplateExtractionService(templateDirectory);
    }

    /**
     * 使用已创建好的缓存服务创建 API。
     *
     * <p>适合你已经在上层做了缓存生命周期管理的场景。
     */
    public TemplateExtractionApi(CachedTemplateExtractionService cachedService) {
        if (cachedService == null) {
            throw new IllegalArgumentException("cachedService must not be null");
        }
        this.cachedService = cachedService;
    }

    /**
     * 工厂方法：通过模板目录创建 API。
     */
    public static TemplateExtractionApi fromDirectory(Path templateDirectory) throws IOException {
        return new TemplateExtractionApi(templateDirectory);
    }

    /**
     * 重新加载模板目录。
     *
     * <p>当 Python 侧生成了新模板并同步到模板目录后，可调用此方法刷新缓存。
     */
    public synchronized void reloadTemplates() throws IOException {
        cachedService.refresh();
    }

    /**
     * 返回当前已加载的模板数量。
     */
    public int getLoadedTemplateCount() {
        return cachedService.size();
    }

    /**
     * 返回当前缓存中的模板清单。
     */
    public Collection<TemplateContract.TemplateManifest> listTemplates() {
        return cachedService.manifestsView();
    }

    /**
     * 根据 templateId 查询模板。
     */
    public TemplateContract.TemplateManifest getTemplate(String templateId) {
        return cachedService.findTemplateById(templateId);
    }

    /**
     * 注册自定义 code selector 处理器。
     *
     * <p>当模板中的 selector.kind = code 时会用到。
     */
    public TemplateExtractionApi registerCodeHandler(
            String name,
            DeclarativeTemplateEngine.SelectorCodeHandler handler
    ) {
        cachedService.registerCodeHandler(name, handler);
        return this;
    }

    /**
     * 自动匹配模板并执行抽取。
     *
     * @param url 页面 URL。用于优先缩小模板检索范围，不是最终决定模板的唯一依据
     * @param html 页面 HTML
     * @return 含匹配模板、匹配分数、指纹和抽取结果的完整执行结果
     */
    public TemplateContract.ExtractionExecutionResult extract(String url, String html) {
        return cachedService.extract(url, html);
    }

    /**
     * 自动匹配模板并执行抽取。
     *
     * @param url 页面 URL
     * @param htmlPath 本地 HTML 文件路径
     */
    public TemplateContract.ExtractionExecutionResult extract(String url, Path htmlPath)
            throws IOException {
        return cachedService.extract(url, htmlPath);
    }

    /**
     * 使用请求对象自动匹配模板并执行抽取。
     *
     * <p>适合需要传入 scenario / preferredTemplateId / siteId 的场景。
     */
    public TemplateContract.ExtractionExecutionResult extract(
            TemplateContract.ExtractionRequest request
    ) {
        return cachedService.extract(request);
    }

    /**
     * 仅做模板选择，不执行抽取。
     *
     * @param url 页面 URL
     * @param html 页面 HTML
     * @return 最佳模板及匹配分数；如果找不到匹配模板则返回 null
     */
    public TemplateManifestRepository.ManifestSelection findBestTemplate(String url, String html) {
        TemplateContract.ExtractionRequest request = new TemplateContract.ExtractionRequest();
        request.url = url;
        request.html = html;
        return cachedService.findBestManifest(request);
    }

    /**
     * 仅做模板选择，不执行抽取。
     *
     * @param request 抽取请求对象
     */
    public TemplateManifestRepository.ManifestSelection findBestTemplate(
            TemplateContract.ExtractionRequest request
    ) {
        return cachedService.findBestManifest(request);
    }

    /**
     * 指定模板 ID 直接执行抽取，不走自动匹配。
     */
    public TemplateContract.ExtractionResult extractByTemplateId(String html, String templateId) {
        return cachedService.extractByTemplateId(html, templateId);
    }

    /**
     * 指定模板对象直接执行抽取。
     */
    public TemplateContract.ExtractionResult extractByTemplate(
            String html,
            TemplateContract.TemplateManifest manifest
    ) {
        return cachedService.extractor().extract(html, manifest);
    }

    /**
     * 指定模板 JSON 文件直接执行抽取。
     */
    public TemplateContract.ExtractionResult extractByTemplateFile(
            Path htmlPath,
            Path manifestPath
    ) throws IOException {
        return cachedService.extractor().extract(htmlPath, manifestPath);
    }

    /**
     * 获取底层缓存服务。
     *
     * <p>如果上层还需要更细粒度能力，可以继续向下使用。
     */
    public CachedTemplateExtractionService rawService() {
        return cachedService;
    }
}
