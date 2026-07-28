"""Sprint 0 exit tests: the harness itself works.

If these fail, nothing downstream can be trusted — every later sprint
measures itself through these fixtures.
"""
from conftest import PRIORITIES


def test_cache_loads(raw_articles):
    assert len(raw_articles) > 0, "article cache is empty"


def test_cache_has_expected_shape(raw_articles):
    first = raw_articles[0]
    assert "title" in first
    assert "url" in first


def test_cache_is_dated(raw_cache):
    assert "date" in raw_cache, "cache has no date stamp — freshness is unknowable"


def test_gold_labels_are_valid(gold):
    """Empty gold set is allowed (Sprint 0 ships before labelling).
    Any label present must be one of the five priorities."""
    for row in gold:
        assert row["priority"] in PRIORITIES, (
            f"invalid label {row['priority']!r} for {row.get('title', '')[:60]!r}"
        )


def test_gold_rows_have_source_article(gold):
    for row in gold:
        assert row.get("title"), "gold row missing title"
        assert row.get("url"), "gold row missing url"
