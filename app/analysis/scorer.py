# app/analysis/scorer.py

from datetime import datetime, timedelta

# TODO: Implement a more sophisticated scoring engine.
# This could involve using NLP to analyze the article content.
# For now, we'll use a simple keyword-based approach.

# COMMENTED OUT AS OF DECEMBER 24, 2025 - SHIFTING TO INDUSTRY-WIDE INSURANCE INTELLIGENCE
# SCORING_KEYWORDS = {
#     'Macro & Geo-Political Signals': ['interest rate', 'bond yield', 'currency', 'geopolitical', 'trade sanctions', 'cross-border', 'economy', 'market', 'global', 'trade', 'policy', 'regulation', 'new', 'challenge', 'development', 'issue', 'crisis', 'trend', 'breaking', 'alert', 'urgent', 'opportunity', 'threat'],
#     'Regulatory & Compliance Signals': ['regulators', 'health insurance', 'solvency', 'capital', 'reporting', 'ESG', 'data privacy', 'AI regulation', 'compliance', 'regulation', 'policy', 'law', 'supervision', 'insurance', 'new', 'change', 'update', 'challenge', 'breaking', 'alert'],
#     'Economic & Market Signals': ['stock movements', 'credit rating', 'bond market', 'reinsurance pricing', 'investor sentiment', 'financial', 'capital', 'market', 'rating', 'reinsurance', 'volatility', 'crash', 'boom', 'new', 'development', 'challenge'],
#     'Digital, AI & Automation Signals': ['AI deployments', 'claims automation', 'underwriting', 'fraud', 'core system', 'cloud', 'platform', 'digital', 'AI', 'automation', 'tech', 'technology', 'innovation', 'new', 'challenge', 'development', 'disruption'],
#     'Operating Model & Talent Signals': ['GCC', 'offshoring', 'talent', 'layoffs', 'productivity', 'restructuring', 'operation', 'model', 'talent', 'hiring', 'challenge', 'issue', 'problem', 'new', 'trend', 'change'],
#     'MetLife-Specific Signals': ['MetLife', 'MetLife-specific', 'metlife', 'announcement', 'update', 'new'],
# }

# INSURANCE_KEYWORDS = ['insurance', 'insurer', 'reinsurance', 'MetLife', 'policy', 'claim', 'premium', 'underwriting', 'actuary', 'risk', 'coverage', 'liability', 'casualty', 'life insurance', 'health insurance', 'property insurance', 'auto insurance', 'home insurance', 'business insurance', 'insurtech', 'Lloyd\'s', 'AIG', 'Allstate', 'State Farm', 'Progressive', 'Geico', 'Nationwide', 'Farmers', 'Travelers', 'Chubb', 'Hartford', 'Prudential', 'New York Life', 'Northwestern Mutual', 'MassMutual', 'Guardian Life', 'Pacific Life', 'Voya', 'Lincoln Financial', 'Principal Financial', 'Unum', 'Genworth', 'Brighthouse Financial', 'Jackson National', 'CNO Financial', 'FGL Holdings', 'American Equity', 'Annuities', 'mutual fund', 'pension', 'annuity', 'retirement', 'employee benefits', 'workers compensation', 'disability insurance', 'long-term care', 'flood insurance', 'earthquake insurance', 'cyber insurance', 'terrorism insurance']

# def score_article(article):
#     """Score an article based on its content."""
#     # Relaxed for testing: no date filter, score all articles
#     scores = {category: 0 for category in SCORING_KEYWORDS}
    
#     title = article.get('title', '').lower()
#     summary = article.get('summary', '').lower()
#     content = title + ' ' + summary
    
#     # First, check if article is insurance-related
#     if not any(kw.lower() in content for kw in INSURANCE_KEYWORDS):
#         return {}, 0  # Exclude non-insurance articles
    
#     for category, keywords in SCORING_KEYWORDS.items():
#         for keyword in keywords:
#             if keyword.lower() in content:
#                 scores[category] += 1
    
#     total_score = sum(scores.values())
#     return scores, total_score

# NEW DESIGN: INDUSTRY-WIDE INSURANCE INTELLIGENCE

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

# 1️⃣ GEOGRAPHY-AWARE SCORING (WHERE DOES THIS MATTER?)
GEOGRAPHY_KEYWORDS = {
    'Global': {
        'global', 'worldwide', 'international', 'cross-border', 'multinational'
    },
    'North America': {
        'us', 'united states', 'canada', 'naic', 'sec', 'fed', 'treasury'
    },
    'Europe': {
        'eu', 'europe', 'european union', 'ecb', 'eiopa',
        'uk', 'fca', 'pra', 'boe'
    },
    'Asia-Pacific': {
        'apac', 'asia', 'china', 'india', 'japan', 'singapore',
        'mas', 'irdai', 'csrc', 'hkma'
    },
    'Middle East & Africa': {
        'mea', 'middle east', 'africa', 'uae', 'saudi', 'sama'
    },
    'Latin America': {
        'latam', 'brazil', 'mexico', 'chile', 'argentina'
    }
}

GEOGRAPHY_WEIGHTS = {
    'Global': 1.4,
    'North America': 1.3,
    'Europe': 1.3,
    'Asia-Pacific': 1.2,
    'Middle East & Africa': 1.1,
    'Latin America': 1.1,
    'Unspecified': 1.0
}

# 2️⃣ FALSE-POSITIVE SUPPRESSION
NOISE_KEYWORDS = {
    'opinion', 'thought leadership', 'podcast', 'webinar',
    'marketing', 'sponsored', 'press release',
    'announcement only', 'interview', 'brand story'
}

WEAK_SIGNAL_PHRASES = {
    'could impact', 'may affect', 'exploring', 'considering',
    'early stage', 'pilot', 'discussion underway'
}

# 3️⃣ LLM-BASED “WHY THIS MATTERS” NARRATIVE
WHY_THIS_MATTERS_PROMPT = """
You are a Chief of Staff to a global Insurance CXO.

Context:
- Primary Signal: {primary_signal}
- Geography: {geography}
- Urgency: {urgency}
- Article Title: {title}

Write a concise executive narrative answering:
1. Why this development matters to insurers
2. What risk or opportunity it creates
3. What leadership should monitor or decide next

Rules:
- No hype
- No future speculation
- Strategic tone
- Max 90 words
"""

# 5️⃣ FINAL SCORING ENGINE (PRODUCTION VERSION)
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

def detect_geography(text: str) -> dict:
    text = text.lower()
    geo_hits = {}

    for region, keywords in GEOGRAPHY_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in text)
        if hits > 0:
            geo_hits[region] = hits

    if not geo_hits:
        geo_hits['Unspecified'] = 1

    return geo_hits

def apply_geography_weight(scores: dict, geography: dict) -> tuple:
    dominant_region = max(geography.items(), key=lambda x: x[1])[0]
    geo_weight = GEOGRAPHY_WEIGHTS.get(dominant_region, 1.0)

    adjusted_scores = {
        k: round(v * geo_weight, 1)
        for k, v in scores.items()
    }

    return adjusted_scores, dominant_region

def suppress_false_positives(text: str, score_output: dict) -> bool:
    text = text.lower()

    noise_hits = sum(1 for kw in NOISE_KEYWORDS if kw in text)
    weak_hits = sum(1 for kw in WEAK_SIGNAL_PHRASES if kw in text)

    primary_score = score_output['Primary Signal'][1]

    # Suppress if:
    # 1) Low score AND
    # 2) Noise or weak language dominates
    if primary_score < 60 and (noise_hits > 0 or weak_hits > 1):
        return True

    return False

# 6️⃣ CXO SUMMARY (GENERIC, CLEAN)
def generate_cxo_summary(title: str, score_output: dict) -> str:
    primary, score = score_output['Primary Signal']
    urgency = "URGENT" if score_output['Urgency Flag'] else "Monitor"

    return (
        f"{primary} signal detected ({score}/100). "
        f"Relevance for Insurance leadership. Status: {urgency}."
    )

# 4️⃣ FINAL PIPELINE (END-TO-END FLOW)
def intelligence_pipeline(article_text, title, llm=None):
    scores = score_article(article_text)
    if not scores:
        return None

    geography_hits = detect_geography(article_text)
    adjusted_scores, region = apply_geography_weight(
        scores['All Scores'], geography_hits
    )

    scores['All Scores'] = adjusted_scores

    if suppress_false_positives(article_text, scores):
        return None

    narrative = ""
    if llm:
        primary_signal = scores['Primary Signal'][0]
        urgency = "High" if scores['Urgency Flag'] else "Moderate"

        prompt = WHY_THIS_MATTERS_PROMPT.format(
            primary_signal=primary_signal,
            geography=region,
            urgency=urgency,
            title=title
        )

        narrative = llm(prompt)

    return {
        'Title': title,
        'Primary Signal': scores['Primary Signal'],
        'Secondary Signals': scores['Secondary Signals'],
        'Geography': region,
        'Urgency': scores['Urgency Flag'],
        'Why This Matters': narrative
    }
