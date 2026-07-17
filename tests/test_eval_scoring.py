"""Eval scoring math: retrieval hit detection, judge-score parsing, aggregates,
table formatting. No embeddings, no network, no API key."""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "eval"))

from scoring import (
    format_table,
    hit_rate,
    mean,
    normalize_url,
    parse_judge_score,
    retrieval_hit,
)


def test_normalize_url_folds_slash_and_case():
    assert normalize_url("https://X/A/") == normalize_url("https://x/a")


def test_retrieval_hit_true_when_expected_page_retrieved():
    retrieved = ["https://x/a", "https://x/b", "https://x/c"]
    assert retrieval_hit(retrieved, ["https://x/b"]) is True
    # trailing slash on the expected side still matches
    assert retrieval_hit(retrieved, ["https://x/b/"]) is True


def test_retrieval_hit_false_when_missing():
    assert retrieval_hit(["https://x/a"], ["https://x/z"]) is False


def test_retrieval_hit_any_expected_source_counts():
    # multi-source questions hit if the retriever finds either page
    assert retrieval_hit(["https://x/b"], ["https://x/a", "https://x/b"]) is True


def test_hit_rate():
    assert hit_rate([True, True, False, False]) == 0.5
    assert hit_rate([]) == 0.0


def test_parse_judge_score_formats():
    assert parse_judge_score("Score: 4") == 4
    assert parse_judge_score("4/5") == 4
    assert parse_judge_score("5") == 5
    assert parse_judge_score("I'd rate this a score of 3 overall") == 3


def test_parse_judge_score_out_of_range_or_garbled_is_none():
    assert parse_judge_score("no number here") is None
    assert parse_judge_score("9") is None
    assert parse_judge_score("") is None


def test_mean_ignores_none():
    assert mean([4, None, 2]) == 3.0
    assert mean([None]) is None


def test_format_table_aligns_columns():
    out = format_table([(1, "short", "yes"), (2, "a longer question", "no")],
                       ["#", "question", "retr"])
    lines = out.splitlines()
    assert lines[0].startswith("#")
    # every row is padded to the same width
    assert len({len(line) for line in lines}) == 1


def test_golden_set_is_well_formed():
    path = os.path.join(os.path.dirname(__file__), "..", "eval", "golden_set.json")
    with open(path) as f:
        golden = json.load(f)
    assert len(golden) >= 12
    for item in golden:
        assert item["question"].strip()
        assert item["sources"] and all(s.startswith("http") for s in item["sources"])
