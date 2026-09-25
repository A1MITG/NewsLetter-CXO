# app/analysis/gcc_rubric.py
"""Signal GCC: is this story about a Global Capability Centre?

Every other Signal is a flat keyword sum (app/analysis/signals.py). GCC is
not, because the words around a capability centre -- Indian cities, IT
vendors, "India" itself -- surround most Indian business news, and the same
three letters are also the Gulf Cooperation Council. Two live defects came
from a flat sum:

    "Indian art auction market triples"      -> india(1) + indian(1)    = 3
    "Puravankara ... Greater Noida project"  -> noida(2) + gurugram(2)  = 6

What those stories lack is not the AMOUNT of evidence but the KIND. So a GCC
story needs both of two things:

    ENTITY   it names a capability centre           (section 1)
    FACET    it says what is happening to one       (section 2)

The file reads top to bottom:

    1. ENTITY         the names of a capability centre
    2. FACETS         what a story about one turns on, by the India GCC
                      taxonomy: New GCC, Expansion, Leadership, Capability,
                      Sector, Talent, Policy, Real estate, Consolidation
    3. NOT EVIDENCE   cities, vendors, nationality: never scored
    4. GULF           when "GCC" means the Gulf Cooperation Council
    5. SCORING        score_gcc(), gcc_axes(), gcc_branches(), gcc_vocabulary()

How a story is scored
---------------------
  * Each ENTITY term found adds its points: 4 names a centre outright, 2 is
    the operating model around one ('outsourcing', 'shared services').
  * Each FACET found adds its weight ONCE, however many of its terms fire,
    so restating one event ("opens", "opening", "to open") cannot inflate.
  * A term in the headline counts double (signals.TITLE_MULTIPLIER).
  * No entity, or no facet: 0. The Signal needs MIN_SCORE.

Two kinds of facet
------------------
EVENT facets ("opens", "expands", "hires") count beside any entity term.
TOPIC facets (leadership, capability, sector, policy, ...) describe a story
ABOUT a centre rather than an event at one, and would fire on most business
news, so each counts only beside a NAMED centre (NAMED_CENTRE: a GCC, a
global capability centre, an engineering or R&D centre), never beside
supporting terms such as 'it services'. That keeps an IT supplier's AI deal
off the GCC tile. And a centre's own name is not evidence of its work:
'engineering' in "engineering centre" is blanked before topic facets look.

Changing the rubric
-------------------
  * A new name for a capability centre: ENTITY (and NAMED_CENTRE if it
    names an in-house centre unambiguously).
  * A new kind of GCC story: a term in the right FACETS entry, or a new
    Facet with its taxonomy branch. Never a city, vendor or nationality.
  * Candidates can be mined from history: scripts/mine_gcc_keywords.py.
  * Tests: tests/test_gcc_rubric.py follows the same five sections.
"""
import re
from dataclasses import dataclass

from ..intelligence.normalize import normalize_text

# The score a story needs. 6, not 3: at 5 an IT-vendor services deal
# ("HCLTech bags AI-led IT transformation deal from M Group") cleared both
# axes and reached the tile -- a supplier story, not a capability-centre one.
MIN_SCORE = 6


# ═════════════════════════════════════════════════════════════════════════════
# 1. ENTITY -- does the story name a capability centre?
# ═════════════════════════════════════════════════════════════════════════════

ENTITY = {
    # 4: names a capability centre outright.
    'gcc': 4, 'gccs': 4,
    'global capability center': 4, 'global capability centre': 4,
    'global capability centers': 4, 'global capability centres': 4,
    'global capability': 4,
    'capability center': 4, 'capability centre': 4,
    'capability centers': 4, 'capability centres': 4,
    'global in-house center': 4, 'global in-house centre': 4, 'gic': 4,
    'captive center': 4, 'captive centre': 4, 'captive unit': 4,
    'shared services center': 4, 'shared services centre': 4,
    'global business services': 4, 'gbs': 4,
    'global delivery center': 4, 'global delivery centre': 4, 'gdc': 4,
    'offshore development center': 4, 'offshore development centre': 4, 'odc': 4,
    'center of excellence': 4, 'centre of excellence': 4, 'coe': 4,
    'delivery center': 4, 'delivery centre': 4,
    'competency center': 4, 'competency centre': 4,
    'development center': 4, 'development centre': 4,
    'innovation center': 4, 'innovation centre': 4,
    'technology center': 4, 'technology centre': 4,
    # Engineering capability centres. Plurals are listed because matching is
    # word-bounded: 'engineering centre' does not match "engineering centres".
    'engineering center': 4, 'engineering centre': 4,
    'engineering centers': 4, 'engineering centres': 4, 'engineering hub': 4,
    'r&d center': 4, 'r&d centre': 4, 'r&d centers': 4, 'r&d centres': 4, 'r&d hub': 4,
    'er&d center': 4, 'er&d centre': 4, 'er&d centers': 4, 'er&d centres': 4,
    'research and development center': 4,
    # 2: the operating model around a centre, not the centre itself.
    'shared services': 2, 'offshoring': 2, 'nearshoring': 2, 'reshoring': 2,
    'outsourcing': 2, 'it services': 2, 'ites': 2, 'bpo': 2, 'kpo': 2,
    'back office': 2, 'in-house center': 2, 'in-house centre': 2,
    'managed services': 2, 'nasscom': 2, 'global mandate': 2, 'global roles': 2,
    # Bare 'captive' is deliberately absent: in this corpus it is far more
    # often a CAPTIVE INSURER ("Allianz names captive leader") than a captive
    # centre, and Signal Insurance is the right home for those.
}

# The names of an in-house centre, which TOPIC facets need beside them. Left
# out: names suppliers, universities and funds use as often as capability
# centres do ('delivery centre', 'global delivery centre', 'coe', 'gic',
# 'innovation centre', ...), and every supporting (2-point) term.
NAMED_CENTRE = (
    'gcc', 'gccs',
    'global capability center', 'global capability centre',
    'global capability centers', 'global capability centres', 'global capability',
    'capability center', 'capability centre', 'capability centers', 'capability centres',
    'global in-house center', 'global in-house centre',
    'captive center', 'captive centre', 'captive unit',
    'shared services center', 'shared services centre',
    'engineering center', 'engineering centre', 'engineering centers', 'engineering centres',
    'engineering hub', 'r&d center', 'r&d centre', 'r&d centers', 'r&d centres', 'r&d hub',
    'er&d center', 'er&d centre', 'er&d centers', 'er&d centres',
    'research and development center',
)


# ═════════════════════════════════════════════════════════════════════════════
# 2. FACETS -- what is the story about? (the India GCC taxonomy)
# ═════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Facet:
    """One kind of GCC story. Adds its weight once, however many terms fire."""
    branch: str        # the taxonomy branch it belongs to
    weight: int
    terms: tuple
    topic: bool = False  # True: counts only beside a NAMED_CENTRE


NEW_GCC, EXPANSION, LEADERSHIP, CAPABILITY = 'New GCC', 'Expansion', 'Leadership', 'Capability'
SECTOR, TALENT, POLICY, REAL_ESTATE, CONSOLIDATION = (
    'Sector', 'Talent', 'Policy', 'Real estate', 'Consolidation')

# Taxonomy branches in reading order, for gcc_branches().
BRANCHES = (NEW_GCC, EXPANSION, LEADERSHIP, CAPABILITY, SECTOR, TALENT, POLICY,
            REAL_ESTATE, CONSOLIDATION)

FACETS = {
    # ── New GCC: a new centre, a new company in India, a new city ──────────
    'new_build': Facet(NEW_GCC, 3, (
        'sets up', 'set up', 'setting up', 'to set up', 'establishes',
        'established', 'establishing', 'establish', 'opens', 'opened',
        'opening', 'to open', 'launches', 'launched', 'launching', 'launch',
        'inaugurates', 'inaugurated', 'unveils', 'unveiled', 'stands up',
        'stood up', 'commissions', 'greenfield', 'new center', 'new centre',
        'first center', 'first centre', 'debuts', 'breaks ground')),
    'new_location': Facet(NEW_GCC, 3, (
        'new city', 'new cities', 'new location', 'new locations', 'second city',
        'tier-2', 'tier 2', 'tier-ii', 'tier ii', 'tier-3', 'tier 3',
        'emerging cities', 'non-metro', 'relocates', 'relocating', 'relocation',
        'new home'), topic=True),

    # ── Expansion: hiring, investment, capacity, new functions ─────────────
    'expansion': Facet(EXPANSION, 3, (
        'expands', 'expanded', 'expanding', 'expansion', 'expand',
        'scales up', 'scaling up', 'scale-up', 'ramps up', 'ramping up',
        'ramp-up', 'doubles', 'doubling', 'tripling', 'adds capacity',
        'adding capacity', 'second campus', 'new campus', 'grows headcount',
        'widens', 'broadens', 'enlarges', 'deepens', 'upgrades',
        'extends charter', 'expands mandate', 'expanded mandate')),
    'augment_capability': Facet(EXPANSION, 3, (
        'augment', 'augments', 'augmenting', 'augmentation', 'absorbs',
        'take over', 'takes over', 'taking over', 'transitions',
        'transitioning', 'transition', 'migrates', 'migrating', 'migration',
        'insources', 'insourcing', 'in-sourcing', 'consolidates',
        'consolidating', 'consolidation', 'lift and shift',
        'brings in-house', 'moves in-house')),
    'talent_scale': Facet(EXPANSION, 2, (
        'hire', 'hires', 'hiring', 'to hire', 'headcount', 'seats',
        'workforce', 'ftes', 'professionals', 'engineers', 'recruit',
        'recruiting', 'roles', 'jobs', 'positions')),
    'investment': Facet(EXPANSION, 3, (
        'invest', 'invests', 'invested', 'investing', 'investment', 'investments',
        'crore', 'capex', 'outlay', 'commits', 'pumps', 'infuses', 'allocates',
        'million', 'billion'), topic=True),

    # ── Leadership: GCC heads, CIOs and CTOs, executive moves ──────────────
    # (Not 'to lead': "firms overtake banks to lead India's GCC boom".)
    'leadership': Facet(LEADERSHIP, 3, (
        'appoints', 'appointed', 'appointment', 'names', 'named', 'elevates',
        'elevated', 'promotes', 'promoted', 'joins', 'joined',
        'to head', 'head', 'heads', 'site leader', 'site head', 'centre head',
        'center head', 'country head', 'managing director', 'ceo', 'cio', 'cto',
        'chro', 'cfo', 'coo', 'chief executive', 'leader', 'leaders',
        'leadership', 'steps down', 'succeeds'), topic=True),

    # ── Capability: AI, engineering, R&D, product, data, cybersecurity ─────
    'coe_standup': Facet(CAPABILITY, 4, (
        'center of excellence', 'centre of excellence', 'coe',
        'hub for', 'center for', 'centre for')),
    'new_development': Facet(CAPABILITY, 3, (
        'product development', 'product engineering', 'new product',
        'end-to-end ownership', 'full stack ownership', 'product ownership',
        'charter expansion', 'digital transformation', 'platform build',
        'greenfield build', 'from scratch', 'ground up', 'r&d mandate')),
    'capability': Facet(CAPABILITY, 3, (
        'ai', 'genai', 'gen ai', 'generative ai', 'agentic', 'artificial intelligence',
        'machine learning', 'automation', 'data', 'analytics', 'cloud',
        'cybersecurity', 'cyber', 'engineering', 'er&d', 'r&d', 'research',
        'innovation', 'product', 'products', 'platform', 'platforms', 'software',
        'digital'), topic=True),

    # ── Sector: the industry a centre serves ───────────────────────────────
    'sector': Facet(SECTOR, 3, (
        'manufacturing', 'manufacturer', 'manufacturers', 'industrial',
        'automotive', 'automaker', 'automakers', 'aerospace', 'semiconductor',
        'semiconductors', 'chipmaker', 'chipmakers', 'banking', 'bank', 'banks',
        'bfsi', 'financial services', 'fintech', 'insurance', 'insurer',
        'insurers', 'healthcare', 'pharma', 'pharmaceutical', 'life sciences',
        'retail', 'retailer', 'retailers', 'consumer', 'fmcg', 'telecom',
        'energy', 'utilities', 'transport', 'logistics', 'professional services'),
        topic=True),

    # ── Talent: skills, pay, attrition (hiring volume is talent_scale) ─────
    'talent': Facet(TALENT, 3, (
        'talent', 'skills', 'skilling', 'reskilling', 'upskilling', 'attrition',
        'salary', 'salaries', 'compensation', 'freshers', 'graduates',
        'women', 'diversity'), topic=True),

    # ── Policy: central government, state incentives, education ───────────
    # (Not bare 'infrastructure': "data infrastructure" is not policy. Office
    # parks are Real estate.)
    'policy': Facet(POLICY, 3, (
        'policy', 'policies', 'incentive', 'incentives', 'subsidy', 'subsidies',
        'government', 'govt', 'state government', 'central government',
        'ministry', 'minister', 'chief minister', 'meity', 'scheme', 'mou',
        'memorandum of understanding', 'cabinet', 'budget', 'tax', 'regulation',
        'regulatory', 'sez', 'special economic zone', 'single window',
        'university', 'universities', 'academia', 'iit', 'iiit', 'education'),
        topic=True),

    # ── Real estate: offices and leasing ───────────────────────────────────
    'real_estate': Facet(REAL_ESTATE, 3, (
        'lease', 'leases', 'leased', 'leasing', 'office space', 'office spaces',
        'sq ft', 'sq. ft', 'square feet', 'square foot', 'msf', 'grade a',
        'real estate', 'tech park', 'it park', 'business park', 'co-working',
        'coworking', 'flex space', 'absorption'), topic=True),

    # ── Consolidation: closures, cuts, sales and acquisitions ─────────────
    'consolidation': Facet(CONSOLIDATION, 3, (
        'shuts', 'shut down', 'shutting', 'closes', 'closing', 'closure',
        'exits', 'exit', 'winds down', 'wind down', 'scales down', 'downsizes',
        'downsizing', 'layoffs', 'lays off', 'job cuts', 'cuts', 'trims', 'trim',
        'divests', 'divestment', 'sells', 'acquires', 'acquired', 'acquisition',
        'buys', 'buying', 'stake', 'merger', 'merges', 'build-operate-transfer',
        'build operate transfer', 'carve-out', 'carve out', 'spin off',
        'spins off'), topic=True),
}

# ═════════════════════════════════════════════════════════════════════════════
# 3. NOT EVIDENCE -- words that must never classify a story alone
# ═════════════════════════════════════════════════════════════════════════════
# Scores nothing. Listed so the exclusion is explicit and reviewable rather
# than an absence someone re-adds in good faith next year.
#
# Geography is deliberately not evidence at any weight. Tier-2 cities now
# court the same investment as Bengaluru and Hyderabad, so "GCC cities" is
# widening toward "Indian cities": a longer city list makes things worse. The
# cities do one job: telling a capability centre from the Gulf bloc (4).

NOT_EVIDENCE = {
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


# ═════════════════════════════════════════════════════════════════════════════
# 4. GULF -- when "GCC" means the Gulf Cooperation Council
# ═════════════════════════════════════════════════════════════════════════════
# Then 'gcc' is not a capability centre: it scores nothing here and its
# evidence moves to Signal Global (signals.score_signals).
#
#   1. The bloc named outright, or GCC used as a bloc of states ("GCC
#      countries", "GCC secretary-general", "India-GCC FTA"): always Gulf.
#   2. Gulf places, or trade-bloc words (FTA, trade talks, remittances):
#      Gulf -- unless the story also says plainly that it means a centre
#      ("global capability centre", "opens GCC in Chennai", "its GCC",
#      "India's GCCs"). A Dubai bank opening a GCC in Chennai is a GCC story.
#   3. Neither: a capability centre.
# "GCC summit" and "GCC leaders" are left out of (1): India's capability
# centres hold summits and have leaders too.

GCC_TERM = re.compile(r'\bgccs?\b')

_SEP = r'\s*[-–—/]\s*'  # "India-GCC", "India – GCC", "India/GCC"
_PARTNERS = r'(?:india|uk|eu|us|china|japan|asean|pakistan|korea)'

_GULF_BLOC = re.compile(
    r'\bgulf cooperation council\b'
    r'|\bgcc (?:countries|country|nations|states|member states|members|region|'
    r'regional|economies|bloc|secretariat|secretary[- ]general|ministers?|'
    r'ministerial|citizens|nationals|residents|visas?|railway|rail|investors|'
    r'sovereign)\b'
    rf'|\b{_PARTNERS}{_SEP}gccs?\b|\bgccs?{_SEP}{_PARTNERS}\b')

_GULF_WORDS = re.compile(
    r'\b(?:gulf|saudi|saudi arabia|uae|united arab emirates|emirates|emirati|'
    r'qatar|qatari|bahrain|bahraini|kuwait|kuwaiti|oman|omani|dubai|abu dhabi|'
    r'sharjah|riyadh|jeddah|doha|muscat|manama|middle east|mena|arab|arabian|'
    r'fta|free trade|trade pact|trade deal|trade talks|trade agreement|'
    r'trade negotiations|bilateral trade|remittances?|expatriates?|expats?)\b')

_CITIES = '|'.join(NOT_EVIDENCE['city_tier1'] + NOT_EVIDENCE['city_tier2'])
_CENTRE_SENSE = re.compile(
    r'\b(?:global capability|capability cent(?:er|re)s?|global in-house|'
    r'captive (?:cent(?:er|re)|unit))\b'
    rf"|\bgccs? in (?:india|{_CITIES})\b|\b(?:{_CITIES})(?:-based)? gccs?\b"
    r"|\b(?:india's|indian|its|their|own|new|first|second) gccs?\b")


def gcc_means_gulf(text):
    """True when "GCC" in this text is the Gulf Cooperation Council."""
    text = normalize_text(text)
    if _GULF_BLOC.search(text):
        return True
    if not GCC_TERM.search(text):
        return False
    return bool(_GULF_WORDS.search(text)) and not _CENTRE_SENSE.search(text)


# ═════════════════════════════════════════════════════════════════════════════
# 5. SCORING
# ═════════════════════════════════════════════════════════════════════════════

_RX = {term: re.compile(r'\b' + re.escape(term) + r'\b')
       for term in {*ENTITY, *NAMED_CENTRE, *(t for f in FACETS.values() for t in f.terms)}}

# Every entity name, longest first: blanked before topic facets look, so a
# centre's own name ("engineering centre") is not evidence of its work.
_ENTITY_ANY = re.compile(
    r'\b(?:' + '|'.join(re.escape(t) for t in sorted(ENTITY, key=len, reverse=True)) + r')\b')

_GULF_SENSE_ONLY = ('gcc', 'gccs')  # what the Gulf reading takes away


def _where(terms, title, summary):
    """'title' if any term is in the headline, else 'summary' if in it, else None."""
    if any(_RX[t].search(title) for t in terms):
        return 'title'
    if summary and any(_RX[t].search(summary) for t in terms):
        return 'summary'
    return None


def _facets(title, summary, gulf):
    """{facet name: 'title' | 'summary'} for every facet this story shows."""
    names_a_centre = _where([t for t in NAMED_CENTRE
                             if not (gulf and t in _GULF_SENSE_ONLY)], title, summary)
    bare_title, bare_summary = _ENTITY_ANY.sub(' ', title), _ENTITY_ANY.sub(' ', summary)
    found = {}
    for name, facet in FACETS.items():
        if facet.topic:
            where = names_a_centre and _where(facet.terms, bare_title, bare_summary)
        else:
            where = _where(facet.terms, title, summary)
        if where:
            found[name] = where
    return found


def _normal(title, summary):
    return normalize_text(title or ''), normalize_text(summary or '')


def score_gcc(title, summary, headline_weight):
    """Signal GCC's score for one story; 0 unless it has both axes."""
    title, summary = _normal(title, summary)
    gulf = gcc_means_gulf(f'{title} {summary}')
    multiplier = {'title': headline_weight, 'summary': 1}

    entity_hits, total = 0, 0
    for term, points in ENTITY.items():
        if gulf and term in _GULF_SENSE_ONLY:
            continue
        where = _where((term,), title, summary)
        if where:
            entity_hits += 1
            total += points * multiplier[where]

    facets = _facets(title, summary, gulf)
    if not entity_hits or not facets:
        return 0
    return total + sum(FACETS[name].weight * multiplier[where] for name, where in facets.items())


def gcc_axes(title, summary=''):
    """(names a centre, shows a facet): the two-axis gate.

    app/intelligence/domains.py applies the same gate, from this definition,
    so the two classifiers cannot disagree about what counts as a GCC story.
    """
    title, summary = _normal(title, summary)
    gulf = gcc_means_gulf(f'{title} {summary}')
    entity = _where([t for t in ENTITY if not (gulf and t in _GULF_SENSE_ONLY)], title, summary)
    return bool(entity), bool(_facets(title, summary, gulf))


def gcc_branches(title, summary=''):
    """The taxonomy branches a GCC story touches, in BRANCHES order."""
    title, summary = _normal(title, summary)
    hit = {FACETS[name].branch for name in _facets(title, summary, gcc_means_gulf(f'{title} {summary}'))}
    return [b for b in BRANCHES if b in hit]


def gcc_vocabulary():
    """Every term Signal GCC scores, as a flat {term: points} table.

    For anything that reads signals.KEYWORDS (app/intelligence/domains.py, the
    keyword miner, the tests). The real scoring is score_gcc(): a flat sum of
    this table would reopen every defect this file exists to prevent.
    """
    vocab = dict(ENTITY)
    for facet in FACETS.values():
        for term in facet.terms:
            vocab.setdefault(term, facet.weight)
    return vocab
