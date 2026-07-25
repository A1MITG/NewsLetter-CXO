# app/analysis/synthesis.py
from .scorer import score_article
from datetime import datetime

CXO_MAPPING = {
    'Macro & Geo-Political': 'CEO',
    'Regulatory & Compliance': 'CRO',
    'Economic & Market': 'CFO',
    'Digital, AI & Automation': 'CIO',
    'Operating Model & Talent': 'COO'
}

def synthesize_articles(articles):
    """Synthesize articles into CXO Daily Intelligence Brief format."""
    
    # Filter and score articles
    scored_articles = []
    for article in articles:
        text = article['title'] + ' ' + article.get('summary', '')
        score_output = score_article(text)
        if score_output:
            primary_signal, primary_score = score_output['Primary Signal']
            article['scores'] = score_output['All Scores']
            article['total_score'] = primary_score
            article['primary_lens'] = primary_signal
            article['primary_cxo'] = CXO_MAPPING.get(primary_signal, 'CEO')
            scored_articles.append(article)
    
    # Sort by score descending
    scored_articles.sort(key=lambda x: x['total_score'], reverse=True)
    
    # Build the brief structure
    brief = {
        'date': datetime.now().strftime('%B %d, %Y'),
        'Macro & Geo-Political': [],
        'Regulatory & Compliance': [],
        'Economic & Market': [],
        'Digital, AI & Automation': [],
        'Operating Model & Talent': [],
        'executive_takeaway': generate_executive_takeaway(scored_articles),
        'cxo_action_lens': generate_cxo_action_lens(scored_articles)
    }
    
    # Categorize articles by lens
    for article in scored_articles[:30]:  # Limit to top 30
        category = article['primary_lens'] if article['primary_lens'] in CXO_MAPPING else 'Macro & Geo-Political'
        formatted = format_article_for_lens(article, category)
        if len(brief[category]) < 5:  # Max 5 per category
            brief[category].append(formatted)
    
    return brief

def trim_headline(text, limit):
    """Trim to a word boundary with an ellipsis instead of a mid-word cut."""
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(' ', 1)[0].rstrip(',;:—-') + '…'

def generate_executive_takeaway(articles):
    """Generate one-sentence executive takeaway."""
    if not articles:
        return "No material CXO-level developments in the last 24 hours."
    top = articles[0]
    return f"In the last 24 hours, the most material development for MetLife is \"{trim_headline(top['title'], 90)}\" because it impacts {top['primary_lens']}."

def generate_cxo_action_lens(articles):
    """Generate CXO action lens with Watch, Prepare, Act."""
    actions = []
    if articles:
        actions.append("Watch: Monitor emerging trends in " + articles[0]['primary_lens'])
        if len(articles) > 1:
            actions.append("Prepare: Assess impact of \"" + trim_headline(articles[1]['title'], 60) + "\"")
        if len(articles) > 2:
            actions.append("Act: Review implications of \"" + trim_headline(articles[2]['title'], 60) + "\"")
    return actions[:5]  # Max 5

def format_article_for_lens(article, category):
    """Format article for specific lens section."""
    signal = article['title']
    impact = f"Impacts {article['primary_lens'].lower()} considerations"
    metlife_exposure = f"Potential exposure for MetLife in {article['primary_cxo']} domain"
    return {
        'signal': signal,
        'impact': impact,
        'metlife_exposure': metlife_exposure,
        'url': article['url'],
        'score': article['total_score'],
        'primary_cxo': article['primary_cxo']
    }
