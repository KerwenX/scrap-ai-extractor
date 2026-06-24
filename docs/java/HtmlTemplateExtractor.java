import com.fasterxml.jackson.databind.ObjectMapper;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Comparator;
import java.util.List;

public class HtmlTemplateExtractor {
    private static final int CHEAP_TOP_K = 5;
    private final ObjectMapper objectMapper;
    private final DeclarativeTemplateEngine templateEngine;
    private final TemplateManifestRepository manifestRepository;

    public HtmlTemplateExtractor() {
        this(TemplateManifestRepository.buildDefaultObjectMapper());
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
                    selectBestManifest(request, manifests, document, fingerprint);
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
        TemplateContract.ExtractionRequest request = new TemplateContract.ExtractionRequest();
        request.siteId = siteId;
        request.scenario = scenario;
        request.html = html;
        return selectBestManifest(request, manifests, document, fingerprint);
    }

    public TemplateManifestRepository.ManifestSelection findBestManifest(
            TemplateContract.ExtractionRequest request,
            Collection<TemplateContract.TemplateManifest> manifests
    ) {
        String html = request == null || request.html == null ? "" : request.html;
        Document document = Jsoup.parse(html);
        TemplateContract.PageFingerprint fingerprint = manifestRepository.buildFingerprint(document);
        return selectBestManifest(request, manifests, document, fingerprint);
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

    private TemplateManifestRepository.ManifestSelection selectBestManifest(
            TemplateContract.ExtractionRequest request,
            Collection<TemplateContract.TemplateManifest> manifests,
            Document document,
            TemplateContract.PageFingerprint fingerprint
    ) {
        List<TemplateContract.TemplateManifest> recalled =
                manifestRepository.recallActiveManifests(manifests, request, fingerprint);
        if (recalled.isEmpty()) {
            return null;
        }

        List<ScoredManifest> cheapRanked = new ArrayList<ScoredManifest>();
        for (TemplateContract.TemplateManifest manifest : recalled) {
            cheapRanked.add(new ScoredManifest(
                    manifest,
                    manifestRepository.cheapScoreManifest(manifest, request, fingerprint)
            ));
        }
        cheapRanked.sort((left, right) -> Double.compare(right.score, left.score));

        String resolvedSiteId = manifestRepository.resolveSiteId(request);
        TemplateContract.TemplateManifest bestManifest = null;
        double bestScore = 0.0d;

        int limit = Math.min(CHEAP_TOP_K, cheapRanked.size());
        for (int i = 0; i < limit; i++) {
            ScoredManifest evaluated = expensiveScoreManifest(
                    document,
                    cheapRanked.get(i).manifest,
                    request,
                    fingerprint,
                    resolvedSiteId
            );
            if (evaluated.score <= bestScore) {
                continue;
            }
            bestManifest = evaluated.manifest;
            bestScore = evaluated.score;
            if (shouldEarlyExit(evaluated)) {
                break;
            }
        }

        if (bestManifest == null) {
            return null;
        }
        return new TemplateManifestRepository.ManifestSelection(bestManifest, bestScore, fingerprint);
    }

    private ScoredManifest expensiveScoreManifest(
            Document document,
            TemplateContract.TemplateManifest manifest,
            TemplateContract.ExtractionRequest request,
            TemplateContract.PageFingerprint fingerprint,
            String resolvedSiteId
    ) {
        double fingerprintScore = 0.0d;
        if (manifest.fingerprint != null && fingerprint != null) {
            fingerprintScore = manifestRepository.compareFingerprints(fingerprint, manifest.fingerprint);
        }
        double siteAffinity = manifestRepository.siteAffinityValue(manifest.siteId, resolvedSiteId);
        double urlPatternAffinity = manifestRepository.urlPatternAffinityForUrl(
                manifest,
                request == null ? null : request.url
        );
        boolean scenarioProvided = request != null
                && request.scenario != null
                && !request.scenario.trim().isEmpty();
        double scenarioAffinity = scenarioAffinity(manifest, request == null ? null : request.scenario);

        TemplateContract.ExtractionResult extracted = extract(document, manifest);
        double selectorHitRate = selectorHitRate(extracted.data, manifest);
        ValidationSummary validation = validateRequiredFields(extracted.data, manifest.requiredFields);
        double requiredHitRate = validation.coverage;

        double score = 0.42d * requiredHitRate
                + 0.22d * selectorHitRate
                + 0.15d * fingerprintScore
                + 0.11d * scenarioAffinity
                + 0.07d * siteAffinity
                + 0.03d * urlPatternAffinity;

        if (selectorHitRate >= 0.85d && requiredHitRate >= 0.85d) {
            score += 0.08d;
        } else if (validation.passed && selectorHitRate >= 0.60d) {
            score += 0.04d;
        }

        if (scenarioProvided && manifest.fingerprint != null && scenarioAffinity < 0.30d && fingerprintScore < 0.30d) {
            score = 0.0d;
        } else if (scenarioProvided && manifest.fingerprint == null && scenarioAffinity < 0.30d && selectorHitRate < 0.90d) {
            score = 0.0d;
        } else if (!validation.passed && selectorHitRate < 0.50d) {
            score = 0.0d;
        } else if (selectorHitRate < 0.35d) {
            score = 0.0d;
        }

        return new ScoredManifest(
                manifest,
                Math.min(score, 1.0d),
                selectorHitRate,
                requiredHitRate,
                fingerprintScore,
                siteAffinity,
                urlPatternAffinity,
                scenarioAffinity
        );
    }

    private double selectorHitRate(
            java.util.Map<String, Object> data,
            TemplateContract.TemplateManifest manifest
    ) {
        if (manifest == null || manifest.extractionPlan == null || manifest.extractionPlan.fields == null) {
            return 0.0d;
        }
        int totalFields = manifest.extractionPlan.fields.size();
        if (totalFields <= 0) {
            return 0.0d;
        }
        int hitCount = 0;
        for (TemplateContract.FieldRule field : manifest.extractionPlan.fields) {
            if (hasValue(data.get(field.fieldName))) {
                hitCount++;
            }
        }
        return (double) hitCount / (double) totalFields;
    }

    private ValidationSummary validateRequiredFields(
            java.util.Map<String, Object> data,
            List<String> requiredFields
    ) {
        List<String> required = requiredFields == null ? new ArrayList<String>() : requiredFields;
        if (required.isEmpty()) {
            boolean hasAnyValue = false;
            for (Object value : data.values()) {
                if (hasValue(value)) {
                    hasAnyValue = true;
                    break;
                }
            }
            return new ValidationSummary(hasAnyValue, hasAnyValue ? 1.0d : 0.0d, false);
        }

        int hitCount = 0;
        boolean missingName = false;
        for (String field : required) {
            if (hasValue(data.get(field))) {
                hitCount++;
            } else if ("name".equals(field)) {
                missingName = true;
            }
        }
        double coverage = (double) hitCount / (double) required.size();
        boolean passed = coverage >= 0.60d && !missingName;
        return new ValidationSummary(passed, coverage, missingName);
    }

    private boolean hasValue(Object value) {
        if (value == null) {
            return false;
        }
        if (value instanceof String) {
            return !((String) value).trim().isEmpty();
        }
        if (value instanceof java.util.Collection) {
            return !((java.util.Collection<?>) value).isEmpty();
        }
        if (value instanceof java.util.Map) {
            return !((java.util.Map<?, ?>) value).isEmpty();
        }
        return true;
    }

    private double scenarioAffinity(TemplateContract.TemplateManifest manifest, String scenario) {
        if (scenario == null || scenario.trim().isEmpty()) {
            return 0.50d;
        }
        if (scenario.equals(manifest.scenario)) {
            return 1.0d;
        }
        if ("unknown".equals(scenario) || "unknown".equals(manifest.scenario)) {
            return 0.40d;
        }
        return 0.10d;
    }

    private boolean shouldEarlyExit(ScoredManifest evaluated) {
        return evaluated.urlPatternAffinity >= 1.0d
                && evaluated.siteAffinity >= 0.85d
                && evaluated.requiredHitRate >= 0.95d
                && evaluated.selectorHitRate >= 0.95d;
    }

    private static class ValidationSummary {
        private final boolean passed;
        private final double coverage;
        private final boolean missingName;

        private ValidationSummary(boolean passed, double coverage, boolean missingName) {
            this.passed = passed;
            this.coverage = coverage;
            this.missingName = missingName;
        }
    }

    private static class ScoredManifest {
        private final TemplateContract.TemplateManifest manifest;
        private final double score;
        private final double selectorHitRate;
        private final double requiredHitRate;
        private final double fingerprintScore;
        private final double siteAffinity;
        private final double urlPatternAffinity;
        private final double scenarioAffinity;

        private ScoredManifest(TemplateContract.TemplateManifest manifest, double score) {
            this(manifest, score, 0.0d, 0.0d, 0.0d, 0.0d, 0.0d, 0.0d);
        }

        private ScoredManifest(
                TemplateContract.TemplateManifest manifest,
                double score,
                double selectorHitRate,
                double requiredHitRate,
                double fingerprintScore,
                double siteAffinity,
                double urlPatternAffinity,
                double scenarioAffinity
        ) {
            this.manifest = manifest;
            this.score = score;
            this.selectorHitRate = selectorHitRate;
            this.requiredHitRate = requiredHitRate;
            this.fingerprintScore = fingerprintScore;
            this.siteAffinity = siteAffinity;
            this.urlPatternAffinity = urlPatternAffinity;
            this.scenarioAffinity = scenarioAffinity;
        }
    }
}
