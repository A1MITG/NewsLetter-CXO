"""Propose new Signal GCC keywords from accumulated history.

Why this is not a word-frequency counter
----------------------------------------
Counting frequency is how the rubric broke in the first place. "noida" is
frequent in GCC stories -- and equally frequent in Indian business news that
has nothing to do with a capability centre. Frequency measures how often a
term appears; it cannot tell you whether the term is ABOUT the thing.

Two measures decide instead, and a candidate must clear both:

  LIFT          P(term | confirmed GCC) / P(term | everything else).
                How much more the term belongs to GCC stories than to news
                in general. A term that is merely common scores near 1.

  CO-OCCURRENCE Share of the term's GCC appearances that sit alongside a
                weight-4 ENTITY term. This is the "must direct to a GCC
                business" gate: it separates vocabulary that describes a
                capability centre from vocabulary that merely travels near
                one. "noida" fails here even in a GCC-heavy sample, because
                it appears in stories that never name a centre.

Nothing here activates a keyword. Candidates are written out with their
evidence for a person to promote into app/analysis/signals.py. The decisive
weight-4 tier is never proposed automatically -- naming what counts as a
capability centre stays a human judgement.

The same arithmetic run backwards flags DEMOTIONS: a live keyword whose lift
has decayed below the bar is one the corpus no longer supports. That is the
check that would have caught "noida" without anyone noticing it by hand.
"""
import json
import os
import re
from collections import Counter, defaultdict

from app.analysis.signals import GCC_ACTION, GCC_CONTEXT, GCC_ENTITY

# A candidate must appear in this many distinct confirmed GCC stories before
# its lift means anything. Below it the ratio is noise from one headline.
MIN_SUPPORT = 5
MIN_LIFT = 3.0
MIN_COOCCURRENCE = 0.6
# Share of case-preserved occurrences that must be capitalised before a term
# is treated as a proper noun. Place, company and person names are exactly
# what this module must never propose.
PROPER_NOUN_RATIO = 0.8

MAX_NGRAM = 3
SAMPLE_HEADLINES = 3

# Terms already spoken for: the live rubric, plus everything deliberately
# excluded from it. Re-proposing a term the rubric rejects on purpose would
# be the module arguing with its own design.
_CONTEXT_TERMS = {t for group in GCC_CONTEXT.values() for t in group}

_STOPWORDS = set("""
a an the of in on at to for with as by and or but is are was were be been being
it its this that these those after over amid into from up down out not no how
why what which who whom his her their our your we they them there here then than
more most much many such some any all both each other another same own very just
only also will would could should may might must can said says say report reports
new news year years month months day days time times first last next
""".split())


def _tokens(text):
    return re.findall(r"[a-z][a-z&'\-]+", text.lower())


def _ngrams(text, max_n=MAX_NGRAM):
    """1..n word grams, minus anything a stopword makes meaningless."""
    words = _tokens(text)
    out = set()
    for n in range(1, max_n + 1):
        for i in range(len(words) - n + 1):
            gram = words[i:i + n]
            if n == 1:
                if gram[0] in _STOPWORDS or len(gram[0]) < 4:
                    continue
            else:
                # A gram that is only stopwords carries nothing; one that
                # starts or ends on a stopword is usually a fragment.
                if gram[0] in _STOPWORDS or gram[-1] in _STOPWORDS:
                    continue
            out.add(" ".join(gram))
    return out


def _live_terms():
    """Every term the rubric currently scores, in one set."""
    terms = set(GCC_ENTITY)
    for _weight, action_terms in GCC_ACTION.values():
        terms.update(action_terms)
    return terms


def _decisive_terms():
    return {term for term, weight in GCC_ENTITY.items() if weight == 4}


# --------------------------------------------------------------------------
# History store
# --------------------------------------------------------------------------

def record_path(root):
    return os.path.join(root, 'instance', 'gcc_history.jsonl')


def record_day(articles, store, data_date, classify):
    """Append today's classified articles, skipping ones already stored.

    The daily cache holds a single slot and is overwritten on each scrape, so
    without this there is no history to measure lift against -- the pool is
    however many GCC stories happened to run today, which is typically one.

    Deduplicated on url: re-running a build, or a story carried by a feed for
    several days, must not inflate a term's support count.
    """
    seen = {r.get('url') for r in load_history(store)}
    added = 0
    with open(store, 'a', encoding='utf-8') as handle:
        for article in articles:
            url = (article.get('url') or '').strip()
            title = (article.get('title') or '').strip()
            if not title or (url and url in seen):
                continue
            result = classify(title, article.get('summary', '') or '')
            handle.write(json.dumps({
                'date': data_date,
                'url': url,
                'title': title,
                'summary': (article.get('summary') or '')[:600],
                'signal': result[0] if result else None,
                'score': result[1] if result else 0,
            }, ensure_ascii=False) + '\n')
            if url:
                seen.add(url)
            added += 1
    return added


def load_history(store):
    if not os.path.exists(store):
        return []
    records = []
    with open(store, encoding='utf-8') as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except ValueError:
                continue  # a partial write must not take the whole store down
    return records


# --------------------------------------------------------------------------
# Mining
# --------------------------------------------------------------------------

def _blob(record):
    return (record.get('title') or '') + ' ' + (record.get('summary') or '')


def _capitalisation(term, texts):
    """Share of this term's occurrences that are capitalised in the source.

    A cheap proper-noun test. Place names, companies and people are the exact
    class of term this module must not propose, and they are capitalised in
    running prose while ordinary vocabulary is not.
    """
    pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
    total = upper = 0
    for text in texts:
        for match in pattern.finditer(text):
            total += 1
            if match.group(0)[:1].isupper():
                upper += 1
    return (upper / total) if total else 0.0


def _weight_for(lift):
    """Lift band -> weight. Never 4: the decisive tier stays hand-curated."""
    if lift >= 8:
        return 3
    if lift >= 5:
        return 2
    return 1


def _facet_for(term, positives):
    """Which axis the candidate travels with most.

    A proposal is only useful if it says where the term belongs. Entity wins
    ties: a term that co-occurs with the centre itself is more likely to name
    one than to describe something being done to it.
    """
    pattern = re.compile(r'\b' + re.escape(term) + r'\b')
    tallies = Counter()
    for record in positives:
        text = _blob(record).lower()
        if not pattern.search(text):
            continue
        if any(re.search(r'\b' + re.escape(e) + r'\b', text) for e in _decisive_terms()):
            tallies['entity'] += 1
        for facet, (_weight, terms) in GCC_ACTION.items():
            if any(re.search(r'\b' + re.escape(t) + r'\b', text) for t in terms):
                tallies[facet] += 1
    if not tallies:
        return 'entity'
    best = max(tallies.values())
    if tallies.get('entity', 0) == best:
        return 'entity'
    return max(tallies, key=lambda k: tallies[k])


def mine(records, min_support=MIN_SUPPORT, min_lift=MIN_LIFT,
         min_cooccurrence=MIN_COOCCURRENCE):
    """-> (candidates, stats). Candidates are proposals, never activations."""
    positives = [r for r in records if r.get('signal') == 'Signal GCC']
    negatives = [r for r in records if r.get('signal') != 'Signal GCC']

    stats = {
        'records': len(records),
        'confirmed_gcc': len(positives),
        'rest': len(negatives),
        'min_support': min_support,
        'ready': len(positives) >= min_support,
    }
    if not stats['ready']:
        # Reporting a ranking off two articles would invite someone to act on
        # it. Say the pool is too small instead.
        return [], stats

    live = _live_terms() | _CONTEXT_TERMS
    decisive = _decisive_terms()

    pos_df, neg_df = Counter(), Counter()
    pos_grams = []
    for record in positives:
        grams = _ngrams(_blob(record))
        pos_grams.append(grams)
        pos_df.update(grams)
    for record in negatives:
        neg_df.update(_ngrams(_blob(record)))

    # co-occurrence with a decisive entity term, counted per candidate
    cooc = defaultdict(lambda: [0, 0])
    for record, grams in zip(positives, pos_grams):
        text = _blob(record).lower()
        has_decisive = any(re.search(r'\b' + re.escape(e) + r'\b', text)
                           for e in decisive)
        for gram in grams:
            cooc[gram][1] += 1
            if has_decisive:
                cooc[gram][0] += 1

    n_pos, n_neg = max(len(positives), 1), max(len(negatives), 1)
    pos_texts = [_blob(r) for r in positives]

    candidates = []
    for term, support in pos_df.items():
        if term in live or support < min_support:
            continue
        # +0.5 keeps a term absent from the negative pool finite rather than
        # infinite, so a single-corpus artefact cannot top the ranking.
        lift = (support / n_pos) / ((neg_df.get(term, 0) + 0.5) / n_neg)
        if lift < min_lift:
            continue
        hits, seen = cooc[term]
        rate = hits / max(seen, 1)
        if rate < min_cooccurrence:
            continue
        cap = _capitalisation(term, pos_texts)
        if cap >= PROPER_NOUN_RATIO:
            continue  # a place, a company or a person
        candidates.append({
            'term': term,
            'support': support,
            'lift': round(lift, 2),
            'cooccurrence': round(rate, 2),
            'capitalisation': round(cap, 2),
            'weight': _weight_for(lift),
            'facet': _facet_for(term, positives),
            'samples': [r['title'] for r, g in zip(positives, pos_grams)
                        if term in g][:SAMPLE_HEADLINES],
        })
    candidates.sort(key=lambda c: (-c['lift'], -c['support']))
    stats['candidates'] = len(candidates)
    return candidates, stats


def demotions(records, min_lift=MIN_LIFT, min_support=MIN_SUPPORT):
    """Live keywords the accumulated corpus no longer supports.

    The same test as mine(), run against terms already in the rubric. This is
    the automated form of the review that caught "noida" by hand: a term
    whose lift has fallen to around 1 is appearing just as often outside GCC
    stories as inside them, and is no longer discriminating anything.
    """
    positives = [r for r in records if r.get('signal') == 'Signal GCC']
    negatives = [r for r in records if r.get('signal') != 'Signal GCC']
    if len(positives) < min_support:
        return []

    n_pos, n_neg = max(len(positives), 1), max(len(negatives), 1)
    pos_texts = [_blob(r).lower() for r in positives]
    neg_texts = [_blob(r).lower() for r in negatives]

    flagged = []
    for term in sorted(_live_terms()):
        pattern = re.compile(r'\b' + re.escape(term) + r'\b')
        in_pos = sum(1 for t in pos_texts if pattern.search(t))
        in_neg = sum(1 for t in neg_texts if pattern.search(t))
        if in_pos + in_neg == 0:
            continue  # never fires either way; silence is not evidence against it
        lift = (in_pos / n_pos) / ((in_neg + 0.5) / n_neg)
        if lift < min_lift and in_neg >= min_support:
            flagged.append({'term': term, 'lift': round(lift, 2),
                            'in_gcc': in_pos, 'in_rest': in_neg})
    flagged.sort(key=lambda f: f['lift'])
    return flagged
