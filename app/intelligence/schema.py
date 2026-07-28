"""The Signal object — the canonical unit of the intelligence pipeline.

PRD §15: every stage enriches, no stage discards. Sprints 2-12 populate the
enrichment fields below; none of them may mutate the raw block or the §1
fields. Tests enforce that invariant.

Attribution (PRD, user requirement): the Command Center publishes the
original headline verbatim with full credit to the publisher and a link to
the original. No generated prose ever reaches that surface — synthesis
happens one layer downstream, in the Signals newsletter.
"""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

# Maximum characters of publisher summary we retain. Headline + link +
# short excerpt is the standard aggregator position; retaining full article
# bodies would not be.
MAX_SUMMARY_CHARS = 1200


@dataclass
class Source:
    """Where a Signal came from, and how much weight that carries."""
    domain: str = ""              # livemint.com
    name: str = ""                # livemint
    category: str = ""            # feed group from scraper/sources.py
    # --- §2, populated in Sprint 2 ---
    tier: str = "unknown"         # tier_1 | tier_2 | tier_3 | unknown
    authority: float = 0.5        # 0-1, how expert on its own subject
    independence: float = 0.5     # 0-1, arms-length vs self-reporting


@dataclass
class Signal:
    """One scored, attributed article."""

    # ---------- §1: preserved verbatim, never discarded ----------
    title: str
    url: str
    summary: str = ""
    published_at: datetime | None = None
    author: str = ""
    image_url: str = ""
    language: str = "en"
    source: Source = field(default_factory=Source)
    scraped_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    raw: dict[str, Any] = field(default_factory=dict)

    # ---------- §1: attribution (Command Center renders these as-is) ----------
    publisher: str = ""                 # display name: "Insurance Journal"
    canonical_url: str = ""             # publisher's own URL
    attribution_required: bool = True   # never render without publisher + link

    # ---------- enrichment: later sprints append here ----------
    freshness: dict = field(default_factory=dict)     # §3  Sprint 3
    domains: list = field(default_factory=list)       # §4  Sprint 4
    entities: dict = field(default_factory=dict)      # §5  Sprint 5
    events: list = field(default_factory=list)        # §6  Sprint 6
    impact: dict = field(default_factory=dict)        # §7  Sprint 7
    priority: str = ""                                # §8  Sprint 8
    explain: list = field(default_factory=list)       # §11 Sprint 9
    development_id: str = ""                          # §10 Sprint 10
    newsletter: dict = field(default_factory=dict)    # §9  Sprint 11 (LLM)
    recommendation: str = ""                          # §12 Sprint 12

    # ---------- projection labels (one taxonomy, two groupings) ----------
    engine_id: str = ""       # Command Center tile
    signal_name: str = ""     # Signals newsletter section

    def trace(self, stage: str, reason: str, evidence: Any = None) -> None:
        """§11. Record why a decision was made, at the moment it is made."""
        self.explain.append({"stage": stage, "reason": reason, "evidence": evidence})

    def is_publishable(self) -> bool:
        """Attribution gate. A Signal without a publisher and a working link
        must never reach the Command Center."""
        return bool(self.title and self.canonical_url and self.publisher)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["published_at"] = self.published_at.isoformat() if self.published_at else None
        d["scraped_at"] = self.scraped_at.isoformat()
        return d
