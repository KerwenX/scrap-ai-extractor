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
