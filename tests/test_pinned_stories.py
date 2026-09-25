"""Engine tile pins, and the feeds that keep the GCC tile supplied.

Each build sees only what the feeds list at that moment. On 2026-09-25 ET
stopped listing the Dell-Zinnov report on India's GCCs two days after running
it, and the GCC tile, which it led, went empty. A pin
(config/pinned_stories.yaml) keeps a published story at the front of its
tile, and optionally on the Featured card, until an end date. It keeps the
story's real date and says "Pinned", so an older story never passes as
today's. The same change added five feeds that carry GCC news.
"""
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock
from urllib.parse import urlparse

from app.analysis.brief import build_brief
from app.analysis.command_center import (PINNED_STORIES, _clip, build_engine_data,
                                         build_featured, load_pinned_stories)
from app.intelligence.normalize import publisher_for
from app.main import create_app
from app.scraper import sources

ROOT = Path(__file__).resolve().parents[1]

PIN = """
pins:
  - title: "Acme report: most capability centres still piloting AI"
    url: "https://press.example.com/acme-gcc-report"
    source: "Example Press"
    published: 2026-09-23
    engine: gcc
    summary: "The report finds most centres have yet to move AI past a pilot."
    image: "https://press.example.com/report.jpg"
    featured: true
    until: 2026-09-27
"""


def _write(tmp, text):
    path = Path(tmp) / 'pins.yaml'
    path.write_text(text, encoding='utf-8')
    return path


def _signals(gcc_titles=()):
    return {'signals': [{'name': 'Signal GCC',
                         'articles': [{'title': t, 'url': f'https://example.com/{i}'}
                                      for i, t in enumerate(gcc_titles)]}]}


class TestLoadPinnedStories(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_an_in_date_pin_keeps_its_real_date_and_is_marked(self):
        pins = load_pinned_stories(_write(self.tmp.name, PIN), today=date(2026, 9, 25))
        self.assertEqual(len(pins), 1)
        pin = pins[0]
        self.assertTrue(pin['pinned'])
        self.assertTrue(pin['featured'])
        self.assertEqual((pin['engine'], pin['date'], pin['source']), ('gcc', '23 Sep', 'Example Press'))

    def test_shown_on_its_last_day_and_gone_the_day_after(self):
        path = _write(self.tmp.name, PIN)
        self.assertEqual(len(load_pinned_stories(path, today=date(2026, 9, 27))), 1)
        self.assertEqual(load_pinned_stories(path, today=date(2026, 9, 28)), [])

    def test_incomplete_or_unknown_engine_pins_are_skipped(self):
        for broken in (PIN.replace('url: "https://press.example.com/acme-gcc-report"', 'url: ""'),
                       PIN.replace('    until: 2026-09-27\n', ''),
                       PIN.replace('engine: gcc', 'engine: sports')):
            self.assertEqual(load_pinned_stories(_write(self.tmp.name, broken), today=date(2026, 9, 25)), [])

    def test_featured_only_when_marked(self):
        pins = load_pinned_stories(_write(self.tmp.name, PIN.replace('    featured: true\n', '')),
                                   today=date(2026, 9, 25))
        self.assertFalse(pins[0]['featured'])

    def test_a_missing_or_broken_file_never_fails_the_build(self):
        self.assertEqual(load_pinned_stories(Path(self.tmp.name) / 'absent.yaml'), [])
        self.assertEqual(load_pinned_stories(_write(self.tmp.name, 'pins: [unclosed')), [])

    def test_the_shipped_pin_is_valid_and_expires(self):
        """The Dell-Zinnov report, pinned on 2026-09-25 through Sunday 27 Sep.
        Remove this test with the pin once it has expired."""
        pins = load_pinned_stories(PINNED_STORIES, today=date(2026, 9, 25))
        self.assertEqual([(p['engine'], p['featured']) for p in pins], [('gcc', True)])
        self.assertIn('Dell-Zinnov', pins[0]['title'])
        self.assertEqual((pins[0]['source'], pins[0]['date']), ('The Economic Times', '23 Sep'))
        self.assertTrue(pins[0]['image'].startswith('https://'))
        self.assertEqual(load_pinned_stories(PINNED_STORIES, today=date(2026, 9, 28)), [])


class TestPinsOnTheTiles(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.pins = load_pinned_stories(_write(tmp.name, PIN), today=date(2026, 9, 25))

    def test_a_pin_leads_its_tile(self):
        data = build_engine_data(_signals(['Globex opens GCC in Pune']), pinned=self.pins)
        self.assertEqual([a['url'] for a in data['gcc']['articles']],
                         ['https://press.example.com/acme-gcc-report', 'https://example.com/0'])
        self.assertNotIn('engine', data['gcc']['articles'][0])

    def test_other_tiles_are_untouched(self):
        data = build_engine_data(_signals(), pinned=self.pins)
        self.assertEqual(data['insurance']['articles'], [])

    def test_a_pinned_story_the_scan_also_found_is_shown_once(self):
        data = build_engine_data(_signals([self.pins[0]['title']]), pinned=self.pins)
        self.assertEqual(len(data['gcc']['articles']), 1)
        self.assertTrue(data['gcc']['articles'][0]['pinned'])

    def test_pins_count_toward_the_tile_limit(self):
        data = build_engine_data(_signals([f'Firm{i} opens GCC in Pune' for i in range(8)]), pinned=self.pins)
        self.assertEqual(len(data['gcc']['articles']), 8)
        self.assertEqual(data['gcc']['articles'][0]['url'], self.pins[0]['url'])

    def test_no_pins_by_default(self):
        data = build_engine_data(_signals(['Globex opens GCC in Pune']))
        self.assertEqual([a['url'] for a in data['gcc']['articles']], ['https://example.com/0'])


class TestPinnedFeatured(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.pins = load_pinned_stories(_write(tmp.name, PIN), today=date(2026, 9, 25))

    def test_a_featured_pin_is_the_featured_card_and_says_so(self):
        data = build_engine_data(_signals(['Globex opens GCC in Pune']), pinned=self.pins)
        by_title = {'Globex opens GCC in Pune': {'image': 'https://example.com/g.jpg', 'summary': ''}}
        featured = build_featured(data, by_title)
        self.assertEqual(featured['url'], self.pins[0]['url'])
        self.assertEqual((featured['pinned'], featured['source'], featured['date']),
                         (True, 'Example Press', '23 Sep'))
        self.assertEqual(featured['summary'], self.pins[0]['summary'])

    def test_an_unfeatured_pin_leaves_featured_to_the_usual_order(self):
        pins = [dict(self.pins[0], featured=False)]
        data = build_engine_data(_signals(['Globex opens GCC in Pune']), pinned=pins)
        by_title = {'Globex opens GCC in Pune': {'image': 'https://example.com/g.jpg', 'summary': ''}}
        featured = build_featured(data, by_title)
        self.assertEqual(featured['url'], 'https://example.com/0')
        self.assertNotIn('pinned', featured)

    def test_the_summary_is_cut_on_a_word(self):
        text = 'word ' * 80
        clipped = _clip(text, 260)
        self.assertLessEqual(len(clipped), 260)
        self.assertTrue(clipped.endswith('word…'))
        self.assertEqual(_clip('Short and whole.', 260), 'Short and whole.')

    def test_the_brief_carries_the_pin_with_its_own_summary(self):
        data = build_engine_data(_signals(), pinned=self.pins)
        sections = build_brief(data, {})
        item = sections[0]['items'][0]
        self.assertEqual(item['url'], self.pins[0]['url'])
        self.assertTrue(item['summary'].startswith('The report finds'))

    def test_the_live_endpoint_passes_pins_through(self):
        with mock.patch('app.api.routes.get_articles', return_value=[]), \
             mock.patch('app.api.routes.get_leader_quotes', return_value={'quotes': [], 'leaders': []}), \
             mock.patch('app.api.routes.load_pinned_moves', return_value=[]), \
             mock.patch('app.api.routes.load_pinned_stories', return_value=self.pins):
            payload = create_app().test_client().get('/api/command-center').get_json()
        self.assertEqual(payload['gcc']['articles'][0]['url'], self.pins[0]['url'])
        self.assertTrue(payload['_featured']['pinned'])

    def test_the_page_labels_a_pinned_featured_story(self):
        page = (ROOT / 'app' / 'static' / 'command_center_source.html').read_text(encoding='utf-8')
        self.assertIn('${f.pinned ? `<div class="featured-pin">Pinned &middot; ${esc(f.source)} &middot; ${esc(f.date)}</div>` : \'\'}', page)
        public = (ROOT / 'public' / 'command_center.html').read_text(encoding='utf-8')
        self.assertEqual(public, page)


class TestGCCFeeds(unittest.TestCase):

    FEEDS = ('https://gcc.economictimes.indiatimes.com/rss/recentstories',
             'https://economictimes.indiatimes.com/tech/technology/rssfeeds/78570561.cms',
             'https://hr.economictimes.indiatimes.com/rss/topstories',
             'https://www.thehindubusinessline.com/info-tech/feeder/default.rss',
             'https://www.thehindubusinessline.com/companies/feeder/default.rss')

    def test_the_gcc_feeds_are_scanned(self):
        india = sources.TIER_2_SOURCES['India & GCC Business']
        for feed in self.FEEDS:
            self.assertIn(feed, india)

    def test_they_are_read_as_rss_and_credited_by_name(self):
        for feed in self.FEEDS:
            self.assertTrue('rss' in feed.lower() or 'feed' in feed.lower(), feed)
            self.assertIn(publisher_for(urlparse(feed).netloc),
                          ('The Economic Times', 'The Hindu BusinessLine'), feed)


if __name__ == '__main__':
    unittest.main()
