from hybrid_extractor.models import ExtractionPlan, FieldRule, FieldSelectorRule, PostProcessStep
from hybrid_extractor.preprocessing import build_soup
from hybrid_extractor.rule_runtime import RuleRuntime


def test_rule_runtime_executes_declarative_selectors():
    html = """
    <html>
      <head><title>Example</title><meta name="description" content="A summary."></head>
      <body>
        <h1>Example Name</h1>
        <div id="aliases">别名A、别名B</div>
      </body>
    </html>
    """
    plan = ExtractionPlan(
        mode="declarative",
        fields=[
            FieldRule(
                field_name="name",
                selectors=[FieldSelectorRule(kind="css", value="h1")],
                postprocess=[PostProcessStep(op="strip")],
            ),
            FieldRule(
                field_name="summary",
                selectors=[FieldSelectorRule(kind="meta", value="description")],
            ),
            FieldRule(
                field_name="aliases",
                selectors=[FieldSelectorRule(kind="id", value="aliases")],
                postprocess=[PostProcessStep(op="split_cn_list"), PostProcessStep(op="unique")],
            ),
        ],
    )
    result = RuleRuntime().execute(build_soup(html), plan)
    assert result.data["name"] == "Example Name"
    assert result.data["summary"] == "A summary."
    assert result.data["aliases"] == ["别名A", "别名B"]
