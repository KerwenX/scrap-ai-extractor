import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.List;

public class CachedTemplateExtractionService {
    private final Path templateDirectory;
    private final TemplateManifestRepository manifestRepository;
    private final HtmlTemplateExtractor extractor;

    private volatile List<TemplateContract.TemplateManifest> cachedManifests =
            Collections.<TemplateContract.TemplateManifest>emptyList();

    public CachedTemplateExtractionService(Path templateDirectory) throws IOException {
        this(templateDirectory, new TemplateManifestRepository(), new HtmlTemplateExtractor());
    }

    public CachedTemplateExtractionService(
            Path templateDirectory,
            TemplateManifestRepository manifestRepository,
            HtmlTemplateExtractor extractor
    ) throws IOException {
        this.templateDirectory = templateDirectory;
        this.manifestRepository = manifestRepository;
        this.extractor = extractor;
        refresh();
    }

    public synchronized void refresh() throws IOException {
        List<TemplateContract.TemplateManifest> manifests = manifestRepository.loadManifests(templateDirectory);
        this.cachedManifests = Collections.unmodifiableList(
                new ArrayList<TemplateContract.TemplateManifest>(manifests)
        );
    }

    public List<TemplateContract.TemplateManifest> getCachedManifests() {
        return cachedManifests;
    }

    public int size() {
        return cachedManifests.size();
    }

    public HtmlTemplateExtractor extractor() {
        return extractor;
    }

    public CachedTemplateExtractionService registerCodeHandler(
            String name,
            DeclarativeTemplateEngine.SelectorCodeHandler handler
    ) {
        extractor.registerCodeHandler(name, handler);
        return this;
    }

    public TemplateContract.ExtractionExecutionResult extract(String url, String html) {
        return extractor.extract(url, html, cachedManifests);
    }

    public TemplateContract.ExtractionExecutionResult extract(
            String url,
            Path htmlPath
    ) throws IOException {
        String html = new String(Files.readAllBytes(htmlPath), StandardCharsets.UTF_8);
        return extract(url, html);
    }

    public TemplateContract.ExtractionExecutionResult extract(
            TemplateContract.ExtractionRequest request
    ) {
        return extractor.extract(request, cachedManifests);
    }

    public TemplateContract.ExtractionResult extractByTemplateId(
            String html,
            String templateId
    ) {
        return extractor.extractByTemplateId(html, cachedManifests, templateId);
    }

    public TemplateManifestRepository.ManifestSelection findBestManifest(
            String html,
            String siteId,
            String scenario
    ) {
        return extractor.findBestManifest(html, cachedManifests, siteId, scenario);
    }

    public TemplateManifestRepository.ManifestSelection findBestManifest(
            TemplateContract.ExtractionRequest request
    ) {
        return extractor.findBestManifest(request, cachedManifests);
    }

    public TemplateContract.TemplateManifest findTemplateById(String templateId) {
        return manifestRepository.findByTemplateId(cachedManifests, templateId);
    }

    public Collection<TemplateContract.TemplateManifest> manifestsView() {
        return cachedManifests;
    }
}
