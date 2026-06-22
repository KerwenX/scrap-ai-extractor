import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class DeclarativeTemplateEngine {
    @FunctionalInterface
    public interface SelectorCodeHandler {
        Object handle(
                Document document,
                TemplateContract.FieldRule fieldRule,
                TemplateContract.FieldSelectorRule selectorRule
        );
    }

    private final Map<String, SelectorCodeHandler> codeHandlers =
            new LinkedHashMap<String, SelectorCodeHandler>();

    public DeclarativeTemplateEngine registerCodeHandler(String name, SelectorCodeHandler handler) {
        codeHandlers.put(name, handler);
        return this;
    }

    public TemplateContract.ExtractionResult execute(
            Document document,
            TemplateContract.ExtractionPlan plan
    ) {
        TemplateContract.ExtractionResult result = new TemplateContract.ExtractionResult();
        if (plan == null || plan.fields == null) {
            return result;
        }

        for (TemplateContract.FieldRule fieldRule : plan.fields) {
            Object value = null;
            String source = "";
            String ruleId = null;

            if (fieldRule.selectors != null) {
                for (TemplateContract.FieldSelectorRule selector : fieldRule.selectors) {
                    value = resolveSelector(document, fieldRule, selector);
                    if (hasValue(value)) {
                        source = selector.kind + ":" + selector.value;
                        ruleId = fieldRule.fieldName + ":" + selector.kind;
                        break;
                    }
                }
            }

            if (!hasValue(value)) {
                value = fieldRule.fallbackValue;
            }

            value = applyPostprocess(value, fieldRule);
            result.data.put(fieldRule.fieldName, value);
            if (fieldRule.mergeOutput && value instanceof Map<?, ?>) {
                mergeOutput(result.data, (Map<?, ?>) value);
            }
            if (hasValue(value)) {
                result.evidences.add(new TemplateContract.FieldEvidence(fieldRule.fieldName, source, ruleId));
            }
        }

        return result;
    }

    private Object resolveSelector(
            Document document,
            TemplateContract.FieldRule fieldRule,
            TemplateContract.FieldSelectorRule selector
    ) {
        if (selector == null || selector.kind == null) {
            return null;
        }

        switch (selector.kind) {
            case "css":
                return extractNodes(document.select(selector.value), selector.attr, selector.many);
            case "id":
                Element byId = document.getElementById(selector.value);
                if (byId == null) {
                    return null;
                }
                return extractNodes(new Elements(byId), selector.attr, selector.many);
            case "meta":
                if ("description".equals(selector.value)) {
                    return extractPageDescription(document);
                }
                Element meta = document.selectFirst("meta[name=" + selector.value + "]");
                return meta == null ? null : normalizeText(meta.attr("content"));
            case "text_pattern":
                return extractByTextPattern(document, selector.value);
            case "section_tab":
                return buildSectionTabMap(document).get(selector.value);
            case "label_value":
                return extractLabelValue(document, selector.value, selector.many);
            case "all_label_values":
                return extractAllLabelValues(document);
            case "all_sections":
                return extractAllSections(document);
            case "code":
                SelectorCodeHandler handler = codeHandlers.get(selector.value);
                if (handler == null) {
                    return null;
                }
                return handler.handle(document, fieldRule, selector);
            default:
                return null;
        }
    }

    private Object extractByTextPattern(Document document, String patternText) {
        String text = normalizeText(document.text());
        Matcher matcher = Pattern.compile(patternText).matcher(text);
        if (!matcher.find()) {
            return null;
        }
        if (matcher.groupCount() >= 1) {
            return matcher.group(1);
        }
        return matcher.group(0);
    }

    private Map<String, String> buildSectionTabMap(Document document) {
        List<String> tabs = new ArrayList<String>();
        for (Element element : document.select(".van-tabs__nav [role='tab'] .van-tab__text")) {
            String text = normalizeText(element.text());
            if (!text.isEmpty()) {
                tabs.add(text);
            }
        }

        Elements panes = document.select(".van-tab__pane-wrapper .van-tab__pane");
        Map<String, String> result = new LinkedHashMap<String, String>();
        int count = Math.min(tabs.size(), panes.size());
        for (int i = 0; i < count; i++) {
            result.put(tabs.get(i), normalizeText(panes.get(i).text()));
        }
        return result;
    }

    private Object extractNodes(Elements nodes, String attr, boolean many) {
        List<String> values = new ArrayList<String>();
        for (Element node : nodes) {
            String value;
            if (attr == null || attr.isEmpty() || "text".equals(attr)) {
                value = normalizeText(node.text());
            } else {
                value = normalizeText(node.attr(attr));
            }
            if (!value.isEmpty()) {
                values.add(value);
            }
        }
        if (many) {
            return values;
        }
        return values.isEmpty() ? null : values.get(0);
    }

    private Object extractLabelValue(Document document, String label, boolean many) {
        String normalizedLabel = normalizeText(label);
        if (normalizedLabel.isEmpty()) {
            return null;
        }

        List<String> values = new ArrayList<String>();
        Map<String, String> mappings = extractAllLabelValues(document);
        for (Map.Entry<String, String> entry : mappings.entrySet()) {
            if (normalizeText(entry.getKey()).replace(" ", "").equals(normalizedLabel.replace(" ", ""))) {
                values.add(entry.getValue());
            }
        }

        if (many) {
            return values;
        }
        return values.isEmpty() ? null : values.get(0);
    }

    private Map<String, String> extractAllLabelValues(Document document) {
        Map<String, String> result = new LinkedHashMap<String, String>();

        for (Element container : document.select(".item-container")) {
            Element titleNode = container.selectFirst(".item-title-container");
            Element valueNode = container.selectFirst(".item-content");
            if (titleNode == null || valueNode == null) {
                continue;
            }
            String title = normalizeText(titleNode.text()).replace(" ", "");
            String value = normalizeText(valueNode.text());
            if (!title.isEmpty() && !value.isEmpty() && !result.containsKey(title)) {
                result.put(title, value);
            }
        }

        for (Element row : document.select("tr")) {
            Elements cells = row.select("> th, > td");
            if (cells.size() < 2) {
                continue;
            }
            String label = normalizeText(cells.get(0).text()).replaceAll("[:：]+$", "");
            String value = normalizeText(cells.get(1).text());
            if (!label.isEmpty() && !value.isEmpty() && !result.containsKey(label)) {
                result.put(label, value);
            }
        }

        for (Element dl : document.select("dl")) {
            Elements terms = dl.select("> dt");
            Elements descriptions = dl.select("> dd");
            int count = Math.min(terms.size(), descriptions.size());
            for (int i = 0; i < count; i++) {
                String label = normalizeText(terms.get(i).text()).replaceAll("[:：]+$", "");
                String value = normalizeText(descriptions.get(i).text());
                if (!label.isEmpty() && !value.isEmpty() && !result.containsKey(label)) {
                    result.put(label, value);
                }
            }
        }

        return result;
    }

    private Map<String, String> extractAllSections(Document document) {
        Map<String, String> result = new LinkedHashMap<String, String>();
        for (Element container : document.select(".public-container")) {
            String title = extractContainerTitle(container);
            String content = extractContainerContent(container);
            if (!title.isEmpty() && !content.isEmpty() && !result.containsKey(title)) {
                result.put(title, content);
            }
        }

        if (!result.isEmpty()) {
            return result;
        }

        for (Element container : document.select("section, article, .section, .content-section")) {
            String title = extractContainerTitle(container);
            String content = extractContainerContent(container);
            if (!title.isEmpty() && !content.isEmpty() && !result.containsKey(title)) {
                result.put(title, content);
            }
        }
        return result;
    }

    private Object applyPostprocess(Object value, TemplateContract.FieldRule fieldRule) {
        Object current = value;
        if (fieldRule.postprocess == null) {
            return current;
        }
        for (TemplateContract.PostProcessStep step : fieldRule.postprocess) {
            current = applyStep(current, step);
        }
        return current;
    }

    private String extractContainerTitle(Element node) {
        Element titleNode = node.selectFirst("h2, h3, h4, .section-title, .title, .item-title, .title-line p, .title p");
        return titleNode == null ? "" : normalizeText(titleNode.text());
    }

    private String extractContainerContent(Element node) {
        Element contentNode = node.selectFirst(".item-content, .content, .section-content");
        Element target = contentNode == null ? node : contentNode;
        return normalizeText(target.text());
    }

    private Object applyStep(Object value, TemplateContract.PostProcessStep step) {
        if (value == null || step == null || step.op == null) {
            return value;
        }

        switch (step.op) {
            case "strip":
                return mapStringOrList(value, new StringMapper() {
                    public String map(String input) {
                        return input.trim();
                    }
                });
            case "strip_cn_punctuation":
                return mapStringOrList(value, new StringMapper() {
                    public String map(String input) {
                        return input.replaceAll("^[，。；：: ]+|[，。；：: ]+$", "");
                    }
                });
            case "split_cn_list":
                if (value instanceof String) {
                    String normalized = ((String) value)
                            .replace("、", "，")
                            .replace("以及", "，")
                            .replace("及", "，")
                            .replace("等", "");
                    List<String> result = new ArrayList<String>();
                    for (String part : normalized.split("，")) {
                        String trimmed = part.replaceAll("^[，。 ]+|[，。 ]+$", "").trim();
                        if (!trimmed.isEmpty()) {
                            result.add(trimmed);
                        }
                    }
                    return result;
                }
                return value;
            case "unique":
                if (value instanceof List<?>) {
                    List<?> list = (List<?>) value;
                    Set<String> seen = new LinkedHashSet<String>();
                    List<Object> result = new ArrayList<Object>();
                    for (Object item : list) {
                        String key = String.valueOf(item);
                        if (seen.add(key)) {
                            result.add(item);
                        }
                    }
                    return result;
                }
                return value;
            case "first_non_empty_line":
                if (value instanceof String) {
                    for (String line : ((String) value).split("\\r?\\n")) {
                        String normalizedLine = normalizeText(line);
                        if (!normalizedLine.isEmpty()) {
                            return normalizedLine;
                        }
                    }
                    return "";
                }
                return value;
            case "regex_extract":
                if (value instanceof String) {
                    String pattern = stringArg(step.args, "pattern", "");
                    int group = intArg(step.args, "group", 1);
                    if (pattern.isEmpty()) {
                        return value;
                    }
                    Matcher matcher = Pattern.compile(pattern).matcher((String) value);
                    if (!matcher.find()) {
                        return null;
                    }
                    if (matcher.groupCount() >= group) {
                        return matcher.group(group);
                    }
                    return matcher.group(0);
                }
                return value;
            case "regex_replace":
                final String pattern = stringArg(step.args, "pattern", "");
                final String repl = stringArg(step.args, "repl", "");
                if (pattern.isEmpty()) {
                    return value;
                }
                return mapStringOrList(value, new StringMapper() {
                    public String map(String input) {
                        return input.replaceAll(pattern, repl);
                    }
                });
            case "join":
                if (value instanceof List<?>) {
                    String separator = stringArg(step.args, "separator", ", ");
                    List<?> list = (List<?>) value;
                    List<String> parts = new ArrayList<String>();
                    for (Object item : list) {
                        if (hasValue(item)) {
                            parts.add(String.valueOf(item));
                        }
                    }
                    return join(parts, separator);
                }
                return value;
            case "filter_empty":
                if (value instanceof List<?>) {
                    List<?> list = (List<?>) value;
                    List<Object> result = new ArrayList<Object>();
                    for (Object item : list) {
                        if (hasValue(item)) {
                            result.add(item);
                        }
                    }
                    return result;
                }
                return value;
            case "normalize_whitespace":
                return mapStringOrList(value, new StringMapper() {
                    public String map(String input) {
                        return normalizeText(input);
                    }
                });
            case "to_int":
                return toInt(value);
            case "to_float":
                return toFloat(value);
            default:
                return value;
        }
    }

    private Object mapStringOrList(Object value, StringMapper mapper) {
        if (value instanceof String) {
            return mapper.map((String) value);
        }
        if (value instanceof List<?>) {
            List<?> list = (List<?>) value;
            List<Object> result = new ArrayList<Object>();
            for (Object item : list) {
                result.add(item instanceof String ? mapper.map((String) item) : item);
            }
            return result;
        }
        return value;
    }

    private Integer toInt(Object value) {
        if (value instanceof Number) {
            return Integer.valueOf(((Number) value).intValue());
        }
        if (value instanceof String) {
            Matcher matcher = Pattern.compile("-?\\d+").matcher(((String) value).replace(",", ""));
            if (matcher.find()) {
                return Integer.valueOf(Integer.parseInt(matcher.group(0)));
            }
        }
        return null;
    }

    private Double toFloat(Object value) {
        if (value instanceof Number) {
            return Double.valueOf(((Number) value).doubleValue());
        }
        if (value instanceof String) {
            Matcher matcher = Pattern.compile("-?\\d+(?:\\.\\d+)?").matcher(((String) value).replace(",", ""));
            if (matcher.find()) {
                return Double.valueOf(Double.parseDouble(matcher.group(0)));
            }
        }
        return null;
    }

    private String extractPageDescription(Document document) {
        Element meta = document.selectFirst("meta[name=description]");
        if (meta != null) {
            return normalizeText(meta.attr("content"));
        }
        return "";
    }

    private static String stringArg(Map<String, Object> args, String key, String defaultValue) {
        if (args == null) {
            return defaultValue;
        }
        Object value = args.get(key);
        return value == null ? defaultValue : String.valueOf(value);
    }

    private static int intArg(Map<String, Object> args, String key, int defaultValue) {
        if (args == null) {
            return defaultValue;
        }
        Object value = args.get(key);
        if (value instanceof Number) {
            return ((Number) value).intValue();
        }
        if (value instanceof String) {
            try {
                return Integer.parseInt((String) value);
            } catch (NumberFormatException ignored) {
                return defaultValue;
            }
        }
        return defaultValue;
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

    private void mergeOutput(Map<String, Object> data, Map<?, ?> mapping) {
        for (Map.Entry<?, ?> entry : mapping.entrySet()) {
            if (entry.getKey() == null) {
                continue;
            }
            String key = String.valueOf(entry.getKey());
            Object value = entry.getValue();
            if (key.trim().isEmpty() || !hasValue(value) || hasValue(data.get(key))) {
                continue;
            }
            data.put(key, value);
        }
    }

    public static boolean hasValue(Object value) {
        if (value == null) {
            return false;
        }
        if (value instanceof String) {
            return !((String) value).trim().isEmpty();
        }
        if (value instanceof List<?>) {
            return !((List<?>) value).isEmpty();
        }
        if (value instanceof Map<?, ?>) {
            return !((Map<?, ?>) value).isEmpty();
        }
        return true;
    }

    public static String normalizeText(String value) {
        if (value == null) {
            return "";
        }
        return value.replace('\u00A0', ' ').replaceAll("\\s+", " ").trim();
    }

    private interface StringMapper {
        String map(String input);
    }
}
