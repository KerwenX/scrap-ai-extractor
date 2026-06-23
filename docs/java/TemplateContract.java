import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class TemplateContract {
    private TemplateContract() {
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class PageFingerprint {
        @JsonProperty("dom_signature")
        public String domSignature;
        public List<String> headings = new ArrayList<String>();
        @JsonProperty("key_ids")
        public List<String> keyIds = new ArrayList<String>();
        @JsonProperty("key_classes")
        public List<String> keyClasses = new ArrayList<String>();
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class PostProcessStep {
        public String op;
        public Map<String, Object> args = new LinkedHashMap<String, Object>();
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class FieldSelectorRule {
        public String kind;
        public String value;
        public String attr = "text";
        public boolean many = false;
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class FieldRule {
        @JsonProperty("field_name")
        public String fieldName;
        public List<FieldSelectorRule> selectors = new ArrayList<FieldSelectorRule>();
        public List<PostProcessStep> postprocess = new ArrayList<PostProcessStep>();
        @JsonProperty("fallback_value")
        public Object fallbackValue;
        @JsonProperty("merge_output")
        public boolean mergeOutput = false;
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class ExtractionPlan {
        public String mode = "declarative";
        public List<FieldRule> fields = new ArrayList<FieldRule>();
        @JsonProperty("code_entrypoint")
        public String codeEntrypoint = "";
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class TemplateManifest {
        @JsonProperty("template_id")
        public String templateId;
        @JsonProperty("parser_key")
        public String parserKey;
        @JsonProperty("site_id")
        public String siteId;
        @JsonProperty("site_name")
        public String siteName;
        @JsonProperty("page_type")
        public String pageType;
        public String scenario;
        public String version = "v1";
        @JsonProperty("template_key")
        public String templateKey = "";
        @JsonProperty("url_pattern")
        public String urlPattern = "";
        @JsonProperty("url_pattern_hash")
        public String urlPatternHash = "";
        @JsonProperty("lifecycle_status")
        public String lifecycleStatus = "active";
        public boolean active = true;
        public PageFingerprint fingerprint;
        @JsonProperty("required_fields")
        public List<String> requiredFields = new ArrayList<String>();
        @JsonProperty("extraction_plan")
        public ExtractionPlan extractionPlan;
        public String notes = "";
        @JsonProperty("source_candidate_id")
        public String sourceCandidateId;
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class ExtractionRequest {
        public String url;
        public String html;
        @JsonProperty("site_id")
        public String siteId;
        public String scenario;
        @JsonProperty("preferred_template_id")
        public String preferredTemplateId;
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class FieldEvidence {
        @JsonProperty("field_name")
        public String fieldName;
        public String source;
        @JsonProperty("rule_id")
        public String ruleId;

        public FieldEvidence() {
        }

        public FieldEvidence(String fieldName, String source, String ruleId) {
            this.fieldName = fieldName;
            this.source = source;
            this.ruleId = ruleId;
        }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class ExtractionResult {
        public Map<String, Object> data = new LinkedHashMap<String, Object>();
        public List<FieldEvidence> evidences = new ArrayList<FieldEvidence>();
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class ExtractionExecutionResult {
        public ExtractionRequest request;
        @JsonProperty("matched_manifest")
        public TemplateManifest matchedManifest;
        public PageFingerprint fingerprint;
        @JsonProperty("match_score")
        public Double matchScore;
        @JsonProperty("extraction_result")
        public ExtractionResult extractionResult = new ExtractionResult();
    }
}
