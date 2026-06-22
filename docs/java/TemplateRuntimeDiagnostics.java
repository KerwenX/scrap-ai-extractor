import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * Java 模板运行时诊断入口。
 *
 * <p>适用场景：
 * <ul>
 *   <li>同一份代码在不同机器上结果不一致</li>
 *   <li>怀疑模板目录没有真正加载到</li>
 *   <li>怀疑自动匹配失败，但指定模板其实可以抽取</li>
 *   <li>怀疑 HTML 编码、依赖版本、运行目录存在差异</li>
 * </ul>
 *
 * <p>命令行参数：
 * <pre>
 *   java TemplateRuntimeDiagnostics <templateDir> <htmlPath> [url] [templateId]
 * </pre>
 *
 * <p>示例：
 * <pre>
 *   java TemplateRuntimeDiagnostics ^
 *     G:\code\Extractor\scrap-ai-extractor\data ^
 *     E:\Documents\Downloads\新分类模式下的转移支付财力均等化效应再评估.html ^
 *     "https://erj.ajcass.com/#/issue?id=123010&year=2026&issue=5" ^
 *     ajcass_com_detail_page_detail_page_c5d7b04b_v3
 * </pre>
 */
public class TemplateRuntimeDiagnostics {
    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            printUsage();
            return;
        }

        Path templateDir = Paths.get(args[0]);
        Path htmlPath = Paths.get(args[1]);
        String url = args.length >= 3 ? trimToEmpty(args[2]) : "";
        String templateId = args.length >= 4 ? trimToEmpty(args[3]) : "";

        printEnvironment(templateDir, htmlPath, url, templateId);

        byte[] htmlBytes = Files.readAllBytes(htmlPath);
        String html = new String(htmlBytes, StandardCharsets.UTF_8);
        printHtmlDiagnostics(htmlBytes, html);

        TemplateExtractionApi api = TemplateExtractionApi.fromDirectory(templateDir);
        printTemplateDiagnostics(api);

        TemplateManifestRepository.ManifestSelection selection = api.findBestTemplate(url, html);
        printSelection(selection);

        TemplateContract.ExtractionExecutionResult autoResult = api.extract(url, html);
        printAutoExtraction(autoResult);

        String directTemplateId = !templateId.isEmpty()
                ? templateId
                : autoResult.matchedManifest == null ? "" : nullToEmpty(autoResult.matchedManifest.templateId);

        if (!directTemplateId.isEmpty()) {
            TemplateContract.ExtractionResult directResult = api.extractByTemplateId(html, directTemplateId);
            printDirectExtraction(directTemplateId, directResult);
        } else {
            System.out.println();
            System.out.println("== 指定模板直抽 ==");
            System.out.println("未执行。原因：既没有显式传入 templateId，自动匹配也没有返回 matchedTemplateId。");
        }
    }

    private static void printUsage() {
        System.out.println("用法：");
        System.out.println("  java TemplateRuntimeDiagnostics <templateDir> <htmlPath> [url] [templateId]");
        System.out.println();
        System.out.println("示例：");
        System.out.println("  java TemplateRuntimeDiagnostics "
                + "G:\\code\\Extractor\\scrap-ai-extractor\\data "
                + "E:\\Documents\\Downloads\\page.html "
                + "\"https://m.dayi.org.cn/doctor/1150764\" "
                + "dayi_org_cn_article_detail_article_page_f83933ac_v1");
    }

    private static void printEnvironment(
            Path templateDir,
            Path htmlPath,
            String url,
            String templateId
    ) throws IOException {
        System.out.println("== 运行环境 ==");
        System.out.println("java.version=" + System.getProperty("java.version"));
        System.out.println("java.vendor=" + System.getProperty("java.vendor"));
        System.out.println("os.name=" + System.getProperty("os.name"));
        System.out.println("os.arch=" + System.getProperty("os.arch"));
        System.out.println("default.charset=" + Charset.defaultCharset().name());
        System.out.println("user.dir=" + Paths.get("").toAbsolutePath().normalize());
        System.out.println("templateDir.input=" + templateDir);
        System.out.println("templateDir.absolute=" + templateDir.toAbsolutePath().normalize());
        System.out.println("templateDir.exists=" + Files.exists(templateDir));
        System.out.println("htmlPath.input=" + htmlPath);
        System.out.println("htmlPath.absolute=" + htmlPath.toAbsolutePath().normalize());
        System.out.println("htmlPath.exists=" + Files.exists(htmlPath));
        System.out.println("url=" + (url.isEmpty() ? "<empty>" : url));
        System.out.println("templateId=" + (templateId.isEmpty() ? "<empty>" : templateId));
    }

    private static void printHtmlDiagnostics(byte[] htmlBytes, String html) throws Exception {
        System.out.println();
        System.out.println("== HTML 诊断 ==");
        System.out.println("html.bytes=" + htmlBytes.length);
        System.out.println("html.text.length=" + html.length());
        System.out.println("html.sha256=" + sha256Hex(htmlBytes));
        System.out.println("html.preview=" + preview(html, 300));
        System.out.println("html.contains.h1=" + html.contains("<h1") + ", html.contains.body=" + html.contains("<body"));
        System.out.println("html.meta.charset.hint=" + extractCharsetHint(html));
    }

    private static void printTemplateDiagnostics(TemplateExtractionApi api) {
        System.out.println();
        System.out.println("== 模板加载 ==");
        System.out.println("loadedTemplateCount=" + api.getLoadedTemplateCount());

        Collection<TemplateContract.TemplateManifest> manifests = api.listTemplates();
        List<String> templateIds = new ArrayList<String>();
        for (TemplateContract.TemplateManifest manifest : manifests) {
            StringBuilder line = new StringBuilder();
            line.append(manifest.templateId);
            line.append(" | active=").append(manifest.active);
            line.append(" | site=").append(nullToEmpty(manifest.siteId));
            line.append(" | scenario=").append(nullToEmpty(manifest.scenario));
            line.append(" | urlPatternHash=").append(nullToEmpty(manifest.urlPatternHash));
            templateIds.add(line.toString());
        }
        System.out.println("loadedTemplates=" + templateIds);
    }

    private static void printSelection(TemplateManifestRepository.ManifestSelection selection) {
        System.out.println();
        System.out.println("== 自动匹配 ==");
        if (selection == null || selection.manifest == null) {
            System.out.println("matchedTemplateId=null");
            System.out.println("matchScore=null");
            return;
        }
        System.out.println("matchedTemplateId=" + selection.manifest.templateId);
        System.out.println("matchScore=" + selection.score);
        if (selection.fingerprint != null) {
            System.out.println("fingerprint.domSignature=" + nullToEmpty(selection.fingerprint.domSignature));
            System.out.println("fingerprint.headings=" + selection.fingerprint.headings);
        }
    }

    private static void printAutoExtraction(TemplateContract.ExtractionExecutionResult result) {
        System.out.println();
        System.out.println("== 自动抽取结果 ==");
        if (result == null) {
            System.out.println("result=null");
            return;
        }
        System.out.println("matchedManifest="
                + (result.matchedManifest == null ? "null" : result.matchedManifest.templateId));
        System.out.println("matchScore=" + result.matchScore);
        if (result.extractionResult == null) {
            System.out.println("extractionResult=null");
            return;
        }
        printDataSummary(result.extractionResult.data);
    }

    private static void printDirectExtraction(
            String templateId,
            TemplateContract.ExtractionResult result
    ) {
        System.out.println();
        System.out.println("== 指定模板直抽 ==");
        System.out.println("templateId=" + templateId);
        if (result == null) {
            System.out.println("result=null");
            return;
        }
        printDataSummary(result.data);
    }

    private static void printDataSummary(Map<String, Object> data) {
        if (data == null) {
            System.out.println("data=null");
            return;
        }
        System.out.println("data.size=" + data.size());
        System.out.println("data.keys=" + data.keySet());
        System.out.println("data=" + data);
    }

    private static String extractCharsetHint(String html) {
        String lower = html.toLowerCase(Locale.ROOT);
        List<String> hints = Arrays.asList("charset=utf-8", "charset=gbk", "charset=gb2312", "charset=gb18030");
        for (String hint : hints) {
            int index = lower.indexOf(hint);
            if (index >= 0) {
                return hint;
            }
        }
        return "<not-found>";
    }

    private static String preview(String text, int maxLength) {
        if (text == null) {
            return "<null>";
        }
        String normalized = text.replace("\r", "\\r").replace("\n", "\\n");
        if (normalized.length() <= maxLength) {
            return normalized;
        }
        return normalized.substring(0, maxLength) + "...";
    }

    private static String trimToEmpty(String value) {
        return value == null ? "" : value.trim();
    }

    private static String nullToEmpty(String value) {
        return value == null ? "" : value;
    }

    private static String sha256Hex(byte[] bytes) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        byte[] hashed = digest.digest(bytes);
        StringBuilder builder = new StringBuilder();
        for (byte b : hashed) {
            builder.append(String.format(Locale.ROOT, "%02x", b));
        }
        return builder.toString();
    }
}
