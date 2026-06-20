from hybrid_extractor.models import ExtractionPlan, FieldRule, FieldSelectorRule, PostProcessStep
from hybrid_extractor.preprocessing import build_soup
from hybrid_extractor.rule_runtime import RuleRuntime


def test_rule_runtime_executes_declarative_selectors():
    html = """
    <html>
      <head><title>Example</title><meta name="description" content="A summary."></head>
      <body>
        <h1>Example Name</h1>
        <div id="aliases">Alias A，Alias B</div>
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
                postprocess=[
                    PostProcessStep(op="regex_replace", args={"pattern": "，", "repl": "、"}),
                    PostProcessStep(op="split_cn_list"),
                    PostProcessStep(op="unique"),
                ],
            ),
        ],
    )
    result = RuleRuntime().execute(build_soup(html), plan)
    assert result.data["name"] == "Example Name"
    assert result.data["summary"] == "A summary."
    assert result.data["aliases"] == ["Alias A", "Alias B"]


def test_rule_runtime_supports_extended_postprocess_ops():
    html = """
    <html>
      <body>
        <div id="price"> Price: 1,234.50 USD </div>
        <div id="tags">Tag A； Tag B； Tag A</div>
      </body>
    </html>
    """
    plan = ExtractionPlan(
        mode="declarative",
        fields=[
            FieldRule(
                field_name="price_value",
                selectors=[FieldSelectorRule(kind="id", value="price")],
                postprocess=[
                    PostProcessStep(op="normalize_whitespace"),
                    PostProcessStep(op="regex_extract", args={"pattern": r"(\d[\d,]*\.\d+)"}),
                    PostProcessStep(op="to_float"),
                ],
            ),
            FieldRule(
                field_name="tags",
                selectors=[FieldSelectorRule(kind="id", value="tags")],
                postprocess=[
                    PostProcessStep(op="regex_replace", args={"pattern": r"[；;]+", "repl": "、"}),
                    PostProcessStep(op="split_cn_list"),
                    PostProcessStep(op="filter_empty"),
                    PostProcessStep(op="unique"),
                ],
            ),
            FieldRule(
                field_name="summary",
                fallback_value="\n\nFirst useful line\nSecond useful line",
                postprocess=[PostProcessStep(op="first_non_empty_line")],
            ),
            FieldRule(
                field_name="tag_line",
                fallback_value=["Tag A", "", "Tag B"],
                postprocess=[
                    PostProcessStep(op="filter_empty"),
                    PostProcessStep(op="join", args={"separator": " / "}),
                ],
            ),
        ],
    )
    result = RuleRuntime().execute(build_soup(html), plan)
    assert result.data["price_value"] == 1234.50
    assert result.data["tags"] == ["Tag A", "Tag B"]
    assert result.data["summary"] == "First useful line"
    assert result.data["tag_line"] == "Tag A / Tag B"


def test_rule_runtime_supports_label_value_selector():
    html = """
    <html>
      <body>
        <table class="info-table">
          <tr><td>作者</td><td>张三</td></tr>
          <tr><td>期刊</td><td>经济研究</td></tr>
        </table>
      </body>
    </html>
    """
    plan = ExtractionPlan(
        mode="declarative",
        fields=[
            FieldRule(
                field_name="作者",
                selectors=[FieldSelectorRule(kind="label_value", value="作者")],
            ),
            FieldRule(
                field_name="期刊",
                selectors=[FieldSelectorRule(kind="label_value", value="期刊")],
            ),
        ],
    )
    result = RuleRuntime().execute(build_soup(html), plan)
    assert result.data["作者"] == "张三"
    assert result.data["期刊"] == "经济研究"
