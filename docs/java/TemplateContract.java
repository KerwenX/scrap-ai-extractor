import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class TemplateContract {
    private TemplateContract() {
    }

    public static class PageFingerprint {
        public String domSignature;
        public List<String> headings = new ArrayList<String>();
        public List<String> keyIds = new ArrayList<String>();
        public List<String> keyClasses = new ArrayList<String>();
    }

    public static class PostProcessStep {
        public String op;
        public Map<String, Object> args = new LinkedHashMap<String, Object>();
    }

    public static class FieldSelectorRule {
        public String kind;
        public String value;
        public String attr = "text";
        public boolean many = false;
    }

    public static class FieldRule {
        public String fieldName;
        public List<FieldSelectorRule> selectors = new ArrayList<FieldSelectorRule>();
        public List<PostProcessStep> postprocess = new ArrayList<PostProcessStep>();
        public Object fallbackValue;
    }

    public static class ExtractionPlan {
        public String mode = "declarative";
        public List<FieldRule> fields = new ArrayList<FieldRule>();
        public String codeEntrypoint = "";
    }

    public static class TemplateManifest {
        public String templateId;
        public String parserKey;
        public String siteId;
        public String siteName;
        public String pageType;
        public String scenario;
        public String version = "v1";
        public String templateKey = "";
        public String lifecycleStatus = "active";
        public boolean active = true;
        public PageFingerprint fingerprint;
        public List<String> requiredFields = new ArrayList<String>();
        public ExtractionPlan extractionPlan;
        public String notes = "";
        public String sourceCandidateId;
    }

    public static class ExtractionRequest {
        public String url;
        public String html;
        public String siteId;
        public String scenario;
        public String preferredTemplateId;
    }

    public static class FieldEvidence {
        public String fieldName;
        public String source;
        public String ruleId;

        public FieldEvidence() {
        }

        public FieldEvidence(String fieldName, String source, String ruleId) {
            this.fieldName = fieldName;
            this.source = source;
            this.ruleId = ruleId;
        }
    }

    public static class ExtractionResult {
        public Map<String, Object> data = new LinkedHashMap<String, Object>();
        public List<FieldEvidence> evidences = new ArrayList<FieldEvidence>();
    }

    public static class ExtractionExecutionResult {
        public ExtractionRequest request;
        public TemplateManifest matchedManifest;
        public PageFingerprint fingerprint;
        public Double matchScore;
        public ExtractionResult extractionResult = new ExtractionResult();
    }
}
