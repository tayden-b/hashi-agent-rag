"""Scoring helpers for the eval harness.

Deliberately free of network and API-key dependencies so retrieval hit-rate,
judge-score parsing, and table formatting can be unit tested without an
embeddings backend or a live model.
"""

from __future__ import annotations

import re


def normalize_url(url: str) -> str:
    """Fold trivial URL differences (trailing slash, case, whitespace) so an
    expected page and a retrieved source compare equal when they're the same."""
    return (url or "").strip().rstrip("/").lower()


def retrieval_hit(retrieved_urls, expected_urls) -> bool:
    """True if any expected source page appears among the retrieved sources."""
    retrieved = {normalize_url(u) for u in retrieved_urls}
    return any(normalize_url(e) in retrieved for e in expected_urls)


def hit_rate(flags) -> float:
    """Fraction of questions whose retrieval included an expected source."""
    flags = list(flags)
    return sum(1 for f in flags if f) / len(flags) if flags else 0.0


def parse_judge_score(text):
    """Pull a 1-5 integer score out of an LLM judge's reply.

    Accepts 'Score: 4', '4/5', a bare '4', or a 1-5 digit anywhere in a short
    sentence. Returns the int, or None if no in-range digit is found (so a
    garbled judgment is visibly missing rather than silently counted as zero)."""
    if not text:
        return None
    for pattern in (
        r"(?:score\s*[:=]?\s*)([1-5])\b",  # "Score: 4"
        r"\b([1-5])\s*/\s*5\b",            # "4/5"
        r"\b([1-5])\b",                     # a standalone 1-5 anywhere
    ):
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return None


def mean(values):
    """Average of the non-None values, or None if there are none."""
    nums = [v for v in values if v is not None]
    return sum(nums) / len(nums) if nums else None


def format_table(rows, headers) -> str:
    """Render rows (list of tuples) as a fixed-width text table."""
    cols = list(zip(*([headers] + rows))) if rows else [[h] for h in headers]
    widths = [max(len(str(c)) for c in col) for col in cols]

    def line(cells):
        return "  ".join(str(c).ljust(w) for c, w in zip(cells, widths))

    out = [line(headers), line(["-" * w for w in widths])]
    out += [line(r) for r in rows]
    return "\n".join(out)
