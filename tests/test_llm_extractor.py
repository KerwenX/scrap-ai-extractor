from hybrid_extractor.extractors.llm import ScrapeGraphFallbackExtractor


def test_openai_base_url_normalization_removes_chat_completions_suffix():
    extractor = ScrapeGraphFallbackExtractor()

    assert (
        extractor._normalize_openai_base_url("http://7.242.106.7:30928/v1/chat/completions")
        == "http://7.242.106.7:30928/v1"
    )
    assert (
        extractor._normalize_openai_base_url("https://api.example.com/chat/completions/")
        == "https://api.example.com"
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
