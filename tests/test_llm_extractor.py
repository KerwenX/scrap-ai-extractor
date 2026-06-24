from hybrid_extractor.extractors.llm import ScrapeGraphFallbackExtractor


def test_requests_url_normalization_appends_chat_completions_for_v1_root():
    extractor = ScrapeGraphFallbackExtractor()

    assert (
        extractor._normalize_requests_url("http://7.242.106.7:30928/v1/chat/completions")
        == "http://7.242.106.7:30928/v1/chat/completions"
    )
    assert (
        extractor._normalize_requests_url("https://api.example.com/v1/")
        == "https://api.example.com/v1/chat/completions"
    )


def test_normalize_result_decodes_json_markdown_fence():
    extractor = ScrapeGraphFallbackExtractor()

    result = extractor._normalize_result(
        """```json
{"标题":"测试标题","摘要":"测试摘要"}
```"""
    )

    assert result == {"标题": "测试标题", "摘要": "测试摘要"}


def test_streaming_reader_concatenates_content_chunks_only():
    extractor = ScrapeGraphFallbackExtractor()

    class Delta:
        def __init__(self, content=None, reasoning_content=None):
            self.content = content
            self.reasoning_content = reasoning_content

    class Choice:
        def __init__(self, delta):
            self.delta = delta

    class Chunk:
        def __init__(self, delta):
            self.choices = [Choice(delta)]

    stream = [
        Chunk(Delta(reasoning_content="thinking")),
        Chunk(Delta(content="{")),
        Chunk(Delta(content='"标题":"测试"')),
        Chunk(Delta(content="}")),
    ]

    assert extractor._read_streaming_content(stream) == '{"标题":"测试"}'


def test_sse_streaming_reader_concatenates_data_lines_only():
    extractor = ScrapeGraphFallbackExtractor()

    lines = [
        'data: {"choices":[{"delta":{"content":"{"}}]}'.encode("utf-8"),
        'data: {"choices":[{"delta":{"content":"\\"标题\\":\\"测试\\""}}]}'.encode("utf-8"),
        'data: {"choices":[{"delta":{"content":"}"}}]}'.encode("utf-8"),
        b"data: [DONE]",
    ]

    assert extractor._read_sse_streaming_content(lines) == '{"标题":"测试"}'


def test_extract_json_response_content_reads_standard_payload():
    extractor = ScrapeGraphFallbackExtractor()

    class FakeResponse:
        def json(self):
            return {"choices": [{"message": {"content": "{\"标题\":\"测试\"}"}}]}

    assert extractor._extract_json_response_content(FakeResponse()) == '{"标题":"测试"}'
