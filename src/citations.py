"""Turn retrieved chunks into cited context.

Kept free of API keys and network calls so the citation logic can be unit
tested without an embeddings backend. Works on anything with `.page_content`
and `.metadata` (a LangChain Document, or a stub in a test).
"""


def source_label(metadata):
    """A human-readable label for a chunk's origin: 'Title (url)' or just the url."""
    url = (metadata or {}).get("source") or "unknown source"
    title = (metadata or {}).get("title")
    return f"{title} ({url})" if title else url


def format_docs_with_sources(docs):
    """Prefix each chunk with its source and collect the unique sources.

    Returns (context, sources):
      - context: the chunks joined for the model, each tagged with [Source: ...]
        so it can cite inline.
      - sources: ordered, de-duplicated (label, url) pairs for a Sources footer.
    """
    blocks = []
    sources = []
    seen = set()
    for doc in docs:
        url = (doc.metadata or {}).get("source") or "unknown source"
        label = source_label(doc.metadata)
        if url not in seen:
            seen.add(url)
            sources.append((label, url))
        blocks.append(f"[Source: {label}]\n{doc.page_content}")
    return "\n\n".join(blocks), sources


def render_sources(sources):
    """Format collected sources as a numbered 'Sources' block, or '' if none."""
    if not sources:
        return ""
    lines = ["Sources:"]
    for i, (label, _url) in enumerate(sources, 1):
        lines.append(f"  [{i}] {label}")
    return "\n".join(lines)
