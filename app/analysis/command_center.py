"""Shared Command Center engine mapping.

Single source of truth for turning scored Signals into the Command Center's
{engineId: {name, articles, comingSoon}} contract.

Both surfaces read from here so they cannot drift apart:
  - app/api/routes.py          -> GET /api/command-center   (live)
  - scripts/build_command_center_data.py -> public/command_center_data.json (static build)

Signal name -> (Command Center engine id, display name). Signal Executive is
intentionally unmapped: the Command Center layout has no tile for it.
"""
import re

SIGNAL_TO_ENGINE = {
    'Signal Global': ('global', 'Global Affairs'),
    'Signal Business': ('economy', 'Economy, Business & Markets'),
    'Signal AI': ('ai', 'AI, Technology & Innovation'),
    'Signal GCC': ('gcc', 'GCC & Enterprise Technology'),
    'Signal Insurance': ('insurance', 'Insurance & Financial Services'),
}

# Engines with no scoring logic yet — written out honestly, not fabricated.
COMING_SOON_ENGINES = {
    'banking': 'Banking',
    'manufacturing': 'Manufacturing',
    'energy': 'Energy',
    'defence': 'Defence',
    'cyber': 'Cyber Intelligence',
    'supplychain': 'Supply Chain',
    'healthcare': 'Healthcare',
    'telecom': 'Telecom & Digital Infrastructure',
    'climate': 'Climate & Sustainability',
}

COMING_SOON_NOTE = (
    "No scoring engine built for this domain yet — it isn't classifying "
    "real articles today. Planned as a future configurable Intelligence Domain."
)


# The three lead cards under "Global Situational Awareness", in page order.
HERO_ENGINES = (
    ('global', 'Global Affairs', 'global'),
    ('economy', 'Economy, Business & Markets', 'economy'),
    ('ai', 'AI, Technology & Innovation', 'ai'),
)


# Words that are never part of a person's name. The Sprint 5 extractor keys
# off a role term followed by capitalised words ("CEO Jane Doe"), so a
# headline like "Chairman Stirs Controversy" yields "Stirs Controversy" and
# "CEO Designate Tewolde Gebremariam" keeps the qualifier. Those are fine as a
# ranking signal, but Executive Pulse prints the name under a photograph of a
# real person, so a wrong one is the exact defect this pipeline exists to
# remove. Anything here disqualifies the extraction outright.
_NOT_NAME_WORDS = frozenset("""
stirs opposed backs weighs says said lauds announces launches urges warns
calls plans seeks sees expects steps names appoints elects joins quits
resigns designate elect nominee interim acting incoming outgoing deputy
former ex chief executive officer chairman chairwoman president director
""".split())


def _looks_like_a_person(name):
    """True when every token could plausibly belong to a person's name."""
    tokens = name.split()
    if not (2 <= len(tokens) <= 3):
        return False
    for token in tokens:
        bare = token.strip('.').lower()
        if bare in _NOT_NAME_WORDS:
            return False
        if not token[:1].isupper():
            return False
    return True


# --- Supplementary headline patterns for Executive Pulse -------------------
#
# app/intelligence/entities.py matches three shapes: "CEO Jane Doe",
# "Jane Doe, chief executive" and "names Jane Doe as CFO". Real leadership
# headlines carry others, and each miss costs this row a card:
#
#   "Helmsman names Emily Drew president, CEO"   -> no "as" before the role
#   "Who is Karandeep Anand? The Character.AI CEO ..."
#   "Warren Buffett steps down as Berkshire chair" -> role follows the verb
#
# These run only for this row, so the shared Sprint 5 extractor (and the 18
# tests that pin its behaviour) stays untouched.

_PULSE_NAME = r"[A-Z][a-z]+(?:\s+[A-Z]\.?)?(?:\s+[A-Z][a-z]+){1,2}"

_PULSE_ROLE = (
    r"chief\s+executive\s+officer|chief\s+executive|chief\s+financial\s+officer|"
    r"chief\s+technology\s+officer|chief\s+operating\s+officer|managing\s+director|"
    r"chairman|chairwoman|chairperson|chair|president|ceo|cfo|cto|coo|cio|"
    r"co-founder|founder|deputy\s+governor|governor|minister|secretary"
)

# A role word must appear somewhere in the headline for any of these to fire:
# "Who is <Name>?" alone matches athletes and celebrities just as happily.
_PULSE_HAS_ROLE = re.compile(_PULSE_ROLE, re.IGNORECASE)

# Case-sensitivity is load-bearing, exactly as it is in entities.py: a global
# re.IGNORECASE turns _PULSE_NAME's [A-Z][a-z]+ into "any word", so the greedy
# {1,2} swallows the role that follows ("Emily Drew president"). The verbs and
# roles are therefore made case-insensitive with scoped (?i:...) groups while
# the name pattern stays case-sensitive.
_PULSE_PATTERNS = (
    # "names/appoints/promotes <Name> president" (with or without "as")
    re.compile(
        r"(?i:(?:names?|named|appoints?|appointed|elects?|elected|promotes?|promoted))\s+"
        r"(?P<name>" + _PULSE_NAME + r")\s*,?\s*(?i:(?:as\s+)?(?:the\s+)?)"
        r"(?i:" + _PULSE_ROLE + r")"
    ),
    # "Who is <Name>?" — profile pieces, gated by _PULSE_HAS_ROLE above.
    re.compile(r"(?i:who\s+is\s+)(?P<name>" + _PULSE_NAME + r")\b"),
    # "<Name> steps down / resigns / to succeed ..."
    re.compile(
        r"\b(?P<name>" + _PULSE_NAME + r")\s+"
        r"(?i:steps?\s+down|stepping\s+down|resigns?|resigned|quits?|retires?|"
        r"to\s+succeed|succeeds)\b"
    ),
)


def _names_from_headline(title):
    """Leader names this headline states outright, for shapes entities.py misses."""
    if not _PULSE_HAS_ROLE.search(title):
        return []
    out = []
    for rx in _PULSE_PATTERNS:
        for m in rx.finditer(title):
            name = (m.group("name") or "").strip()
            if name and name not in out:
                out.append(name)
    return out


def _is_the_subject(name, title):
    """True when the headline is about this person, not merely near them.

    Matching the full name is too strict: "Buffett Steps Down as Berkshire
    Chair" is entirely about Warren Buffett but never spells out his first
    name. Matching the surname alone is enough, because the name was already
    extracted from this headline next to a role term — the surname check only
    decides whether the headline, rather than the summary, is where it sits.
    """
    surname = name.split()[-1].lower()
    pattern = r"\b" + re.escape(surname) + r"\b"
    return re.search(pattern, title.lower()) is not None


def build_pulse_cards(current_articles, limit=8):
    """Executive Pulse: leaders with genuine coverage in today's corpus.

    Was four hardcoded cards — name, photo and hand-written commentary baked
    into the HTML, each stamped "today" while pointing at July 2026 stories.

    Scans the whole corpus rather than the ~40 articles already chosen for
    tiles: a leader story worth showing here often is not the top-scoring
    article in its Signal.

    A card is only built when the headline itself names an executive next to a
    role term AND the article carries a real photograph, because the layout
    puts the person's name over the image as the subject of the story. No qualifying leader today means an empty row, which is the
    honest outcome the section's own note already promises.
    """
    from ..intelligence.entities import extract
    from ..intelligence.freshness import classify
    from ..intelligence.normalize import parse_date

    seen_names = set()
    cards = []
    for raw in current_articles:
        # The caller passes the raw corpus, which still holds whatever a feed
        # served; gate here so a dead feed cannot put a years-old leader story
        # under a "today" stamp.
        if not classify(parse_date(raw.get('date'))).get('is_current'):
            continue
        image = (raw.get('image') or '').strip()
        if not image.startswith('http'):
            continue
        title = (raw.get('title') or '').strip()
        if not title:
            continue
        # Read the summary too: a headline often carries the surname alone
        # ("Buffett Steps Down as Berkshire Chair") with no role term beside
        # it, so a title-only pass misses the person entirely. _is_the_subject
        # below is what keeps an incidental mention out.
        found = extract(title, raw.get('summary', ''))
        candidates = [(p.get('value', '').strip(), p.get('role', ''))
                      for p in found.get('executives', [])]
        candidates += [(n, '') for n in _names_from_headline(title)]
        for name, role in candidates:
            if not name or not _looks_like_a_person(name):
                continue
            if not _is_the_subject(name, title):
                continue
            if name.lower() in seen_names:
                continue
            seen_names.add(name.lower())
            cards.append({
                'name': name,
                'role': role,
                'title': title,
                'url': raw.get('url', ''),
                'image': image,
                'source': _publisher(raw.get('url', '')),
            })
            break
        if len(cards) >= limit:
            break
    return cards


def _publisher(url):
    """Bare domain for the card's meta line."""
    try:
        host = url.split('/')[2]
    except IndexError:
        return ''
    return host.replace('www.', '').split('.')[0]


def build_hero_cards(engine_data, articles_by_title):
    """Top current story per lead engine, for the hero row.

    These three cards were hardcoded HTML with base64 images and hand-written
    commentary, so they stayed frozen on a July 2026 story while the tiles
    below them moved on. An image is required: the card design is image-led
    and renders badly without one, so we take the first scored article that
    has a usable one rather than showing an empty frame.
    """
    cards = []
    for engine_id, label, icon in HERO_ENGINES:
        engine = engine_data.get(engine_id) or {}
        for article in engine.get('articles', []):
            raw = articles_by_title.get(article['title'], {})
            image = (raw.get('image') or '').strip()
            if not image.startswith('http'):
                continue
            cards.append({
                'engine': engine_id,
                'label': label,
                'icon': icon,
                'title': article['title'],
                'url': article['url'],
                'image': image,
                'summary': (raw.get('summary') or '').strip()[:220],
            })
            break
    return cards


def build_featured(hero_cards, engine_data, articles_by_title):
    """The single large Featured Analysis card.

    Was one hardcoded article (a July 2026 GCC office-leasing piece). Takes
    the best current story not already used in the hero row, so the page never
    shows the same headline twice.
    """
    used = {c['url'] for c in hero_cards}
    for engine_id in ('gcc', 'insurance', 'economy', 'global', 'ai'):
        engine = engine_data.get(engine_id) or {}
        for article in engine.get('articles', []):
            if article['url'] in used:
                continue
            raw = articles_by_title.get(article['title'], {})
            image = (raw.get('image') or '').strip()
            if not image.startswith('http'):
                continue
            return {
                'title': article['title'],
                'url': article['url'],
                'image': image,
                'summary': (raw.get('summary') or '').strip()[:260],
                'label': engine.get('name', ''),
            }
    return None


def build_engine_data(signals_data):
    """Map a synthesize_signals() result onto the Command Center tile contract."""
    by_name = {s['name']: s for s in signals_data.get('signals', [])}

    engine_data = {}
    for signal_name, (engine_id, display_name) in SIGNAL_TO_ENGINE.items():
        signal = by_name.get(signal_name, {})
        engine_data[engine_id] = {
            'name': display_name,
            'articles': [
                {'title': a['title'], 'url': a['url']}
                for a in signal.get('articles', [])
            ],
        }

    for engine_id, display_name in COMING_SOON_ENGINES.items():
        engine_data[engine_id] = {
            'name': display_name,
            'comingSoon': True,
            'note': COMING_SOON_NOTE,
        }

    return engine_data
