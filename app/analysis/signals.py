# app/analysis/signals.py
"""Classify scraped articles into the six launch Signals (Phase 1).

Scoring framework
-----------------
Every keyword carries an evidence weight: 4 = definitive phrase, 3 = strong
term, 2 = medium, 1 = weak/contextual. An article's score for a signal is the
sum of the weights of matched keywords (whole-word matches only), with title
matches counting double. An article is classified only when its best score
reaches THRESHOLD — weak hits alone (e.g. "India" inside "Air India") can
never force-fit an article into a bucket. Ties resolve toward the more
specific signal (PRIORITY order). Articles that clear the bar nowhere are
left unclassified and dropped from the view rather than misfiled.
"""
import re
from datetime import datetime

from ..intelligence.freshness import classify as classify_freshness
from ..intelligence.normalize import parse_date

# Display order = the SIGNAL masthead hierarchy.
SIGNALS = [
    {'name': 'Signal Global', 'purpose': 'Geopolitics · Trade · Defence',
     'audience': 'Executives & Policy'},
    {'name': 'Signal Business', 'purpose': 'Business · Markets · Strategy',
     'audience': 'Leaders & Professionals'},
    {'name': 'Signal AI', 'purpose': 'AI · GenAI · Automation · Robotics',
     'audience': 'Everyone'},
    {'name': 'Signal GCC', 'purpose': 'Global Capability Centers · India · Shared Services',
     'audience': 'GCC Leaders'},
    {'name': 'Signal Insurance', 'purpose': 'Insurance · Reinsurance · InsurTech',
     'audience': 'BFSI'},
    {'name': 'Signal Executive', 'purpose': 'Executive Briefs · Leadership · Boardroom Insights',
     'audience': 'Senior Leaders'},
]

# --- Signal GCC: faceted evidence -----------------------------------------
#
# GCC is the one Signal where a flat keyword bag kept misfiring, because the
# vocabulary that surrounds a capability centre -- Indian city names, IT
# vendor names, the word "India" -- also surrounds a great deal of ordinary
# Indian business news. Two live defects came from exactly that:
#
#   "Indian art auction market triples"      -> india(1) + indian(1)    = 3
#   "Puravankara ... Greater Noida project"  -> noida(2) + gurugram(2)  = 6
#
# The second cleared even the stricter evidence rules in config/domains.yaml
# (min_score 6, two distinct keywords), so raising the bar was never going to
# fix it. What those stories lack is not the AMOUNT of evidence but the KIND:
# neither names a capability centre, and neither describes anything happening
# to one. So GCC evidence is split across two axes, and both must be present:
#
#   ENTITY  -- is this about a capability centre?  (GCC_ENTITY)
#   ACTION  -- is something happening to it?       (GCC_ACTION, by facet)
#
# Geography is deliberately NOT evidence at any weight. Tier-2 cities now
# court the same IT/ITES investment as Bengaluru and Hyderabad, so the set of
# "GCC cities" is widening toward "Indian cities"; a longer city list makes
# this worse, not better. Cities, vendors and nationality sit in GCC_CONTEXT,
# which scores nothing and exists to record what must never classify alone.

GCC_ENTITY = {
    # Decisive: names a capability centre outright.
    'global capability center': 4, 'global capability centre': 4,
    'global capability centers': 4, 'global capability centres': 4,
    'global capability': 4,
    'capability center': 4, 'capability centre': 4,
    'capability centers': 4, 'capability centres': 4,
    'global in-house center': 4, 'global in-house centre': 4, 'gic': 4,
    'captive center': 4, 'captive centre': 4, 'captive unit': 4,
    'global delivery center': 4, 'global delivery centre': 4, 'gdc': 4,
    'shared services center': 4, 'shared services centre': 4,
    'offshore development center': 4, 'offshore development centre': 4,
    'odc': 4,
    'center of excellence': 4, 'centre of excellence': 4, 'coe': 4,
    'global business services': 4, 'gbs': 4,
    'gcc': 4, 'gccs': 4,
    'engineering center': 4, 'engineering centre': 4,
    'innovation center': 4, 'innovation centre': 4,
    'technology center': 4, 'technology centre': 4,
    'development center': 4, 'development centre': 4,
    'delivery center': 4, 'delivery centre': 4,
    'competency center': 4, 'competency centre': 4,
    'r&d center': 4, 'r&d centre': 4, 'research and development center': 4,
    # Supporting: the operating model rather than the centre itself.
    'shared services': 2, 'offshoring': 2, 'nearshoring': 2, 'reshoring': 2,
    'outsourcing': 2, 'it services': 2, 'ites': 2, 'bpo': 2, 'kpo': 2,
    'back office': 2, 'in-house center': 2, 'in-house centre': 2,
    'managed services': 2, 'nasscom': 2, 'global mandate': 2,
    'global roles': 2,
    # Bare 'captive' is deliberately absent: in this corpus it is far more
    # often a CAPTIVE INSURER ("Allianz names captive leader", "A-Cap
    # Insurers file suit") than a captive centre, and Signal Insurance is
    # the right home for those. 'captive center/centre/unit' above are
    # unambiguous and stay.
}

# Each facet contributes its weight ONCE, however many of its synonyms fire,
# so a headline cannot inflate by restating one event ("opens", "opening",
# "to open"). Facets are the lifecycle and nature-of-work distinctions a
# capability-centre story actually turns on.
GCC_ACTION = {
    'new_build': (3, (
        'sets up', 'set up', 'setting up', 'to set up', 'establishes',
        'established', 'establishing', 'establish', 'opens', 'opened',
        'opening', 'to open', 'launches', 'launched', 'launching', 'launch',
        'inaugurates', 'inaugurated', 'unveils', 'unveiled', 'stands up',
        'stood up', 'commissions', 'greenfield', 'new center', 'new centre',
        'first center', 'first centre', 'debuts', 'breaks ground')),
    'expansion': (3, (
        'expands', 'expanded', 'expanding', 'expansion', 'expand',
        'scales up', 'scaling up', 'scale-up', 'ramps up', 'ramping up',
        'ramp-up', 'doubles', 'doubling', 'tripling', 'adds capacity',
        'adding capacity', 'second campus', 'new campus', 'grows headcount',
        'widens', 'broadens', 'enlarges', 'deepens', 'upgrades',
        'extends charter', 'expands mandate', 'expanded mandate')),
    'coe_standup': (4, (
        'center of excellence', 'centre of excellence', 'coe',
        'hub for', 'center for', 'centre for')),
    'augment_capability': (3, (
        'augment', 'augments', 'augmenting', 'augmentation', 'absorbs',
        'take over', 'takes over', 'taking over', 'transitions',
        'transitioning', 'transition', 'migrates', 'migrating', 'migration',
        'insources', 'insourcing', 'in-sourcing', 'consolidates',
        'consolidating', 'consolidation', 'lift and shift',
        'brings in-house', 'moves in-house')),
    'new_development': (3, (
        'product development', 'product engineering', 'new product',
        'end-to-end ownership', 'full stack ownership', 'product ownership',
        'charter expansion', 'digital transformation', 'platform build',
        'greenfield build', 'from scratch', 'ground up', 'r&d mandate')),
    'talent_scale': (2, (
        'hire', 'hires', 'hiring', 'to hire', 'headcount', 'seats',
        'workforce', 'ftes', 'professionals', 'engineers', 'recruit',
        'recruiting', 'roles', 'jobs', 'positions')),
}

# Scores nothing. Present so the exclusion is explicit and reviewable rather
# than an absence someone re-adds in good faith next year.
GCC_CONTEXT = {
    'city_tier1': ('bengaluru', 'bangalore', 'hyderabad', 'chennai', 'pune',
                   'gurugram', 'gurgaon', 'noida', 'mumbai', 'delhi',
                   'kolkata'),
    'city_tier2': ('coimbatore', 'kochi', 'indore', 'jaipur', 'ahmedabad',
                   'chandigarh', 'bhubaneswar', 'visakhapatnam', 'mysuru',
                   'nagpur', 'vadodara', 'thiruvananthapuram', 'lucknow',
                   'madurai', 'nashik', 'trichy'),
    'vendor': ('tcs', 'infosys', 'wipro', 'cognizant', 'capgemini',
               'accenture', 'hcl', 'tech mahindra', 'ltimindtree', 'genpact'),
    'nationality': ('india', 'indian'),
}


def _gcc_vocabulary():
    """The flat {keyword: weight} table Signal GCC advertises.

    Composed from the two axes so the vocabulary keeps exactly one home, as
    this module's docstring requires. The real scoring is _score_gcc below --
    this exists so anything reading KEYWORDS (app/intelligence/domains.py,
    the tests) sees the same terms.
    """
    vocab = dict(GCC_ENTITY)
    for weight, terms in GCC_ACTION.values():
        for term in terms:
            vocab.setdefault(term, weight)
    return vocab


KEYWORDS = {
    'Signal AI': {
        'generative ai': 4, 'genai': 4, 'artificial intelligence': 4,
        'machine learning': 4, 'deep learning': 4, 'large language model': 4,
        'llm': 4, 'agentic ai': 4,
        'openai': 3, 'anthropic': 3, 'chatgpt': 3, 'copilot': 3, 'gemini': 3,
        'robotics': 3, 'automation': 3, 'chatbot': 3, 'agentic': 3,
        'robotaxi': 3, 'driverless': 3, 'self-driving': 3,
        'ai-powered': 2, 'ai-driven': 2, 'neural': 2, 'robot': 2,
        'algorithm': 2, 'ai': 2, 'autonomous': 2, 'data center': 2,
        'data centers': 2, 'data centre': 2, 'nvidia': 2, 'xai': 3,
    },
    'Signal Business': {
        'ipo': 3, 'ipos': 3, 'merger': 3, 'mergers': 3, 'acquisition': 3,
        'acquisitions': 3, 'earnings': 3, 'm&a': 3, 'outstanding shares': 3,
        'stake sale': 3,
        'private equity': 3, 'venture capital': 3, 'takeover': 3, 'buyout': 3,
        'startup': 2, 'investment': 2, 'investor': 2, 'revenue': 2,
        'profit': 2, 'valuation': 2, 'stocks': 2, 'stock': 2, 'funding': 2,
        'shareholders': 2, 'fdi': 2,
        'market': 1, 'markets': 1, 'strategy': 1, 'growth': 1, 'capital': 1,
        'deal': 1, 'business': 1, 'shares': 1,
    },
    'Signal Global': {
        'geopolitical': 4, 'geopolitics': 4, 'energy security': 4,
        'trade war': 4, 'strait of hormuz': 4,
        'tariff': 3, 'tariffs': 3, 'sanctions': 3, 'nato': 3, 'ceasefire': 3,
        'diplomacy': 3, 'diplomatic': 3,
        'defence': 2, 'defense': 2, 'military': 2, 'war': 2, 'conflict': 2,
        'summit': 2, 'opec': 2, 'pentagon': 2, 'white house': 2,
        'g7': 2, 'g20': 2, 'election': 2, 'tensions': 1,
        'houthi': 3, 'red sea': 2,
        'trade': 1, 'oil': 1, 'border': 1, 'iran': 1, 'china': 1, 'russia': 1,
        'ukraine': 1, 'israel': 1, 'taiwan': 1, 'middle east': 1, 'gaza': 1,
        'palestine': 1,
        # Political/government leadership changes — a minister or head of
        # government resigning is geopolitical/domestic-policy news, not a
        # corporate "Signal Executive" story, so it lives here instead.
        'minister resigns': 4, 'resigns as minister': 4,
        'cabinet reshuffle': 4, 'steps down as minister': 3,
        'prime minister resigns': 4, 'pm resigns': 4,
        'cabinet minister': 2,
        'union minister': 1, 'chief minister': 1, 'prime minister': 1,
    },
    'Signal Insurance': {
        'reinsurance': 4, 'insurtech': 4, 'underwriting': 4, 'actuarial': 4,
        'policyholder': 4, 'policyholders': 4, 'cat bond': 4, 'cat bonds': 4,
        'catastrophe bond': 4, "workers' compensation": 4,
        'workers compensation': 4, 'cyber insurance': 4,
        'insurer': 3, 'insurers': 3, 'reinsurer': 3, 'annuity': 3, 'p&c': 3,
        'property and casualty': 3, 'life insurance': 3, 'health insurance': 3,
        'premiums': 3, 'underwriter': 3, 'underwriters': 3, 'actuary': 3,
        'am best': 3, 'cat modeling': 3, 'cat renewal': 3,
        'insurance': 2, 'premium': 2, 'broker': 2, 'brokers': 2,
        'brokerage': 2, 'coverage': 2, 'coverages': 2, "lloyd's": 2,
        'renewals': 2, 'cyber risk': 2, 'liability': 2, 'indemnity': 2,
        'claims': 1, 'policy': 1, 'risk': 1,
    },
    'Signal GCC': _gcc_vocabulary(),
    'Signal Executive': {
        # 'people moves' is a generic trade-press section header, not
        # evidence of a specific significant move — kept at medium weight
        # so it doesn't alone stack with routine keyword matches (appoints,
        # names, ceo) to outscore genuinely major single-story leadership news.
        'people moves': 2, 'c-suite': 4, 'boardroom': 4,
        'chief executive officer': 4, 'executive outlook': 4,
        'chief executive': 3, 'ceo': 3, 'ceos': 3, 'cfo': 3, 'cfos': 3,
        'cio': 3, 'coo': 3, 'cro': 3, 'cxo': 3, 'chief risk officer': 3,
        'chief financial officer': 3, 'succession': 3,
        'appoints': 2, 'appointed': 2, 'appointment': 2, 'hires': 2,
        'leadership': 2, 'board of directors': 2, 'managing director': 2,
        'step down': 2, 'steps down': 2, 'resigns': 2, 'welcomes': 2,
        'executive committee': 2,
        'board': 1, 'executive': 1, 'executives': 1, 'governance': 1,
        'names': 1,
    },
}

# Most specific first: on tied scores, the article lands in the earlier signal.
PRIORITY = ['Signal GCC', 'Signal Insurance', 'Signal AI',
            'Signal Global', 'Signal Executive', 'Signal Business']

THRESHOLD = 3        # minimum evidence to classify; below this: unclassified
# Per-signal minimum, where the shared THRESHOLD is too loose. GCC sits at 6
# because at 5 an IT-vendor services deal ("HCLTech bags AI-led IT
# transformation deal from M Group") clears both axes and reaches the tile --
# a supplier story, not a capability-centre one.
SIGNAL_FLOORS = {'Signal GCC': 6}
TITLE_MULTIPLIER = 2  # a keyword in the headline is worth double
MAX_PER_SIGNAL = 8

_COMPILED = {
    name: [(re.compile(r'\b' + re.escape(kw) + r'\b'), weight)
           for kw, weight in kws.items()]
    for name, kws in KEYWORDS.items()
}

# "GCC" next to Gulf-region terms means Gulf Cooperation Council, not
# Global Capability Centers — shift that evidence to Signal Global.
_GCC_TERM = re.compile(r'\bgccs?\b')
_GULF_CONTEXT = re.compile(
    r'\b(gulf|saudi|saudi arabia|uae|united arab emirates|qatar|bahrain'
    r'|kuwait|oman|dubai|abu dhabi)\b')
_GCC_TERM_WEIGHT = KEYWORDS['Signal GCC']['gcc']

_GCC_RX = {kw: re.compile(r'\b' + re.escape(kw) + r'\b')
           for kw in list(GCC_ENTITY)
           + [t for _, terms in GCC_ACTION.values() for t in terms]}


def gcc_axes(title, summary=''):
    """(has_entity, has_action) -- the two-axis gate, on normalised text.

    Public because app/intelligence/domains.py applies the same gate; the two
    classifiers share this one definition so they cannot disagree about what
    counts as a GCC story.
    """
    blob = _normalize(title or '') + ' ' + _normalize(summary or '')
    entity = any(_GCC_RX[k].search(blob) for k in GCC_ENTITY)
    action = any(_GCC_RX[t].search(blob)
                 for _, terms in GCC_ACTION.values() for t in terms)
    return entity, action


def _score_gcc(title, summary):
    """Signal GCC's score under the faceted rule; 0 when either axis is empty.

    Scored apart from the flat sum in score_signals because GCC needs facet
    semantics: every distinct ENTITY term counts, but an ACTION facet counts
    once however many of its synonyms fire. Both arguments arrive already
    normalised.
    """
    gulf = bool(_GULF_CONTEXT.search(title) or _GULF_CONTEXT.search(summary))

    entity_hits = total = 0
    for kw, weight in GCC_ENTITY.items():
        if gulf and kw in ('gcc', 'gccs'):
            continue          # Gulf Cooperation Council, not a capability centre
        rx = _GCC_RX[kw]
        if rx.search(title):
            entity_hits += 1
            total += weight * TITLE_MULTIPLIER
        elif summary and rx.search(summary):
            entity_hits += 1
            total += weight

    action_facets = 0
    for weight, terms in GCC_ACTION.values():
        where = None
        for term in terms:
            rx = _GCC_RX[term]
            if rx.search(title):
                where = 'title'
                break
            if where is None and summary and rx.search(summary):
                where = 'summary'
        if where:
            action_facets += 1
            total += weight * (TITLE_MULTIPLIER if where == 'title' else 1)

    if not entity_hits or not action_facets:
        return 0
    return total


def _normalize(text):
    """Lowercase and straighten curly quotes so keywords match consistently."""
    return text.lower().replace('’', "'").replace('‘', "'")


# Words too common in headlines to signal that two titles are the same story.
_STOPWORDS = {
    'a', 'an', 'the', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'as',
    'by', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 'be', 'been',
    'it', 'its', 'this', 'that', 'after', 'over', 'amid', 'into', 'from',
    'up', 'down', 'out', 'not', 'no', 'how', 'why', 'what', 'his', 'her',
    'new', 'says', 'said', 'sources', 'source', 'report', 'reports',
    'exclusive', 'update', 'jr', 'may', 'will', 'would', 'could',
}


def _title_tokens(title):
    """Meaningful-word set of a headline, for near-duplicate comparison."""
    words = re.findall(r"[a-z0-9']+", _normalize(title))
    words = [w[:-2] if w.endswith("'s") else w.rstrip("'") for w in words]
    return {w for w in words if w not in _STOPWORDS and len(w) > 1}


def _is_near_duplicate(tokens, kept_token_sets):
    """Same story retold: >=3 shared meaningful words covering >=50% of the
    shorter headline (e.g. two outlets on the same Zepto IPO repricing)."""
    for kept in kept_token_sets:
        shared = len(tokens & kept)
        if shared >= 3 and shared / max(1, min(len(tokens), len(kept))) >= 0.5:
            return True
    return False


def score_signals(title, summary=''):
    """Return {signal name: evidence score} for one article."""
    title = _normalize(title)
    summary = _normalize(summary)
    scores = {}
    for name, patterns in _COMPILED.items():
        total = 0
        for regex, weight in patterns:
            if regex.search(title):
                total += weight * TITLE_MULTIPLIER
            elif summary and regex.search(summary):
                total += weight
        scores[name] = total

    if _GULF_CONTEXT.search(title) or _GULF_CONTEXT.search(summary):
        # "GCC" beside Gulf terms is the Gulf Cooperation Council. The GCC
        # side of this is handled inside _score_gcc, which drops the term
        # before scoring; here we only move the evidence to Signal Global.
        if _GCC_TERM.search(title):
            scores['Signal Global'] += 2 * TITLE_MULTIPLIER
        elif summary and _GCC_TERM.search(summary):
            scores['Signal Global'] += 2

    # Signal GCC replaces its flat sum with the faceted, gated score. The
    # loop above cannot express "one facet counts once", nor refuse an
    # article that has plenty of evidence of the wrong kind.
    scores['Signal GCC'] = _score_gcc(title, summary)

    return scores


def classify_article(title, summary=''):
    """Return (signal name, score), or None when nothing clears its floor.

    Each signal is tested against its own floor before the winner is picked,
    rather than picking the winner and then testing it. Otherwise a signal
    carrying a higher floor could take the article on score and then fail its
    own bar, dropping an article another signal would have classified.
    """
    scores = score_signals(title, summary)
    eligible = [name for name in PRIORITY
                if scores[name] >= SIGNAL_FLOORS.get(name, THRESHOLD)]
    if not eligible:
        return None
    # max() keeps the first maximum, so PRIORITY still breaks ties.
    best = max(eligible, key=lambda name: scores[name])
    return best, scores[best]


def _display_date(data_date=None):
    """Render the DATA's date when we know it, else fall back to today.

    `data_date` is the ISO date stamped on instance/articles_cache.json.
    Callers that know it should pass it; the fallback keeps older callers
    working rather than crashing, but it is the behaviour that let a stale
    build claim to be current.
    """
    if data_date:
        try:
            return datetime.strptime(data_date, '%Y-%m-%d').strftime('%B %d, %Y')
        except (ValueError, TypeError):
            pass
    return datetime.now().strftime('%B %d, %Y')


def _is_current(article):
    """True when the article may be presented as today's intelligence."""
    return classify_freshness(parse_date(article.get('date'))).get('is_current', False)


def synthesize_signals(articles, data_date=None, require_current=True):
    """Group scraped articles under the six Signals, strongest evidence first.

    ``require_current`` applies the Sprint 3 freshness gate: anything older
    than config/freshness.yaml's archive_after_hours, or carrying no usable
    publication date, is excluded. Without it a feed that goes stale upstream
    (as moneycontrol.com did, serving April 2024 items under HTTP 200) puts
    multi-year-old stories on a page stamped with today's date.
    """
    seen_titles = set()
    grouped = {s['name']: [] for s in SIGNALS}
    unclassified = 0
    stale = 0
    for article in articles:
        title = article.get('title', '').strip()
        # Titles under 4 words are almost always scraped section headers
        # ("Industry News", "Mergers & Acquisitions"), not articles.
        if not title or len(title.split()) < 4 or title.lower() in seen_titles:
            continue
        seen_titles.add(title.lower())
        if require_current and not _is_current(article):
            stale += 1
            continue
        result = classify_article(title, article.get('summary', ''))
        if result is None:
            unclassified += 1
            continue
        name, score = result
        grouped[name].append({'title': title, 'url': article.get('url', ''),
                              'score': score})
    for name in grouped:
        grouped[name].sort(key=lambda a: a['score'], reverse=True)
        kept, kept_tokens = [], []
        for art in grouped[name]:
            tokens = _title_tokens(art['title'])
            if _is_near_duplicate(tokens, kept_tokens):
                continue  # same story, lower score — the bucket refills below
            kept.append(art)
            kept_tokens.append(tokens)
            if len(kept) == MAX_PER_SIGNAL:
                break
        grouped[name] = kept
    return {
        'date': _display_date(data_date),
        'data_date': data_date,          # ISO, or None when unknown
        'unclassified': unclassified,
        'stale_excluded': stale,
        'signals': [
            {
                'name': s['name'],
                'purpose': s['purpose'],
                'audience': s['audience'],
                'articles': grouped[s['name']],
            }
            for s in SIGNALS
        ],
    }
