"""Sprint 5 exit tests (PRD §5 — Entity Extraction).

Contract: known entities are found in known articles, and nothing is
invented. The second half matters more — a fabricated entity is the defect
class this pipeline exists to remove.
"""
import pytest

from app.intelligence.entities import apply_all, count, extract


# ---------- the false-positive guard ----------

def test_surname_is_not_read_as_a_company():
    """'Paul J. Stock' is a person. 'Stock' must never become a company."""
    e = extract("Paul J. Stock named president of Berkley's Carolina Casualty")
    assert not any(c["value"].lower() == "stock" for c in e["companies"])


def test_bare_capitalised_word_is_not_a_person():
    e = extract("Global Markets Rally On Renewed Optimism")
    assert e["executives"] == []


def test_stoplist_blocks_pseudo_names():
    e = extract("The Group, chief executive of nothing in particular")
    assert not any(x["value"].startswith("The ") for x in e["executives"])


# ---------- people are only found next to a role ----------

def test_executive_detected_before_role():
    e = extract("Nvidia CEO Jensen Huang backs open AI models coalition")
    assert any(x["value"] == "Jensen Huang" for x in e["executives"])


def test_executive_detected_after_role():
    e = extract("Sundar Pichai, chief executive, said Gemini adoption accelerated")
    assert any(x["value"] == "Sundar Pichai" for x in e["executives"])


def test_executive_detected_in_appointment_phrasing():
    e = extract("Berkley names Sarah Mitchell as CFO of its casualty unit")
    assert any(x["value"] == "Sarah Mitchell" for x in e["executives"])


def test_executive_carries_its_role():
    e = extract("Nvidia CEO Jensen Huang backs open AI models coalition")
    person = next(x for x in e["executives"] if x["value"] == "Jensen Huang")
    assert person["role"].lower() == "ceo"


# ---------- gazetteers ----------

def test_countries_and_aliases_merge():
    e = extract("US and UK tighten sanctions", "The United States acted first.")
    values = {c["value"] for c in e["countries"]}
    assert "United States" in values and "United Kingdom" in values
    # "US" and "United States" must not both appear as separate entities
    assert sum(1 for c in e["countries"] if c["value"] == "United States") == 1


def test_companies_from_gazetteer():
    e = extract("Munich Re reports preliminary Q2 net profit")
    assert any(c["value"] == "Munich Re" for c in e["companies"])


def test_companies_from_corporate_suffix():
    """Beyond the gazetteer, without guessing at bare capitalised words."""
    e = extract("Acme Speciality Holdings Ltd acquires a rival book")
    assert any("Ltd" in c["value"] for c in e["companies"])


def test_regulators_agencies_technologies():
    e = extract("SEC and the Federal Reserve weigh AI rules",
                "NATO discussed generative AI and cybersecurity.")
    assert any(r["value"] == "SEC" for r in e["regulators"])
    assert any(a["value"] == "NATO" for a in e["agencies"])
    assert any(t["value"].lower() == "generative ai" for t in e["technologies"])


def test_cities_detected():
    e = extract("GCC leasing surges across Bengaluru and Hyderabad")
    values = {c["value"] for c in e["cities"]}
    assert "Bengaluru" in values and "Hyderabad" in values


# ---------- provenance (§11) ----------

def test_every_entity_records_where_it_came_from():
    e = extract("Munich Re reports profit", "Allianz also reported results.")
    for bucket in e.values():
        for item in bucket:
            assert item["where"] in ("title", "summary")
            assert item["surface"], "no surface form recorded"


def test_no_duplicate_entities_within_a_type():
    e = extract("India and India again", "India once more.")
    values = [c["value"] for c in e["countries"]]
    assert len(values) == len(set(values))


# ---------- live corpus ----------

def test_extraction_runs_clean_on_live_corpus(enriched):
    for s in apply_all(enriched):
        assert isinstance(s.entities, dict)
        for bucket in s.entities.values():
            assert isinstance(bucket, list)


def test_corpus_yields_meaningful_coverage(enriched):
    sigs = apply_all(enriched)
    with_any = sum(1 for s in sigs if count(s.entities) > 0)
    ratio = with_any / len(sigs)
    assert ratio > 0.50, f"only {ratio:.0%} of articles yielded any entity"


def test_every_signal_is_traced(enriched):
    for s in apply_all(enriched):
        assert any(e["stage"] == "entities" for e in s.explain)


def test_entities_are_json_safe(enriched):
    import json
    for s in apply_all(enriched)[:30]:
        json.dumps(s.entities)
