"""The page must never present stale articles as today's intelligence.

Regression cover for the moneycontrol.com incident: that feed returned
HTTP 200 while frozen at April 2024, and three 880-day-old articles reached
the front page under today's date.
"""
import json
import unittest
from datetime import date, datetime, timedelta, timezone

from app.analysis.command_center import build_engine_data
from app.analysis.signals import synthesize_signals
from app.intelligence.freshness import classify
from app.intelligence.normalize import parse_date
from app.main import create_app

OLD = "Tue, 23 Apr 2024 18:51:45 +0530"


def _rss(dt):
    return dt.strftime('%a, %d %b %Y %H:%M:%S +0000')


class TestFreshnessGate(unittest.TestCase):

    def _article(self, title, when):
        return {'title': title, 'url': 'https://example.com/x',
                'summary': 'insurance regulatory compliance market',
                'date': when}

    def test_multi_year_old_article_is_excluded(self):
        arts = [self._article('Tata Elxsi Q4 net profit revenue decline', OLD)]
        out = synthesize_signals(arts)
        shown = [a for s in out['signals'] for a in s['articles']]
        self.assertEqual(shown, [])
        self.assertEqual(out['stale_excluded'], 1)

    def test_recent_article_survives_the_gate(self):
        recent = _rss(datetime.now(timezone.utc) - timedelta(hours=3))
        arts = [self._article('Global insurance regulator issues new solvency rules', recent)]
        out = synthesize_signals(arts)
        shown = [a for s in out['signals'] for a in s['articles']]
        self.assertEqual(len(shown), 1)
        self.assertEqual(out['stale_excluded'], 0)

    def test_undated_article_is_excluded(self):
        """config/freshness.yaml sets treat_as_current: false."""
        arts = [self._article('People on the move in the insurance industry', None)]
        out = synthesize_signals(arts)
        self.assertEqual([a for s in out['signals'] for a in s['articles']], [])
        self.assertEqual(out['stale_excluded'], 1)

    def test_gate_can_be_disabled_for_analysis(self):
        arts = [self._article('Tata Elxsi Q4 net profit revenue decline', OLD)]
        out = synthesize_signals(arts, require_current=False)
        self.assertEqual(out['stale_excluded'], 0)

    def test_boundary_is_the_configured_archive_threshold(self):
        inside = _rss(datetime.now(timezone.utc) - timedelta(hours=167))
        outside = _rss(datetime.now(timezone.utc) - timedelta(hours=169))
        self.assertTrue(classify(parse_date(inside))['is_current'])
        self.assertFalse(classify(parse_date(outside))['is_current'])


class TestLivePageIsCurrent(unittest.TestCase):
    """End-to-end against the real corpus."""

    @classmethod
    def setUpClass(cls):
        cls.payload = create_app().test_client() \
            .get('/api/command-center').get_json()

    def test_no_stale_article_reaches_any_tile(self):
        for engine_id, engine in self.payload.items():
            if engine_id.startswith('_') or engine.get('comingSoon'):
                continue
            for article in engine['articles']:
                self.assertTrue(article['title'].strip())

    def test_meta_reports_freshness(self):
        meta = self.payload.get('_meta')
        self.assertIsNotNone(meta, "page cannot state how fresh it is")
        self.assertIn('fetched_minutes_ago', meta)
        self.assertIn('stale_excluded', meta)

    def test_meta_is_not_treated_as_an_engine(self):
        """_meta must never render as a tile."""
        self.assertNotIn('articles', self.payload['_meta'])


class TestDeadFeedIsGone(unittest.TestCase):

    def test_moneycontrol_feeds_are_not_configured(self):
        """Every moneycontrol RSS feed is frozen upstream (2024, one at 2016)."""
        from app.scraper import sources
        text = json.dumps({k: v for k, v in vars(sources).items()
                           if not k.startswith('_') and isinstance(v, dict)})
        self.assertNotIn('moneycontrol', text)


if __name__ == '__main__':
    unittest.main()


class TestHeroCardsAreLive(unittest.TestCase):
    """The lead row under "Global Situational Awareness".

    It was three hardcoded <a> cards with base64 images, so it stayed frozen
    on July 2026 stories while the live tiles below it moved on.
    """

    @classmethod
    def setUpClass(cls):
        client = create_app().test_client()
        cls.payload = client.get('/api/command-center').get_json()
        cls.page = client.get('/').get_data(as_text=True)

    def test_endpoint_returns_hero_cards(self):
        hero = self.payload.get('_hero')
        self.assertIsNotNone(hero, 'no _hero in payload')
        self.assertTrue(hero, 'hero row would render empty')

    def test_each_card_has_what_the_layout_needs(self):
        for card in self.payload['_hero']:
            for field in ('title', 'url', 'image', 'label', 'icon'):
                self.assertTrue(card.get(field), f'card missing {field}')
            self.assertTrue(card['url'].startswith('http'))
            self.assertTrue(card['image'].startswith('http'))

    def test_cards_follow_the_fixed_page_order(self):
        order = [c['engine'] for c in self.payload['_hero']]
        self.assertEqual(order, [e for e in ('global', 'economy', 'ai')
                                 if e in order])

    def test_no_hardcoded_cards_remain_in_the_page(self):
        """The old cards were frozen July-2026 stories baked into the HTML."""
        self.assertIn('id="econGrid"', self.page)
        self.assertNotIn('War Risk Insurance Surges for Southern Red Sea', self.page)
        self.assertNotIn('Anthropic May Require All Employees', self.page)

    def test_hero_is_not_treated_as_an_engine(self):
        self.assertNotIn('articles', self.payload['_hero'][0])


class TestFeaturedIsLive(unittest.TestCase):
    """The large Featured Analysis card was one frozen July-2026 article."""

    @classmethod
    def setUpClass(cls):
        client = create_app().test_client()
        cls.payload = client.get('/api/command-center').get_json()
        cls.page = client.get('/').get_data(as_text=True)

    def test_endpoint_returns_a_featured_story(self):
        self.assertIsNotNone(self.payload.get('_featured'))

    def test_featured_has_what_the_layout_needs(self):
        f = self.payload['_featured']
        for field in ('title', 'url', 'image'):
            self.assertTrue(f.get(field), f'featured missing {field}')

    def test_featured_does_not_repeat_a_hero_headline(self):
        hero_urls = {c['url'] for c in self.payload['_hero']}
        self.assertNotIn(self.payload['_featured']['url'], hero_urls)

    def test_no_hardcoded_featured_remains(self):
        self.assertIn('id="featuredSlot"', self.page)
        self.assertNotIn("GCCs May Account for Nearly Half", self.page)

    def test_page_structure_survived_the_swap(self):
        """The hardcoded blocks were spliced out; the rest must be intact."""
        for marker in ('id="econGrid"', 'class="pipeline"', 'class="why"',
                       'class="closer"', 'id="founder"', '</nav>'):
            self.assertIn(marker, self.page, f'{marker} lost from the page')
