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
    'Signal GCC': {
        'global capability center': 4, 'global capability centre': 4,
        'global capability centers': 4, 'global capability centres': 4,
        'shared services': 4, 'nasscom': 4,
        'captive center': 3, 'captive centre': 3, 'offshoring': 3,
        'gcc': 3, 'gccs': 3,
        'outsourcing': 2, 'bengaluru': 2, 'bangalore': 2, 'hyderabad': 2,
        'gurugram': 2, 'gurgaon': 2, 'noida': 2, 'pune': 2,
        'tcs': 2, 'infosys': 2, 'wipro': 2, 'cognizant': 2, 'capgemini': 2,
        'accenture': 2, 'it services': 2,
        'india': 1, 'indian': 1,
    },
    'Signal Executive': {
        'people moves': 4, 'c-suite': 4, 'boardroom': 4,
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
        if _GCC_TERM.search(title):
            scores['Signal GCC'] -= _GCC_TERM_WEIGHT * TITLE_MULTIPLIER
            scores['Signal Global'] += 2 * TITLE_MULTIPLIER
        elif summary and _GCC_TERM.search(summary):
            scores['Signal GCC'] -= _GCC_TERM_WEIGHT
            scores['Signal Global'] += 2
        scores['Signal GCC'] = max(scores['Signal GCC'], 0)

    return scores


def classify_article(title, summary=''):
    """Return (signal name, score), or None when evidence is below THRESHOLD."""
    scores = score_signals(title, summary)
    best = max(PRIORITY, key=lambda name: scores[name])
    if scores[best] < THRESHOLD:
        return None
    return best, scores[best]


def synthesize_signals(articles):
    """Group scraped articles under the six Signals, strongest evidence first."""
    seen_titles = set()
    grouped = {s['name']: [] for s in SIGNALS}
    unclassified = 0
    for article in articles:
        title = article.get('title', '').strip()
        # Titles under 4 words are almost always scraped section headers
        # ("Industry News", "Mergers & Acquisitions"), not articles.
        if not title or len(title.split()) < 4 or title.lower() in seen_titles:
            continue
        seen_titles.add(title.lower())
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
        'date': datetime.now().strftime('%B %d, %Y'),
        'unclassified': unclassified,
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
