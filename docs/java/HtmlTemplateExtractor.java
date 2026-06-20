import com.fasterxml.jackson.databind.ObjectMapper;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Collection;

public class HtmlTemplateExtractor {
    private final ObjectMapper objectMapper;
    private final DeclarativeTemplateEngine templateEngine;
    private final TemplateManifestRepository manifestRepository;

    public HtmlTemplateExtractor() {
        this(new ObjectMapper());
    }

    public HtmlTemplateExtractor(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
        this.templateEngine = new DeclarativeTemplateEngine();
        this.manifestRepository = new TemplateManifestRepository(objectMapper);
    }

    public HtmlTemplateExtractor registerCodeHandler(
            String name,
            DeclarativeTemplateEngine.SelectorCodeHandler handler
    ) {
        templateEngine.registerCodeHandler(name, handler);
        return this;
    }

    public TemplateContract.ExtractionResult extract(
            String html,
            TemplateContract.TemplateManifest manifest
    ) {
        Document document = Jsoup.parse(html == null ? "" : html);
        return extract(document, manifest);
    }

    public TemplateContract.ExtractionResult extract(
            Document document,
            TemplateContract.TemplateManifest manifest
    ) {
        if (manifest == null || manifest.extractionPlan == null) {
            return new TemplateContract.ExtractionResult();
        }
        return templateEngine.execute(document, manifest.extractionPlan);
    }

    public TemplateContract.ExtractionExecutionResult extract(
            TemplateContract.ExtractionRequest request,
            Collection<TemplateContract.TemplateManifest> manifests
    ) {
        TemplateContract.ExtractionExecutionResult executionResult =
                new TemplateContract.ExtractionExecutionResult();
        executionResult.request = request;

        String html = request == null || request.html == null ? "" : request.html;
        Document document = Jsoup.parse(html);
        TemplateContract.PageFingerprint fingerprint = manifestRepository.buildFingerprint(document);
        executionResult.fingerprint = fingerprint;

        TemplateContract.TemplateManifest manifest = null;
        if (request != null
                && request.preferredTemplateId != null
                && !request.preferredTemplateId.trim().isEmpty()) {
            manifest = manifestRepository.findByTemplateId(
                    manifests,
                    request.preferredTemplateId.trim()
            );
        }

        if (manifest == null) {
            TemplateManifestRepository.ManifestSelection selection =
                    manifestRepository.findBestActiveManifest(manifests, request, fingerprint);
            if (selection != null) {
                manifest = selection.manifest;
                executionResult.matchScore = Double.valueOf(selection.score);
            }
        }

        executionResult.matchedManifest = manifest;
        executionResult.extractionResult = extract(document, manifest);
        return executionResult;
    }

    public TemplateContract.ExtractionResult extract(String html, String manifestJson) throws IOException {
        TemplateContract.TemplateManifest manifest =
                objectMapper.readValue(manifestJson, TemplateContract.TemplateManifest.class);
        return extract(html, manifest);
    }

    public TemplateContract.ExtractionResult extract(Path htmlPath, Path manifestPath) throws IOException {
        String html = new String(Files.readAllBytes(htmlPath), StandardCharsets.UTF_8);
        TemplateContract.TemplateManifest manifest = manifestRepository.loadManifest(manifestPath);
        return extract(html, manifest);
    }

    public TemplateContract.ExtractionExecutionResult extract(
            String url,
            String html,
            Collection<TemplateContract.TemplateManifest> manifests
    ) {
        TemplateContract.ExtractionRequest request = new TemplateContract.ExtractionRequest();
        request.url = url;
        request.html = html;
        return extract(request, manifests);
    }

    public TemplateContract.ExtractionExecutionResult extract(
            String url,
            Path htmlPath,
            Collection<TemplateContract.TemplateManifest> manifests
    ) throws IOException {
        TemplateContract.ExtractionRequest request = new TemplateContract.ExtractionRequest();
        request.url = url;
        request.html = new String(Files.readAllBytes(htmlPath), StandardCharsets.UTF_8);
        return extract(request, manifests);
    }

    public TemplateContract.ExtractionResult extractByTemplateId(
            String html,
            Collection<TemplateContract.TemplateManifest> manifests,
            String templateId
    ) {
        TemplateContract.TemplateManifest manifest =
                manifestRepository.findByTemplateId(manifests, templateId);
        return extract(html, manifest);
    }

    public TemplateManifestRepository.ManifestSelection findBestManifest(
            String html,
            Collection<TemplateContract.TemplateManifest> manifests,
            String siteId,
            String scenario
    ) {
        Document document = Jsoup.parse(html == null ? "" : html);
        TemplateContract.PageFingerprint fingerprint = manifestRepository.buildFingerprint(document);
        return manifestRepository.findBestActiveManifest(manifests, fingerprint, siteId, scenario);
    }

    public TemplateManifestRepository.ManifestSelection findBestManifest(
            TemplateContract.ExtractionRequest request,
            Collection<TemplateContract.TemplateManifest> manifests
    ) {
        String html = request == null || request.html == null ? "" : request.html;
        Document document = Jsoup.parse(html);
        TemplateContract.PageFingerprint fingerprint = manifestRepository.buildFingerprint(document);
        return manifestRepository.findBestActiveManifest(manifests, request, fingerprint);
    }

    public TemplateContract.ExtractionResult extractBestMatch(
            String html,
            Collection<TemplateContract.TemplateManifest> manifests,
            String siteId,
            String scenario
    ) {
        TemplateManifestRepository.ManifestSelection selection =
                findBestManifest(html, manifests, siteId, scenario);
        if (selection == null) {
            return new TemplateContract.ExtractionResult();
        }
        return extract(html, selection.manifest);
    }

    public DeclarativeTemplateEngine templateEngine() {
        return templateEngine;
    }

    public TemplateManifestRepository manifestRepository() {
        return manifestRepository;
    }
}
