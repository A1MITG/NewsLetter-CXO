"""Sprint 1 (§1). Raw scraper dict -> Signal, discarding nothing.

Replaces the lossy ``{'title': ..., 'url': ...}`` projection in
scripts/build_command_center_data.py, which threw away the publication date
and image the scraper had already captured.
"""
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

from .schema import MAX_SUMMARY_CHARS, Signal, Source

# Publisher display names for full credit on the Command Center. A bare
# hostname is not an attribution — "livemint" is not how Mint is cited.
PUBLISHERS = {
    "insurancejournal.com": "Insurance Journal",
    "businessinsurance.com": "Business Insurance",
    "propertycasualty360.com": "PropertyCasualty360",
    "claimsjournal.com": "Claims Journal",
    "insurancebusinessmag.com": "Insurance Business",
    "nationalunderwriter.com": "National Underwriter",
    "thinkadvisor.com": "ThinkAdvisor",
    "reinsurancene.ws": "Reinsurance News",
    "bbci.co.uk": "BBC News",
    "bbc.co.uk": "BBC News",
    "bbc.com": "BBC News",
    "theguardian.com": "The Guardian",
    "aljazeera.com": "Al Jazeera",
    "economictimes.indiatimes.com": "The Economic Times",
    "timesofindia.indiatimes.com": "The Times of India",
    "livemint.com": "Mint",
    "moneycontrol.com": "Moneycontrol",
    "247wallst.com": "24/7 Wall St.",
    "reuters.com": "Reuters",
    "bloomberg.com": "Bloomberg",
}


def publisher_for(host: str) -> str:
    """Exact match, then parent-domain match, then a readable fallback."""
    if not host:
        return ""
    if host in PUBLISHERS:
        return PUBLISHERS[host]
    parts = host.split(".")
    for i in range(1, len(parts) - 1):
        parent = ".".join(parts[i:])
        if parent in PUBLISHERS:
            return PUBLISHERS[parent]
    stem = parts[0] if parts else host
    return stem.replace("-", " ").title()


def parse_date(value) -> datetime | None:
    """RFC-2822 first (the RSS standard), then ISO-8601.

    51 of 323 cached articles currently fail both. Sprint 1 only records
    that fact in the trace; Sprint 3 widens the parser.
    """
    if not value:
        return None
    raw = str(value).strip()
    try:
        dt = parsedate_to_datetime(raw)
        if dt is not None:
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        pass
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def normalize(raw: dict, category: str = "") -> Signal | None:
    """One scraped dict -> one Signal. Returns None for non-articles."""
    title = (raw.get("title") or "").strip()
    url = (raw.get("url") or "").strip()
    if not title or not url:
        return None
    # Titles under 4 words are almost always scraped section headers
    # ("Industry News", "Mergers & Acquisitions"), not articles.
    if len(title.split()) < 4:
        return None

    host = (urlparse(url).hostname or "").replace("www.", "")
    published = parse_date(raw.get("date"))
    summary = (raw.get("summary") or raw.get("description") or "").strip()

    sig = Signal(
        title=title,
        url=url,
        summary=summary[:MAX_SUMMARY_CHARS],
        published_at=published,
        author=(raw.get("author") or "").strip(),
        image_url=(raw.get("image") or "").strip(),
        language=(raw.get("language") or "en"),
        source=Source(domain=host, name=host.split(".")[0] if host else "",
                      category=category),
        raw=dict(raw),                       # nothing is ever lost
        publisher=publisher_for(host),
        canonical_url=url,
    )

    if published is None and raw.get("date"):
        sig.trace("normalize", "unparseable publication date", raw.get("date"))
    if published is None and not raw.get("date"):
        sig.trace("normalize", "feed supplied no publication date", None)
    if not summary:
        sig.trace("normalize", "feed supplied no description", None)
    if not sig.publisher:
        sig.trace("normalize", "could not resolve publisher for attribution", host)

    return sig


def normalize_all(raw_articles: list[dict], category: str = "") -> list[Signal]:
    """Normalize a scrape, dropping exact-duplicate titles."""
    out: list[Signal] = []
    seen: set[str] = set()
    for raw in raw_articles:
        sig = normalize(raw, category)
        if sig is None:
            continue
        key = sig.title.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(sig)
    return out
