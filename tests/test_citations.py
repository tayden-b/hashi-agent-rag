import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from citations import format_docs_with_sources, render_sources, source_label


class FakeDoc:
    """Stand-in for a LangChain Document so these tests need no embeddings."""

    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata


def test_source_label_prefers_title():
    assert source_label({"source": "https://x/a", "title": "Arch"}) == "Arch (https://x/a)"
    assert source_label({"source": "https://x/a"}) == "https://x/a"
    assert source_label({}) == "unknown source"


def test_context_tags_each_chunk_with_its_source():
    docs = [
        FakeDoc("chunk one", {"source": "https://x/a", "title": "A"}),
        FakeDoc("chunk two", {"source": "https://x/b"}),
    ]
    context, _ = format_docs_with_sources(docs)
    assert "[Source: A (https://x/a)]\nchunk one" in context
    assert "[Source: https://x/b]\nchunk two" in context


def test_sources_are_deduped_by_url_in_order():
    docs = [
        FakeDoc("a1", {"source": "https://x/a", "title": "A"}),
        FakeDoc("a2", {"source": "https://x/a", "title": "A"}),  # same url
        FakeDoc("c1", {"source": "https://x/c"}),
    ]
    _, sources = format_docs_with_sources(docs)
    assert [url for _, url in sources] == ["https://x/a", "https://x/c"]


def test_render_sources_numbers_them_and_handles_empty():
    assert render_sources([]) == ""
    out = render_sources([("A (https://x/a)", "https://x/a"), ("https://x/c", "https://x/c")])
    assert out.splitlines() == [
        "Sources:",
        "  [1] A (https://x/a)",
        "  [2] https://x/c",
    ]
