"""SIGNAL intelligence pipeline.

One scrape, one scoring pass, one canonical store. The Command Center and
the Signals newsletter are both projections of that store, so the two
surfaces cannot drift apart.

Sprint map (PRD section -> module):
    §1  Data Quality        schema.py, normalize.py     Sprint 1
    §2  Source Trust        trust.py                    Sprint 2
    §3  Freshness           freshness.py                Sprint 3
    §4  Domain Detection    domains.py                  Sprint 4
    §5  Entity Extraction   entities.py                 Sprint 5
    §6  Event Detection     events.py                   Sprint 6
    §7  Executive Impact    impact.py                   Sprint 7
    §8  Priority            priority.py                 Sprint 8
    §11 Explainability      explain.py                  Sprint 9
    §10 Developments        developments.py             Sprint 10
    §9  Newsletter content  newsletter.py (LLM)         Sprint 11
    §12 Recommendation      recommend.py                Sprint 12
"""
