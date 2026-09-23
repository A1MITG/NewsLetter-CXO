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

# Domains that exist only as Command Center tiles. The Signals page keeps the
# six above, and classifies exactly as before: these join the competition for
# an article only when a caller passes include_tile_signals=True. Added one
# at a time, each replacing a "coming soon" tile.
TILE_SIGNALS = [
    {'name': 'Signal Banking', 'purpose': 'Banks · Lending · Payments · Central Banks',
     'audience': 'BFSI'},
    {'name': 'Signal Energy', 'purpose': 'Oil & Gas · Power · Renewables · Energy Policy',
     'audience': 'Energy & Infrastructure'},
    {'name': 'Signal Defence', 'purpose': 'Armed Forces · Weapons · Defence Industry · Security',
     'audience': 'Defence & Policy'},
    {'name': 'Signal Healthcare', 'purpose': 'Hospitals · Pharma · Medtech · Public Health',
     'audience': 'Healthcare & Life Sciences'},
    {'name': 'Signal Cyber', 'purpose': 'Cyber Attacks · Data Breaches · Security Industry · Data Protection',
     'audience': 'CISO & Risk'},
]
_TILE_NAMES = {s['name'] for s in TILE_SIGNALS}

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
    # Tile-only (see TILE_SIGNALS). Weights follow the other signals' scale
    # (4 decisive, 3 strong, 2 medium, 1 weak). Reviewed 2026-09-23 against
    # the live scan: the headline must also name Banking (TITLE_REQUIRED), so
    # a bank that only appears in a summary — as a deal's broker, say — can
    # add weight but never qualify a story on its own.
    'Signal Banking': {
        # The business of banking
        'nbfc': 4, 'nbfcs': 4, 'non-performing assets': 4, 'npa': 4, 'npas': 4,
        'gross npa': 4, 'net npa': 4, 'bad loans': 4, 'stressed assets': 4,
        'asset quality': 4, 'net interest margin': 4, 'net interest income': 4,
        'credit growth': 4, 'deposit growth': 4, 'capital adequacy': 4,
        'bad bank': 4, 'narcl': 4, 'basel': 4, 'neobank': 4, 'payments bank': 4,
        'small finance bank': 4, 'microfinance': 4, 'digital lending': 4,
        'housing finance': 4, 'gold loan': 4, 'gold loans': 4,
        'priority sector lending': 4, 'cooperative bank': 4, 'co-operative bank': 4,
        'public sector bank': 4, 'public sector banks': 4,
        'private sector bank': 4, 'private sector banks': 4, 'banking sector': 4,
        'deposit insurance': 4, 'dicgc': 4, 'bank run': 4, 'jan dhan': 4,
        'banking': 3, 'banker': 3, 'bankers': 3, 'lender': 3, 'lenders': 3,
        'psb': 3, 'psbs': 3, 'casa ratio': 4, 'casa deposits': 4,
        'fixed deposit': 3, 'fixed deposits': 3, 'loan emi': 3,
        'fd rates': 3, 'credit card': 3, 'mortgage': 3, 'mortgages': 3,
        'home loan': 3, 'buy now pay later': 3, 'bnpl': 3, 'fintech': 3,
        'kyc': 3, 'money laundering': 3, 'financial inclusion': 3, 'cibil': 3,
        'bank': 2, 'banks': 2, 'loan': 2, 'loans': 2, 'lending': 2,
        'deposit': 2, 'deposits': 2, 'liquidity': 2,
        'credit score': 2, 'remittances': 2,
        'credit': 1,
        # Central banks and monetary policy
        'monetary policy committee': 4, 'repo rate': 4, 'mclr': 4, 'vrrr': 4,
        'rbi governor': 4,
        'rbi': 3, 'reserve bank': 3, 'central bank': 3, 'federal reserve': 3,
        'monetary policy': 3, 'rate cut': 3, 'rate hike': 3,
        'european central bank': 3, 'bank of england': 3, 'bank of japan': 3,
        "people's bank of china": 3,
        'interest rate': 2, 'interest rates': 2,
        # Payment systems
        'npci': 4, 'payment aggregator': 4, 'cbdc': 4, 'digital rupee': 4,
        'e-rupee': 4,
        'upi': 3, 'rtgs': 3, 'neft': 3, 'imps': 3, 'rupay': 3,
        'payments': 2,
        # Banks by name. A name in a headline is strong evidence (3); the
        # pure investment banks sit at 2, because their headlines are as
        # often a market call ("Goldman sees Nifty at ...") as banking news.
        # India
        'sbi': 3, 'state bank of india': 3, 'hdfc bank': 3, 'icici bank': 3,
        'axis bank': 3, 'kotak mahindra bank': 3, 'kotak bank': 3,
        'pnb': 3, 'punjab national bank': 3, 'bank of baroda': 3,
        'canara bank': 3, 'union bank of india': 3, 'bank of india': 3,
        'indian bank': 3, 'indusind bank': 3, 'idbi bank': 3, 'yes bank': 3,
        'idfc first bank': 3, 'federal bank': 3, 'bandhan bank': 3,
        'au small finance bank': 3, 'rbl bank': 3,
        # United States
        'jpmorgan': 3, 'jpmorgan chase': 3, 'jpmorganchase': 3,
        'bank of america': 3, 'citigroup': 3, 'citibank': 3, 'citi': 2,
        'wells fargo': 3, 'us bancorp': 3, 'u.s. bancorp': 3, 'pnc': 3,
        'truist': 3, 'capital one': 3, 'bny mellon': 3,
        'bank of new york mellon': 3,
        'goldman sachs': 2, 'morgan stanley': 2,
        # Europe and the UK
        'hsbc': 3, 'barclays': 3, 'bnp paribas': 3, 'credit agricole': 3,
        'crédit agricole': 3, 'santander': 3, 'societe generale': 3,
        'société générale': 3, 'deutsche bank': 3, 'commerzbank': 3,
        'ubs': 3, 'credit suisse': 3, 'ing group': 3, 'ing bank': 3,
        'unicredit': 3, 'intesa sanpaolo': 3, 'bbva': 3, 'natwest': 3,
        'lloyds bank': 3, 'lloyds banking group': 3, 'standard chartered': 3,
        'nordea': 3,
        # Asia-Pacific, Middle East, Canada
        'icbc': 3, 'china construction bank': 3, 'agricultural bank of china': 3,
        'bank of china': 3, 'mufg': 3, 'mitsubishi ufj': 3, 'smbc': 3,
        'sumitomo mitsui': 3, 'mizuho': 3, 'dbs bank': 3, 'dbs group': 3,
        'ocbc': 3, 'uob': 3, 'emirates nbd': 3, 'first abu dhabi bank': 3,
        'qnb': 3, 'royal bank of canada': 3, 'td bank': 3, 'commonwealth bank': 3,
    },
    # Tile-only. First draft 2026-09-23, built with the Banking review's
    # lessons from the start: the headline must name it (TITLE_REQUIRED),
    # everyday senses of its words are blanked (NEUTRALIZE), and companies
    # appear only in unambiguous forms ("Shell plc", not "Shell"; "BP plc",
    # not "BP", which is also basis points).
    'Signal Energy': {
        # Oil and gas
        'crude oil': 4, 'oil prices': 4, 'oil price': 4, 'brent': 4, 'wti': 4,
        'opec': 4, 'lng': 4, 'natural gas': 4, 'refinery': 4, 'refineries': 4,
        'oilfield': 4, 'oil and gas': 4, 'oil & gas': 4, 'petroleum': 4,
        'gas pipeline': 4, 'oil pipeline': 4, 'fuel prices': 4, 'fuel price': 4,
        'jet fuel': 4, 'omc': 4, 'omcs': 4, 'oil marketing companies': 4,
        'city gas': 4, 'cbg': 4, 'ethanol blending': 4, 'biofuel': 4, 'biofuels': 4,
        'crude': 3, 'barrel': 3, 'barrels': 3, 'upstream': 3, 'downstream': 3,
        'gas prices': 3, 'gas supply': 3, 'petrol': 3, 'diesel': 3,
        'gasoline': 3, 'lpg': 3, 'cng': 3, 'ethanol': 3,
        'oil': 2, 'fuel': 2,
        'gas': 1,
        # Power
        'power sector': 4, 'power plant': 4, 'power plants': 4,
        'power generation': 4, 'power demand': 4, 'power grid': 4,
        'power prices': 4, 'power tariff': 4, 'power outage': 4,
        'load shedding': 4, 'discom': 4, 'discoms': 4, 'electricity prices': 4,
        'grid operator': 4, 'energy storage': 4, 'battery storage': 4,
        'thermal power': 4, 'hydropower': 4, 'hydroelectric': 4,
        'electricity': 3, 'blackout': 3, 'transmission line': 3,
        'megawatt': 3, 'gigawatt': 3,
        'mw': 2, 'gw': 2,
        # Renewables and nuclear
        'renewable energy': 4, 'solar power': 4, 'solar energy': 4,
        'wind power': 4, 'wind energy': 4, 'offshore wind': 4, 'wind farm': 4,
        'wind turbine': 4, 'green hydrogen': 4, 'nuclear power': 4,
        'nuclear plant': 4, 'nuclear reactor': 4, 'nuclear energy': 4,
        'small modular reactor': 4, 'coal mine': 4,
        'renewables': 3, 'solar': 3, 'hydrogen': 3, 'coal': 3,
        # Policy and markets
        'energy security': 4, 'energy transition': 4, 'energy policy': 4,
        'energy prices': 4, 'energy ministry': 4, 'energy minister': 4,
        'energy crisis': 4,
        'energy': 2,
        # Companies, unambiguous forms only
        'saudi aramco': 4, 'aramco': 4, 'exxonmobil': 4, 'exxon': 4,
        'chevron': 4, 'shell plc': 4, 'royal dutch shell': 4,
        'totalenergies': 4, 'bp plc': 4, 'conocophillips': 4, 'equinor': 4,
        'petrobras': 4, 'adnoc': 4, 'qatarenergy': 4, 'gazprom': 4,
        'rosneft': 4, 'nextera': 4, 'ongc': 4, 'indian oil': 4, 'iocl': 4,
        'bpcl': 4, 'hpcl': 4, 'gail': 4, 'ntpc': 4, 'coal india': 4,
        'power grid corporation': 4, 'nhpc': 4, 'tata power': 4,
        'adani green': 4, 'adani power': 4, 'jsw energy': 4, 'oil india': 4,
    },
    # Tile-only. First draft 2026-09-23, same review rules as Energy. Takes
    # its stories mostly from Signal Global, which keeps diplomacy,
    # ceasefires and "war" in general; Defence is armed forces, weapons and
    # the defence industry. Companies in unambiguous forms only ("Dassault
    # Aviation", not the software maker; "Hindustan Aeronautics", not "HAL").
    'Signal Defence': {
        # Institutions and people
        'defence ministry': 4, 'ministry of defence': 4, 'defense department': 4,
        'department of defense': 4, 'pentagon': 4, 'armed forces': 4,
        'air force': 4, 'defence minister': 4, 'defense minister': 4,
        'defence secretary': 4, 'defense secretary': 4, 'secretary of defense': 4,
        'army chief': 4, 'navy chief': 4, 'air chief': 4, 'coast guard': 4,
        'military': 3, 'army': 3, 'navy': 3, 'naval': 3, 'troops': 3,
        'soldiers': 3, 'nato': 3, 'paramilitary': 3,
        'bsf': 3, 'crpf': 3,
        # Operations and conflict
        'military exercise': 4, 'military drills': 4, 'war games': 4,
        'military operation': 4, 'military aid': 4, 'military base': 4,
        'military bases': 4, 'airstrike': 4, 'airstrikes': 4, 'air strike': 4,
        'drone strike': 4, 'drone strikes': 4, 'border clash': 4,
        'airspace': 3, 'militants': 3, 'insurgents': 3, 'counter-terrorism': 3,
        # Weapons and platforms
        'missile': 4, 'missiles': 4, 'ballistic': 4, 'hypersonic': 4,
        'fighter jet': 4, 'fighter jets': 4, 'warship': 4, 'warships': 4,
        'submarine': 4, 'submarines': 4, 'aircraft carrier': 4, 'frigate': 4,
        'artillery': 4, 'howitzer': 4, 'ammunition': 4, 'battle tank': 4,
        'nuclear weapons': 4, 'nuclear warhead': 4, 'nuclear arsenal': 4,
        'missile defence': 4, 'air defence': 4, 'air defense': 4, 'iron dome': 4,
        'rafale': 4, 'f-35': 4, 'sukhoi': 4, 'tejas': 4, 'brahmos': 4,
        's-400': 4, 'himars': 4, 'mq-9': 4,
        'weapons': 3, 'weapon': 3,
        # Bare "defence" and "drone" are weak on purpose: with the floor of
        # 5 (SIGNAL_FLOORS) neither qualifies a headline alone, because
        # "Chelsea's defence holds firm" and a delivery drone are not news
        # about armed forces.
        'defence': 2, 'defense': 2, 'drone': 2, 'drones': 2,
        # Budgets, trade and industry
        'defence budget': 4, 'defense budget': 4, 'defence spending': 4,
        'defense spending': 4, 'defence exports': 4, 'defence procurement': 4,
        'defence deal': 4, 'defense contract': 4, 'arms deal': 4, 'arms sales': 4,
        'arms exports': 4, 'defence stocks': 4, 'defense stocks': 4,
        'drdo': 4, 'hindustan aeronautics': 4, 'bharat electronics': 4,
        'mazagon dock': 4, 'lockheed martin': 4, 'lockheed': 4, 'raytheon': 4,
        'northrop grumman': 4, 'general dynamics': 4, 'bae systems': 4,
        'rheinmetall': 4, 'dassault aviation': 4, 'elbit': 4,
        'israel aerospace industries': 4, 'mbda': 4, 'hanwha aerospace': 4,
        'cochin shipyard': 3, 'thales': 3, 'saab': 3, 'kongsberg': 3,
    },
    # Tile-only. First draft 2026-09-23, same review rules as Defence.
    # Health insurance stays with Insurance, so health insurers
    # (UnitedHealth, Humana, Aetna, Cigna) are left out. Names in unambiguous
    # forms only: "World Health Organization", not "WHO" (the word "who");
    # "European Medicines Agency", not "EMA"; "Eli Lilly", not "Lilly";
    # "Abbott Laboratories", not "Abbott".
    'Signal Healthcare': {
        # Industry
        'healthcare': 4, 'health care': 4, 'pharmaceutical': 4,
        'pharmaceuticals': 4, 'drugmaker': 4, 'drugmakers': 4, 'biotech': 4,
        'biotechnology': 4, 'medtech': 4, 'healthtech': 4, 'medical device': 4,
        'medical devices': 4, 'generic drugs': 4, 'biosimilar': 4,
        'biosimilars': 4, 'cdmo': 4, 'telemedicine': 4,
        'pharma': 3, 'generics': 3, 'diagnostics': 3,
        # Regulators, ministries and public programmes
        'fda': 4, 'usfda': 4, 'cdsco': 4, 'dcgi': 4, 'european medicines agency': 4,
        'world health organization': 4, 'world health organisation': 4,
        'tedros': 4, 'health ministry': 4, 'ministry of health': 4,
        'health minister': 4, 'health secretary': 4, 'hhs': 4,
        'health and human services': 4, 'nih': 4, 'icmr': 4, 'aiims': 4,
        'national medical commission': 4, 'nhs': 4, 'ayushman bharat': 4,
        'public health': 4, 'medicaid': 4,
        'cdc': 3, 'medicare': 3,
        # Care delivery
        'hospital': 3, 'hospitals': 3, 'doctors': 3, 'nurses': 3, 'surgery': 3,
        'health system': 3,
        # Bare "medical", "drug", "patients" and "clinic" are weak on purpose:
        # with the floor of 5 (SIGNAL_FLOORS) none qualifies a headline alone
        # ("medical AI" is an AI story, "unpaid comp medical bills" an
        # insurance one).
        'medical': 2, 'patient': 2, 'patients': 2, 'clinic': 2, 'clinics': 2,
        'drug': 2, 'drugs': 2,
        # Medicines and research
        'clinical trial': 4, 'clinical trials': 4, 'drug approval': 4,
        'vaccine': 4, 'vaccines': 4, 'vaccination': 4, 'gene therapy': 4,
        'cell therapy': 4, 'oncology': 4, 'obesity drug': 4,
        'weight-loss drug': 4, 'glp-1': 4, 'ozempic': 4, 'wegovy': 4,
        'mounjaro': 4,
        'medicine': 3, 'medicines': 3, 'therapy': 3, 'cancer': 3, 'diabetes': 3,
        'insulin': 3, 'antibiotic': 3, 'antibiotics': 3,
        # Public health
        'pandemic': 4, 'covid': 4, 'dengue': 4, 'malaria': 4, 'tuberculosis': 4,
        'measles': 4, 'mpox': 4, 'h5n1': 4, 'bird flu': 4, 'nipah': 4,
        'cholera': 4, 'mental health': 4,
        'outbreak': 3, 'epidemic': 3, 'virus': 3, 'infection': 3,
        'infections': 3, 'disease': 3, 'diseases': 3, 'life expectancy': 3,
        # Companies: India
        'sun pharma': 4, 'sun pharmaceutical': 4, 'dr reddy': 4, 'dr. reddy': 4,
        'cipla': 4, 'lupin': 4, 'aurobindo pharma': 4, 'zydus': 4, 'glenmark': 4,
        'biocon': 4, "divi's": 4, 'torrent pharma': 4, 'alkem': 4,
        'mankind pharma': 4, 'syngene': 4, 'serum institute': 4,
        'bharat biotech': 4, 'apollo hospitals': 4, 'fortis healthcare': 4,
        'max healthcare': 4, 'narayana health': 4,
        # Companies: global
        'pfizer': 4, 'moderna': 4, 'johnson & johnson': 4, 'j&j': 4, 'merck': 4,
        'novartis': 4, 'roche': 4, 'astrazeneca': 4, 'sanofi': 4, 'gsk': 4,
        'glaxosmithkline': 4, 'eli lilly': 4, 'novo nordisk': 4, 'abbvie': 4,
        'bristol myers': 4, 'bristol-myers': 4, 'amgen': 4, 'gilead': 4,
        'regeneron': 4, 'takeda': 4, 'teva': 4, 'medtronic': 4,
        'abbott laboratories': 4, 'siemens healthineers': 4, 'ge healthcare': 4,
        'philips healthcare': 4,
        'bayer': 3,
    },
    # Tile-only. First draft 2026-09-23, same review rules as Defence. Cyber
    # insurance stays with Insurance (see NEUTRALIZE). Takes its stories
    # mostly from AI, where "AI-powered cybersecurity" used to land.
    'Signal Cyber': {
        # Core
        'cybersecurity': 4, 'cyber security': 4, 'cyber-security': 4,
        'cyberattack': 4, 'cyberattacks': 4, 'cyber attack': 4, 'cyber attacks': 4,
        'cyber-attack': 4, 'cyber-attacks': 4, 'cybercrime': 4, 'cyber crime': 4,
        'cybercriminals': 4, 'cyber threat': 4, 'cyber threats': 4,
        'cyber espionage': 4, 'cyber warfare': 4, 'cyberwar': 4,
        'cyber defence': 4, 'cyber defense': 4, 'cyber fraud': 4, 'cyber cell': 4,
        'cyber police': 4, 'cyber': 3,
        # Attacks and threats
        'ransomware': 4, 'malware': 4, 'spyware': 4, 'phishing': 4, 'infostealer': 4,
        'botnet': 4, 'ddos': 4, 'zero-day': 4, 'computer virus': 4,
        'data breach': 4, 'data breaches': 4, 'security breach': 4, 'data leak': 4,
        'data leaks': 4, 'stolen data': 4, 'security flaw': 4, 'security flaws': 4,
        'security vulnerability': 4, 'bug bounty': 4, 'identity theft': 4,
        'sim swap': 4, 'online fraud': 4, 'digital fraud': 4, 'upi fraud': 4,
        'digital arrest': 4,
        'hackers': 4, 'hacker': 4, 'hacked': 4, 'hacking': 3, 'scammers': 3,
        'deepfake': 3, 'deepfakes': 3, 'encryption': 3, 'firewall': 3,
        # Weak on purpose: with the floor of 5 (SIGNAL_FLOORS) none qualifies
        # a headline alone ("Meta leans into AI amid privacy pushback" is an
        # AI story; "breach" and "scam" have everyday senses).
        'hack': 2, 'breach': 2, 'vulnerability': 2, 'vulnerabilities': 2,
        'scam': 2, 'scams': 2, 'privacy': 2, 'surveillance': 2, 'password': 2,
        'passwords': 2, 'trojan': 2,
        # Data protection and agencies
        'data protection': 4, 'data privacy': 4, 'dpdp': 4, 'gdpr': 4,
        'cert-in': 4, 'cisa': 4, 'ncsc': 4, 'nciipc': 4, 'i4c': 4,
        # Threat groups
        'lockbit': 4, 'lazarus group': 4, 'scattered spider': 4, 'shinyhunters': 4,
        'salt typhoon': 4, 'volt typhoon': 4, 'nso group': 4, 'pegasus spyware': 4,
        # Companies, unambiguous forms only ("Palo Alto Networks", not the
        # city; no "Wiz" or "Tenable", which are ordinary words)
        'crowdstrike': 4, 'palo alto networks': 4, 'zscaler': 4, 'fortinet': 4,
        'check point software': 4, 'sentinelone': 4, 'okta': 4, 'mandiant': 4,
        'darktrace': 4, 'rapid7': 4, 'proofpoint': 4, 'kaspersky': 4, 'sophos': 4,
        'trellix': 4, 'quick heal': 4, 'cloudflare': 3,
    },
}

# Signals whose headline must itself carry one of their keywords. A summary
# can add weight but cannot qualify a story alone: in the 2026-09-23 scan
# "home loan" deep in a summary put an online-safety story in Banking, and
# Goldman Sachs and Citigroup named as brokers put a Meesho stake sale there.
TITLE_REQUIRED = {'Signal Banking', 'Signal Energy', 'Signal Defence',
                  'Signal Healthcare', 'Signal Cyber'}

# Phrases that contain a signal's keyword but are not about that signal. They
# are blanked out of the text before that signal (and only that signal) is
# scored: "West Bank" is geopolitics, "food bank" is charity, "gold deposits"
# are geology — none of them is banking.
NEUTRALIZE = {
    'Signal Banking': re.compile(
        r"\b(?:west bank|world bank|food banks?|blood banks?|sperm banks?|seed banks?|"
        r"piggy banks?|river ?banks?|memory banks?|data banks?|power banks?|"
        r"(?:gold|mineral|lithium|oil|gas|copper|coal|rare earth) deposits?|"
        # "banks on" as a verb: "Snapdeal banks on Gen Z".
        # Not "banks on strike" or "banks on Sunday", which are banking news.
        r"(?:banks?|banking) on\b(?! (?:strike|holiday|alert|notice|monday|tuesday|"
        r"wednesday|thursday|friday|saturday|sunday))|"
        # Insurers, fund houses and brokers that carry a bank's name belong
        # with Insurance or markets, not Banking. Longest names first, so
        # "icici prudential amc" is blanked whole.
        r"sbi life|sbi general|sbi mutual fund|sbi funds management|sbi cards?|"
        r"hdfc life|hdfc ergo|hdfc amc|hdfc mutual fund|hdfc securities|"
        r"icici prudential(?: amc| life| mutual fund)?|icici lombard|icici securities|"
        r"kotak life|kotak general|kotak mahindra amc|kotak securities|"
        r"axis max life|axis mutual fund|axis securities|bajaj allianz|"
        r"lloyd's(?: of london)?)\b"
    ),
    # Everyday senses of Energy's words: kitchen oils, weapons, politics.
    # Greenhouse gas belongs with Climate; nuclear weapons with Defence.
    'Signal Energy': re.compile(
        r"\b(?:(?:cooking|edible|palm|olive|vegetable|essential|coconut|mustard|"
        r"castor|fish) oils?|oil paint(?:ing)?s?|oilseeds?|tear gas|"
        r"greenhouse gas(?:es)?|gas chambers?|laughing gas|"
        r"nuclear (?:weapons?|warheads?|missiles?|arsenal|bombs?|tests?|deal|"
        r"talks|programme|program|threat)|shell compan(?:y|ies)|"
        r"solar (?:system|eclipse|flares?)|energy drinks?|energy levels?|"
        r"power banks?|superpowers?|powerhouses?)\b"
    ),
    # Sport, law and metaphor; veterans' personal stories; and cyber defence,
    # which belongs to the Cyber tile.
    'Signal Defence': re.compile(
        r"\b(?:(?:title|world cup|trophy|championship|league|his|her|their|its) defen[cs]e|"
        r"defen[cs]e (?:lawyers?|counsel|attorneys?|team|solicitor|case)|self-defen[cs]e|"
        r"in defen[cs]e of|public defenders?|army of|salvation army|navy blue|old navy|"
        r"air force one|secret weapons?|cyber ?defen[cs]e|"
        r"(?:army|navy|military|air force|marine|war) veterans?)\b"
    ),
    # Health insurance and COVID insurance claims belong to Insurance ("Judge
    # rules for Sompo unit in COVID cover fight" reached the draft tile); drug
    # crime to Global; computer viruses to Cyber; "financial health" and
    # "pandemic-era" loans to Business; and metaphors to nobody.
    'Signal Healthcare': re.compile(
        r"\b(?:health (?:insurance|insurers?|cover(?:age)?|plans?)|mediclaim|medicare advantage|"
        r"covid(?:-19)? (?:cover|insurance|claims?|business interruption|losses|polic(?:y|ies))|"
        r"drugs?[- ](?:trafficking|traffickers?|cartels?|busts?|lords?|smuggling|smugglers?|"
        r"seizures?|seized|peddlers?|peddling|mules?|haul|rackets?|raids?|dealers?|dealing|"
        r"money|cases?|syndicates?)|war on drugs|"
        r"computer virus(?:es)?|"
        r"(?:outbreak|epidemic) of (?:violence|fighting|war|protests|clashes|hostilities|"
        r"fraud|layoffs|scams?)|"
        r"(?:financial|economic|fiscal|corporate|market|balance[- ]sheet) health|"
        r"health of the (?:economy|market|company)|"
        r"(?:post|pre)[- ](?:pandemic|covid)|(?:pandemic|covid)[- ](?:era|lows?|highs?|levels?|"
        r"peaks?|boom|recovery|stimulus|loans?|relief)|"
        r"spin doctors?|retail therapy|nurses (?:a|an|the|his|her|its|their|hopes|"
        r"ambitions?|grudges?|wounds?))\b"
    ),
    # Cyber insurance (cover, underwriting, claims, cat bonds) belongs to
    # Insurance; the rest is everyday usage.
    'Signal Cyber': re.compile(
        r"\b(?:cyber(?:[- ]?security)? (?:insurance|insurers?|cover(?:age)?|polic(?:y|ies)|"
        r"underwriting|underwriters?|reinsurance|premiums?|claims?|market|pricing|losses|"
        r"cat(?:astrophe)?(?: bonds?)?)|cyber risks? (?:insurance|cover|pricing|models?|"
        r"modell?ing|underwriting|transfer)|cyber monday|"
        r"life ?hacks?|growth hack(?:s|ing|ers?)?|"
        r"breach(?:es|ed)? of (?:contract|trust|duty|promise|privilege|ceasefire|covenants?|"
        r"conduct|code|the peace|rules)|trojan horse)\b"
    ),
}

# Most specific first: on tied scores, the article lands in the earlier signal.
# Tile-only domains sit after the audience's core (GCC, Insurance) and ahead
# of the broad signals, so a banking story on a tie lands in Banking rather
# than Business.
PRIORITY = ['Signal GCC', 'Signal Insurance', 'Signal Banking', 'Signal Energy',
            'Signal Defence', 'Signal Healthcare', 'Signal Cyber', 'Signal AI',
            'Signal Global', 'Signal Executive', 'Signal Business']

THRESHOLD = 3        # minimum evidence to classify; below this: unclassified
# Per-signal minimum, where the shared THRESHOLD is too loose. GCC sits at 6
# because at 5 an IT-vendor services deal ("HCLTech bags AI-led IT
# transformation deal from M Group") clears both axes and reaches the tile --
# a supplier story, not a capability-centre one.
# Defence sits at 5 so that a bare "defence" or "drone" in a headline (2 x 2 =
# 4) cannot qualify alone, while one strong term there (military, troops,
# missile: 3 x 2 = 6) still can.
# Healthcare and Cyber sit at 5 for the same reason: "medical" or "privacy"
# alone in a headline is not enough, "hospital" or "hackers" is.
SIGNAL_FLOORS = {'Signal GCC': 6, 'Signal Defence': 5, 'Signal Healthcare': 5,
                 'Signal Cyber': 5}
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
        t, s = title, summary
        blank = NEUTRALIZE.get(name)
        if blank:
            t, s = blank.sub(' ', t), blank.sub(' ', s)
        total, in_title = 0, False
        for regex, weight in patterns:
            if regex.search(t):
                total += weight * TITLE_MULTIPLIER
                in_title = True
            elif s and regex.search(s):
                total += weight
        scores[name] = total if in_title or name not in TITLE_REQUIRED else 0

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


def classify_article(title, summary='', include_tile_signals=False):
    """Return (signal name, score), or None when nothing clears its floor.

    Each signal is tested against its own floor before the winner is picked,
    rather than picking the winner and then testing it. Otherwise a signal
    carrying a higher floor could take the article on score and then fail its
    own bar, dropping an article another signal would have classified.

    Tile-only signals (TILE_SIGNALS) compete only when include_tile_signals is
    set, so the Signals page's six classify exactly as they did before.
    """
    scores = score_signals(title, summary)
    eligible = [name for name in PRIORITY
                if (include_tile_signals or name not in _TILE_NAMES)
                and scores[name] >= SIGNAL_FLOORS.get(name, THRESHOLD)]
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


def synthesize_signals(articles, data_date=None, require_current=True, include_tile_signals=False):
    """Group scraped articles under the six Signals, strongest evidence first.

    ``require_current`` applies the Sprint 3 freshness gate: anything older
    than config/freshness.yaml's archive_after_hours, or carrying no usable
    publication date, is excluded. Without it a feed that goes stale upstream
    (as moneycontrol.com did, serving April 2024 items under HTTP 200) puts
    multi-year-old stories on a page stamped with today's date.

    ``include_tile_signals`` adds the Command Center's tile-only domains
    (TILE_SIGNALS) to both the competition and the result. The Signals page
    leaves it off and keeps its six.
    """
    listed = SIGNALS + (TILE_SIGNALS if include_tile_signals else [])
    seen_titles = set()
    grouped = {s['name']: [] for s in listed}
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
        result = classify_article(title, article.get('summary', ''), include_tile_signals)
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
            for s in listed
        ],
    }
