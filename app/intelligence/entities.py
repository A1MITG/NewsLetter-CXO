"""Sprint 5 (§5). Entity extraction.

Gazetteer and pattern driven, no model. Entity extraction is the stage where
a deterministic list genuinely beats generation: every extraction points at a
term in config/entities.yaml, so a wrong entity is a visible config bug rather
than a hallucination you have to go looking for.

Entities are stored with their surface form and where they were found, so
Sprint 10 (developments) can cluster on shared entities and §11 can show its
working.

Design bias: precision over recall. A missed entity costs a little ranking
signal. A fabricated one — "Stock" read as a company because it was somebody's
surname — is the exact defect class this pipeline exists to remove.
"""
import pathlib
import re
from functools import lru_cache

import yaml

CONFIG = pathlib.Path(__file__).resolve().parents[2] / "config" / "entities.yaml"

# Corporate suffixes let us find companies that are not in the gazetteer,
# without guessing at bare capitalised words.
_SUFFIX_RX = re.compile(
    r"\b([A-Z][\w&.\-]*(?:\s+[A-Z][\w&.\-]*){0,3})\s+"
    r"(Inc|Inc\.|Ltd|Ltd\.|LLC|PLC|Plc|Corp|Corp\.|Corporation|Company|"
    r"Holdings|Group|AG|SE|NV|SA|Pvt|Limited)\b"
)

# A capitalised full name: "Sundar Pichai", "Paul J. Stock", "Elon Musk".
_NAME = r"[A-Z][a-z]+(?:\s+[A-Z]\.?)?(?:\s+[A-Z][a-z]+){1,2}"


@lru_cache(maxsize=1)
def _config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}


@lru_cache(maxsize=1)
def _gazetteers() -> dict:
    """Compile every list once. Whole-word, case-insensitive."""
    cfg = _config()
    out = {}
    for kind in ("countries", "cities", "companies", "regulators",
                 "agencies", "technologies", "industries"):
        terms = cfg.get(kind) or []
        out[kind] = [(t, re.compile(r"\b" + re.escape(t) + r"\b", re.IGNORECASE))
                     for t in terms]
    return out


@lru_cache(maxsize=1)
def _role_rx():
    roles = sorted(_config().get("executive_roles") or [], key=len, reverse=True)
    if not roles:
        return None
    alt = "|".join(re.escape(r) for r in roles)
    # Case-sensitivity is load-bearing here. The name pattern relies on
    # [A-Z][a-z]+ meaning "a proper noun"; a global re.IGNORECASE makes it
    # match any word, and the greedy {1,2} then swallows the following
    # lowercase token ("Jensen Huang backs"). So roles are made
    # case-insensitive with scoped (?i:...) groups and names are not.
    role = rf"(?i:{alt})"
    # "CEO Jane Doe"  |  "Jane Doe, chief executive"  |  "names Jane Doe as CFO"
    return re.compile(
        rf"(?:\b(?P<role_first>{role})\s+(?P<name_after>{_NAME})\b)"
        rf"|(?:\b(?P<name_before>{_NAME})\s*,\s*(?i:the\s+)?(?P<role_after>{role})\b)"
        rf"|(?:(?i:\b(?:names|appoints|elects)\s+)(?P<name_named>{_NAME})"
        rf"(?i:\s+as\s+)(?P<role_named>{role})\b)"
    )


def _record(bucket: list, value: str, kind: str, where: str, surface: str) -> None:
    if not any(e["value"].lower() == value.lower() for e in bucket):
        bucket.append({"value": value, "type": kind, "where": where, "surface": surface})


def extract(title: str, summary: str = "") -> dict:
    """-> {countries: [...], companies: [...], executives: [...], ...}"""
    cfg = _config()
    out = {k: [] for k in ("countries", "cities", "companies", "executives",
                           "regulators", "agencies", "technologies", "industries")}

    fields = [("title", title or "")]
    if summary:
        fields.append(("summary", summary))

    # --- gazetteer passes ---
    for where, text in fields:
        for kind, terms in _gazetteers().items():
            for canonical, rx in terms:
                m = rx.search(text)
                if m:
                    _record(out[kind], canonical, kind[:-1], where, m.group(0))

        # country aliases -> canonical, so "US" and "United States" merge
        for alias, canonical in (cfg.get("country_aliases") or {}).items():
            if re.search(r"\b" + re.escape(alias) + r"\b", text):
                _record(out["countries"], canonical, "country", where, alias)

    # --- companies by corporate suffix (beyond the gazetteer) ---
    for where, text in fields:
        for m in _SUFFIX_RX.finditer(text):
            name = f"{m.group(1)} {m.group(2)}".strip()
            _record(out["companies"], name, "company", where, m.group(0))

    # --- executives: a name is only a person next to a role term ---
    rx = _role_rx()
    stop = {s.lower() for s in (cfg.get("person_stoplist") or [])}
    if rx:
        for where, text in fields:
            for m in rx.finditer(text):
                name = (m.group("name_after") or m.group("name_before")
                        or m.group("name_named") or "").strip()
                role = (m.group("role_first") or m.group("role_after")
                        or m.group("role_named") or "").strip()
                if not name:
                    continue
                if name.split()[0].lower() in stop:
                    continue
                if not any(e["value"].lower() == name.lower() for e in out["executives"]):
                    out["executives"].append({"value": name, "type": "executive",
                                              "role": role, "where": where,
                                              "surface": m.group(0).strip()})
    return out


def count(entities: dict) -> int:
    return sum(len(v) for v in entities.values())


def apply(signal):
    """Populate signal.entities in place, with a trace (§11)."""
    found = extract(signal.title, signal.summary)
    signal.entities = found
    n = count(found)
    if n:
        summary = {k: [e["value"] for e in v] for k, v in found.items() if v}
        signal.trace("entities", f"extracted {n} entities across "
                                 f"{len(summary)} types", summary)
    else:
        signal.trace("entities", "no entities matched the gazetteer", None)
    return signal


def apply_all(signals: list) -> list:
    for s in signals:
        apply(s)
    return signals
