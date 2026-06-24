import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.Comparator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class TemplateManifestRepository {
    private static final int CHEAP_TOP_K = 5;
    private static final int EXACT_URL_MATCH_LIMIT = 8;
    private final ObjectMapper objectMapper;

    public TemplateManifestRepository() {
        this(buildDefaultObjectMapper());
    }

    public TemplateManifestRepository(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    public static ObjectMapper buildDefaultObjectMapper() {
        ObjectMapper mapper = new ObjectMapper();
        mapper.setPropertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE);
        return mapper;
    }

    public TemplateContract.TemplateManifest loadManifest(Path path) throws IOException {
        return objectMapper.readValue(path.toFile(), TemplateContract.TemplateManifest.class);
    }

    public List<TemplateContract.TemplateManifest> loadManifests(Path directory) throws IOException {
        List<TemplateContract.TemplateManifest> manifests = new ArrayList<TemplateContract.TemplateManifest>();
        if (!Files.exists(directory)) {
            return manifests;
        }
        try (java.util.stream.Stream<Path> stream = Files.walk(directory)) {
            List<Path> files = stream
                    .filter(Files::isRegularFile)
                    .filter(path -> path.getFileName().toString().endsWith(".json"))
                    .sorted(Comparator.comparing(path -> directory.relativize(path).toString()))
                    .collect(Collectors.toList());
            for (Path path : files) {
                TemplateContract.TemplateManifest manifest = loadManifest(path);
                if (manifest.parserKey != null) {
                    manifests.add(normalizeManifest(manifest));
                }
            }
        }
        return manifests;
    }

    public TemplateContract.TemplateManifest findByTemplateId(
            Collection<TemplateContract.TemplateManifest> manifests,
            String templateId
    ) {
        for (TemplateContract.TemplateManifest manifest : manifests) {
            if (templateId.equals(manifest.templateId)) {
                return manifest;
            }
        }
        return null;
    }

    public ManifestSelection findBestActiveManifest(
            Collection<TemplateContract.TemplateManifest> manifests,
            TemplateContract.PageFingerprint fingerprint,
            String siteId,
            String scenario
    ) {
        return findBestActiveManifest(
                manifests,
                null,
                fingerprint,
                siteId,
                scenario
        );
    }

    public ManifestSelection findBestActiveManifest(
            Collection<TemplateContract.TemplateManifest> manifests,
            String url,
            TemplateContract.PageFingerprint fingerprint,
            String siteId,
            String scenario
    ) {
        TemplateContract.TemplateManifest bestManifest = null;
        double bestScore = 0.0d;
        String requestUrlPatternHash = buildUrlPatternHash(url);
        List<TemplateContract.TemplateManifest> recalled =
                recallCandidates(manifests, siteId, scenario, requestUrlPatternHash, fingerprint);
        List<ScoredManifest> cheapRanked = new ArrayList<ScoredManifest>();

        for (TemplateContract.TemplateManifest normalized : recalled) {
            cheapRanked.add(new ScoredManifest(
                    normalized,
                    cheapScore(normalized, siteId, scenario, requestUrlPatternHash, fingerprint)
            ));
        }
        cheapRanked.sort((left, right) -> Double.compare(right.score, left.score));

        int limit = Math.min(CHEAP_TOP_K, cheapRanked.size());
        for (int i = 0; i < limit; i++) {
            TemplateContract.TemplateManifest normalized = cheapRanked.get(i).manifest;
            double score = 0.0d;
            double urlPatternAffinity = urlPatternAffinity(normalized, requestUrlPatternHash);
            double siteAffinity = siteAffinity(normalized.siteId, siteId);
            double classificationAffinity = classificationAffinity(normalized, scenario);
            if (normalized.fingerprint != null && fingerprint != null) {
                score = compareFingerprints(fingerprint, normalized.fingerprint);
                if (score < 0.8d) {
                    continue;
                }
            } else if (normalized.extractionPlan != null) {
                score = 0.81d;
            }

            score += 0.07d * urlPatternAffinity + 0.05d * siteAffinity + 0.08d * classificationAffinity;

            if (score > bestScore) {
                bestScore = score;
                bestManifest = normalized;
                if (urlPatternAffinity >= 1.0d
                        && classificationAffinity >= 1.0d
                        && siteAffinity >= 0.85d
                        && score >= 0.95d) {
                    break;
                }
            }
        }

        if (bestManifest == null) {
            return null;
        }
        return new ManifestSelection(bestManifest, bestScore, fingerprint);
    }

    private List<TemplateContract.TemplateManifest> recallCandidates(
            Collection<TemplateContract.TemplateManifest> manifests,
            String siteId,
            String scenario,
            String requestUrlPatternHash,
            TemplateContract.PageFingerprint fingerprint
    ) {
        List<TemplateContract.TemplateManifest> active = new ArrayList<TemplateContract.TemplateManifest>();
        for (TemplateContract.TemplateManifest manifest : manifests) {
            TemplateContract.TemplateManifest normalized = normalizeManifest(manifest);
            if (!normalized.active || !"active".equals(normalized.lifecycleStatus)) {
                continue;
            }
            active.add(normalized);
        }

        String siteFamily = siteId == null ? "" : siteFamily(siteId);
        List<TemplateContract.TemplateManifest> exact = new ArrayList<TemplateContract.TemplateManifest>();
        List<TemplateContract.TemplateManifest> sameSiteScenario = new ArrayList<TemplateContract.TemplateManifest>();
        List<TemplateContract.TemplateManifest> sameSite = new ArrayList<TemplateContract.TemplateManifest>();
        List<TemplateContract.TemplateManifest> sameScenario = new ArrayList<TemplateContract.TemplateManifest>();
        List<TemplateContract.TemplateManifest> sameFingerprint = new ArrayList<TemplateContract.TemplateManifest>();

        for (TemplateContract.TemplateManifest manifest : active) {
            if (!requestUrlPatternHash.isEmpty()
                    && requestUrlPatternHash.equals(nullToEmpty(manifest.urlPatternHash))
                    && siteMatches(manifest.siteId, siteId)) {
                exact.add(manifest);
                continue;
            }
            if (siteMatches(manifest.siteId, siteId) && stringEquals(manifest.scenario, scenario)) {
                sameSiteScenario.add(manifest);
                continue;
            }
            if (!siteFamily.isEmpty() && siteMatches(manifest.siteId, siteId)) {
                sameSite.add(manifest);
                continue;
            }
            if (scenario != null && !scenario.trim().isEmpty() && stringEquals(manifest.scenario, scenario)) {
                sameScenario.add(manifest);
                continue;
            }
            if (fingerprint != null
                    && manifest.fingerprint != null
                    && stringEquals(manifest.fingerprint.domSignature, fingerprint.domSignature)) {
                sameFingerprint.add(manifest);
            }
        }

        if (!exact.isEmpty() && exact.size() <= EXACT_URL_MATCH_LIMIT) {
            return exact;
        }

        List<TemplateContract.TemplateManifest> recalled = new ArrayList<TemplateContract.TemplateManifest>();
        appendDistinct(recalled, exact);
        appendDistinct(recalled, sameSiteScenario);
        appendDistinct(recalled, sameSite);
        appendDistinct(recalled, sameScenario);
        appendDistinct(recalled, sameFingerprint);
        if (recalled.isEmpty()) {
            appendDistinct(recalled, active);
        }
        return recalled;
    }

    private void appendDistinct(
            List<TemplateContract.TemplateManifest> target,
            List<TemplateContract.TemplateManifest> source
    ) {
        Set<String> ids = target.stream()
                .map(manifest -> manifest.templateId)
                .collect(Collectors.toCollection(LinkedHashSet::new));
        for (TemplateContract.TemplateManifest manifest : source) {
            if (ids.add(manifest.templateId)) {
                target.add(manifest);
            }
        }
    }

    private double cheapScore(
            TemplateContract.TemplateManifest manifest,
            String siteId,
            String scenario,
            String requestUrlPatternHash,
            TemplateContract.PageFingerprint fingerprint
    ) {
        double fingerprintScore = 0.0d;
        if (manifest.fingerprint != null && fingerprint != null) {
            fingerprintScore = compareFingerprints(fingerprint, manifest.fingerprint);
        }
        double classificationAffinity = classificationAffinity(manifest, scenario);
        double siteAffinity = siteAffinity(manifest.siteId, siteId);
        double urlPatternAffinity = urlPatternAffinity(manifest, requestUrlPatternHash);
        double score = 0.42d * classificationAffinity
                + 0.28d * siteAffinity
                + 0.20d * urlPatternAffinity
                + 0.10d * fingerprintScore;
        if (manifest.extractionPlan != null) {
            score += 0.03d;
        }
        return score;
    }

    private double classificationAffinity(
            TemplateContract.TemplateManifest manifest,
            String scenario
    ) {
        if (scenario == null || scenario.trim().isEmpty()) {
            return 0.25d;
        }
        if (stringEquals(manifest.scenario, scenario)) {
            return 1.0d;
        }
        if ("unknown".equals(manifest.scenario) || "unknown".equals(scenario)) {
            return 0.4d;
        }
        return 0.1d;
    }

    public ManifestSelection findBestActiveManifest(
            Collection<TemplateContract.TemplateManifest> manifests,
            TemplateContract.ExtractionRequest request,
            TemplateContract.PageFingerprint fingerprint
    ) {
        String resolvedSiteId = resolveSiteId(request);
        String resolvedScenario = request == null ? null : request.scenario;
        String url = request == null ? null : request.url;
        return findBestActiveManifest(manifests, url, fingerprint, resolvedSiteId, resolvedScenario);
    }

    public List<TemplateContract.TemplateManifest> recallActiveManifests(
            Collection<TemplateContract.TemplateManifest> manifests,
            TemplateContract.ExtractionRequest request,
            TemplateContract.PageFingerprint fingerprint
    ) {
        String resolvedSiteId = resolveSiteId(request);
        String resolvedScenario = request == null ? null : request.scenario;
        String url = request == null ? null : request.url;
        String requestUrlPatternHash = buildUrlPatternHash(url);
        return recallCandidates(manifests, resolvedSiteId, resolvedScenario, requestUrlPatternHash, fingerprint);
    }

    public double cheapScoreManifest(
            TemplateContract.TemplateManifest manifest,
            TemplateContract.ExtractionRequest request,
            TemplateContract.PageFingerprint fingerprint
    ) {
        String resolvedSiteId = resolveSiteId(request);
        String resolvedScenario = request == null ? null : request.scenario;
        String url = request == null ? null : request.url;
        String requestUrlPatternHash = buildUrlPatternHash(url);
        return cheapScore(manifest, resolvedSiteId, resolvedScenario, requestUrlPatternHash, fingerprint);
    }

    public double siteAffinityValue(String left, String right) {
        return siteAffinity(left, right);
    }

    public double urlPatternAffinityForUrl(
            TemplateContract.TemplateManifest manifest,
            String url
    ) {
        return urlPatternAffinity(manifest, buildUrlPatternHash(url));
    }

    public TemplateContract.TemplateManifest normalizeManifest(TemplateContract.TemplateManifest manifest) {
        if (manifest.lifecycleStatus == null || manifest.lifecycleStatus.trim().isEmpty()) {
            manifest.lifecycleStatus = manifest.active ? "active" : "deprecated";
        }
        if ("active".equals(manifest.lifecycleStatus)) {
            manifest.active = true;
        } else if ("deprecated".equals(manifest.lifecycleStatus) || "archived".equals(manifest.lifecycleStatus)) {
            manifest.active = false;
        }
        if ((manifest.urlPatternHash == null || manifest.urlPatternHash.trim().isEmpty())
                && manifest.templateKey != null) {
            manifest.urlPatternHash = inferUrlPatternHashFromTemplateKey(manifest.templateKey);
        }
        return manifest;
    }

    public TemplateContract.PageFingerprint buildFingerprint(Document document) {
        TemplateContract.PageFingerprint fingerprint = new TemplateContract.PageFingerprint();

        List<String> nodes = new ArrayList<String>();
        int seen = 0;
        for (Element element : document.getAllElements()) {
            if (seen >= 300) {
                break;
            }
            StringBuilder builder = new StringBuilder();
            builder.append(element.tagName()).append("#");
            builder.append(element.id() == null ? "" : element.id());
            builder.append(".");
            if (!element.classNames().isEmpty()) {
                List<String> classes = new ArrayList<String>(element.classNames());
                Collections.sort(classes);
                int limit = Math.min(3, classes.size());
                builder.append(join(classes.subList(0, limit), "."));
            }
            nodes.add(builder.toString());
            seen++;
        }

        fingerprint.domSignature = sha256Hex(join(nodes, "|")).substring(0, 16);

        for (Element heading : document.select("h1, h2, h3")) {
            if (fingerprint.headings.size() >= 20) {
                break;
            }
            String text = DeclarativeTemplateEngine.normalizeText(heading.text());
            if (!text.isEmpty()) {
                fingerprint.headings.add(text);
            }
        }

        Set<String> ids = new LinkedHashSet<String>();
        Set<String> classes = new LinkedHashSet<String>();
        seen = 0;
        for (Element element : document.getAllElements()) {
            if (element.id() != null && !element.id().trim().isEmpty()) {
                ids.add(element.id());
            }
            if (seen < 300) {
                int count = 0;
                for (String className : element.classNames()) {
                    classes.add(className);
                    count++;
                    if (count >= 3) {
                        break;
                    }
                }
            }
            seen++;
        }

        fingerprint.keyIds.addAll(ids.stream().sorted().limit(20).collect(Collectors.toList()));
        fingerprint.keyClasses.addAll(classes.stream().sorted().limit(30).collect(Collectors.toList()));
        return fingerprint;
    }

    public double compareFingerprints(
            TemplateContract.PageFingerprint left,
            TemplateContract.PageFingerprint right
    ) {
        double score = 0.0d;
        if (left == null || right == null) {
            return score;
        }
        if (stringEquals(left.domSignature, right.domSignature)) {
            score += 0.55d;
        }
        score += 0.25d * jaccard(left.headings, right.headings);

        Set<String> leftKeys = new LinkedHashSet<String>();
        leftKeys.addAll(left.keyIds);
        leftKeys.addAll(left.keyClasses);
        Set<String> rightKeys = new LinkedHashSet<String>();
        rightKeys.addAll(right.keyIds);
        rightKeys.addAll(right.keyClasses);
        score += 0.20d * jaccard(leftKeys, rightKeys);

        return Math.round(score * 1000.0d) / 1000.0d;
    }

    private double jaccard(Collection<String> left, Collection<String> right) {
        Set<String> a = new LinkedHashSet<String>(left == null ? Collections.<String>emptyList() : left);
        Set<String> b = new LinkedHashSet<String>(right == null ? Collections.<String>emptyList() : right);
        if (a.isEmpty() && b.isEmpty()) {
            return 1.0d;
        }
        Set<String> union = new LinkedHashSet<String>(a);
        union.addAll(b);
        if (union.isEmpty()) {
            return 0.0d;
        }
        Set<String> intersection = new LinkedHashSet<String>(a);
        intersection.retainAll(b);
        return (double) intersection.size() / (double) union.size();
    }

    private static boolean stringEquals(String left, String right) {
        return String.valueOf(left).equals(String.valueOf(right));
    }

    private static boolean matchesScope(
            TemplateContract.TemplateManifest manifest,
            String siteId,
            String scenario
    ) {
        if (siteId != null && !siteId.trim().isEmpty()) {
            if (!siteMatches(manifest.siteId, siteId)) {
                return false;
            }
        }
        if (scenario != null && !scenario.trim().isEmpty()) {
            if (!stringEquals(manifest.scenario, scenario)) {
                return false;
            }
        }
        return true;
    }

    public String resolveSiteId(TemplateContract.ExtractionRequest request) {
        if (request == null) {
            return null;
        }
        if (request.siteId != null && !request.siteId.trim().isEmpty()) {
            return request.siteId.trim();
        }
        if (request.url == null || request.url.trim().isEmpty()) {
            return null;
        }
        try {
            java.net.URI uri = java.net.URI.create(request.url.trim());
            String host = uri.getHost();
            if (host == null || host.trim().isEmpty()) {
                return null;
            }
            return host.toLowerCase(Locale.ROOT);
        } catch (IllegalArgumentException ignored) {
            return null;
        }
    }

    public String buildUrlPatternHash(String url) {
        String normalized = normalizeUrlPattern(url);
        if (normalized.isEmpty()) {
            return "";
        }
        return sha256Hex(normalized).substring(0, 8);
    }

    public String normalizeUrlPattern(String url) {
        if (url == null || url.trim().isEmpty()) {
            return "";
        }
        try {
            java.net.URI uri = java.net.URI.create(url.trim());
            String host = uri.getHost();
            if (host == null || host.trim().isEmpty()) {
                return "";
            }
            host = host.toLowerCase(Locale.ROOT);
            String path = uri.getPath() == null || uri.getPath().isEmpty() ? "/" : uri.getPath();
            String[] segments = path.split("/");
            List<String> normalizedSegments = new ArrayList<String>();
            for (String segment : segments) {
                if (segment == null || segment.isEmpty()) {
                    continue;
                }
                if (segment.matches("\\d+")) {
                    normalizedSegments.add("{int}");
                } else if (segment.matches("[0-9a-fA-F]{8,}")) {
                    normalizedSegments.add("{hex}");
                } else {
                    normalizedSegments.add(segment.toLowerCase(Locale.ROOT).replaceAll("\\d+", "{n}"));
                }
            }
            String normalizedPath = "/" + join(normalizedSegments, "/");
            return host + "|" + normalizedPath;
        } catch (IllegalArgumentException ignored) {
            return "";
        }
    }

    private List<TemplateContract.TemplateManifest> prioritizeByUrlPattern(
            List<TemplateContract.TemplateManifest> manifests,
            String requestUrlPatternHash
    ) {
        if (requestUrlPatternHash == null || requestUrlPatternHash.isEmpty()) {
            return manifests;
        }
        List<TemplateContract.TemplateManifest> exact = new ArrayList<TemplateContract.TemplateManifest>();
        List<TemplateContract.TemplateManifest> others = new ArrayList<TemplateContract.TemplateManifest>();
        for (TemplateContract.TemplateManifest manifest : manifests) {
            if (requestUrlPatternHash.equals(manifest.urlPatternHash)) {
                exact.add(manifest);
            } else {
                others.add(manifest);
            }
        }
        exact.addAll(others);
        return exact;
    }

    private double urlPatternAffinity(TemplateContract.TemplateManifest manifest, String requestUrlPatternHash) {
        if (manifest == null || manifest.urlPatternHash == null || manifest.urlPatternHash.isEmpty()) {
            return 0.0d;
        }
        if (requestUrlPatternHash == null || requestUrlPatternHash.isEmpty()) {
            return 0.0d;
        }
        return requestUrlPatternHash.equals(manifest.urlPatternHash) ? 1.0d : 0.0d;
    }

    private static String nullToEmpty(String value) {
        return value == null ? "" : value;
    }

    private static boolean siteMatches(String left, String right) {
        if (left == null || right == null) {
            return false;
        }
        if (left.equalsIgnoreCase(right)) {
            return true;
        }
        return siteFamily(left).equals(siteFamily(right));
    }

    private static double siteAffinity(String left, String right) {
        if (left == null || right == null) {
            return 0.0d;
        }
        if (left.equalsIgnoreCase(right)) {
            return 1.0d;
        }
        return siteFamily(left).equals(siteFamily(right)) ? 0.85d : 0.0d;
    }

    private static String siteFamily(String siteId) {
        if (siteId == null || siteId.trim().isEmpty()) {
            return "";
        }
        String host = siteId.trim().toLowerCase(Locale.ROOT);
        if (host.startsWith("www.")) {
            host = host.substring(4);
        }
        String[] parts = host.split("\\.");
        if (parts.length <= 2) {
            return host;
        }
        String last = parts[parts.length - 1];
        String secondLast = parts[parts.length - 2];
        if (last.length() == 2 && secondLast.length() <= 3 && parts.length >= 3) {
            return parts[parts.length - 3] + "." + secondLast + "." + last;
        }
        return secondLast + "." + last;
    }

    private String inferUrlPatternHashFromTemplateKey(String templateKey) {
        if (templateKey == null || templateKey.trim().isEmpty()) {
            return "";
        }
        Matcher matcher = Pattern.compile("_([0-9a-f]{8})(?:_[0-9a-f]{12})?$").matcher(templateKey);
        if (!matcher.find()) {
            return "";
        }
        return matcher.group(1);
    }

    private static String sha256Hex(String value) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] bytes = digest.digest(value.getBytes(StandardCharsets.UTF_8));
            StringBuilder builder = new StringBuilder();
            for (byte b : bytes) {
                builder.append(String.format(Locale.ROOT, "%02x", b));
            }
            return builder.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException("SHA-256 unavailable", e);
        }
    }

    private static String join(List<String> parts, String separator) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.size(); i++) {
            if (i > 0) {
                builder.append(separator);
            }
            builder.append(parts.get(i));
        }
        return builder.toString();
    }

    public static class ManifestSelection {
        public final TemplateContract.TemplateManifest manifest;
        public final double score;
        public final TemplateContract.PageFingerprint fingerprint;

        public ManifestSelection(
                TemplateContract.TemplateManifest manifest,
                double score,
                TemplateContract.PageFingerprint fingerprint
        ) {
            this.manifest = manifest;
            this.score = score;
            this.fingerprint = fingerprint;
        }
    }

    private static class ScoredManifest {
        private final TemplateContract.TemplateManifest manifest;
        private final double score;

        private ScoredManifest(TemplateContract.TemplateManifest manifest, double score) {
            this.manifest = manifest;
            this.score = score;
        }
    }
}
