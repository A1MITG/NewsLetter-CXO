# app/analysis/scorer.py
"""Keyword-based relevance scoring for the legacy five-lens CXO brief.

Gates articles on an insurance-domain keyword match, scores them per lens
using weighted keyword hits plus an urgency-intensifier boost, then
normalizes to a 0-100 scale per lens.
"""

# 1️⃣ INSURANCE DOMAIN GATE (NEUTRAL)
INSURANCE_DOMAIN_KEYWORDS = {
    'insurance', 'insurer', 'reinsurance', 'policy', 'claim', 'premium',
    'underwriting', 'actuary', 'risk', 'coverage', 'liability',
    'life insurance', 'health insurance', 'property', 'casualty',
    'annuity', 'retirement', 'employee benefits', 'workers compensation',
    'cyber insurance', 'insurtech',
    'broker', 'carrier', 'underwriter', 'claims processing'
}

# 2️⃣ SIGNAL INTENSIFIERS (UNCHANGED, CROSS-CUTTING)
SIGNAL_INTENSIFIERS = {
    'breaking', 'alert', 'urgent', 'crisis', 'shock',
    'major', 'material', 'significant', 'first-ever',
    'penalty', 'lawsuit', 'ban', 'collapse'
}

# 3️⃣ CXO SIGNAL CATEGORIES (INSURANCE-WIDE)
SCORING_KEYWORDS = {
    'Macro & Geo-Political': {
        'interest rate', 'inflation', 'bond yield', 'currency',
        'geopolitical', 'sanctions', 'trade war',
        'cross-border', 'macroeconomic slowdown',
        'economy', 'market', 'global', 'trade', 'policy', 'regulation',
        'crisis', 'trend', 'breaking', 'alert', 'urgent', 'opportunity', 'threat'
    },
    'Regulatory & Compliance': {
        'regulator', 'supervisor', 'solvency',
        'capital adequacy', 'ifrs', 'esg',
        'data privacy', 'ai governance',
        'compliance breach', 'regulatory fine',
        'regulation', 'policy', 'law', 'supervision', 'compliance',
        'new', 'change', 'update', 'breach', 'fine', 'penalty'
    },
    'Economic & Market': {
        'credit rating', 'downgrade', 'upgrade',
        'reinsurance pricing', 'loss ratio',
        'combined ratio', 'capital markets volatility',
        'stock', 'bond', 'market', 'rating', 'reinsurance', 'volatility',
        'crash', 'boom', 'financial', 'capital'
    },
    'Digital, AI & Automation': {
        'artificial intelligence', 'genai', 'ai',
        'claims automation', 'fraud detection',
        'underwriting automation',
        'core system modernization', 'cloud migration',
        'digital', 'automation', 'tech', 'technology', 'innovation',
        'ai deployment', 'fraud', 'core system', 'cloud', 'platform'
    },
    'Operating Model & Talent': {
        'gcc', 'shared services', 'offshoring',
        'restructuring', 'layoffs',
        'talent shortage', 'productivity',
        'operating model redesign',
        'talent', 'hiring', 'layoff', 'restructure', 'productivity',
        'operation', 'model', 'leadership', 'change', 'people', 'move'
    }
}

# 4️⃣ WEIGHTING MODEL (CXO PRIORITY)
CATEGORY_WEIGHTS = {
    'Regulatory & Compliance': 1.5,
    'Macro & Geo-Political': 1.4,
    'Economic & Market': 1.3,
    'Digital, AI & Automation': 1.1,
    'Operating Model & Talent': 1.0
}

# 2️⃣ FINAL SCORING ENGINE
def score_article(article_text: str) -> dict:
    text = article_text.lower()

    # Step 1: Insurance relevance gate
    if not any(k in text for k in INSURANCE_DOMAIN_KEYWORDS):
        return {}

    raw_scores = {}
    weighted_scores = {}

    # Step 2: Category scoring
    for category, keywords in SCORING_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in text)
        if hits > 0:
            raw_scores[category] = hits
            weighted_scores[category] = hits * CATEGORY_WEIGHTS.get(category, 1)

    if not weighted_scores:
        return {}

    # Step 3: Signal intensifier boost
    intensifier_hits = sum(1 for kw in SIGNAL_INTENSIFIERS if kw in text)
    boost = 1 + (0.15 * intensifier_hits)

    for k in weighted_scores:
        weighted_scores[k] *= boost

    # Step 4: Normalize scores to 100
    max_score = max(weighted_scores.values())
    normalized_scores = {
        k: round((v / max_score) * 100, 1)
        for k, v in weighted_scores.items()
    }

    # Step 5: Rank signals
    ranked = sorted(
        normalized_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return {
        'Primary Signal': ranked[0],
        'Secondary Signals': ranked[1:3],
        'All Scores': normalized_scores,
        'Urgency Flag': intensifier_hits > 0
    }
