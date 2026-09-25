"""People Movers pins, and publishers credited by name on the people rows.

A pin (config/pinned_moves.yaml) keeps a reported move at the front of People
Movers past the row's 7-day window, until its end date. It prints a named
person's job change on the public page, so the rules are strict: a real
report, its real date, a visible "Pinned" label, and it expires by itself.

The same change fixed the rows' publisher credits: unlisted feeds were
credited to "Www" (the first label of www.supplychaindive.com), and Executive
Pulse printed bare stems such as "livemint".
"""
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest import mock
from urllib.parse import urlparse

from app.analysis.command_center import (PINNED_MOVES, build_people_rows, build_pulse_cards,
                                         load_pinned_moves)
from app.intelligence.normalize import PUBLISHERS, publisher_for
from app.main import create_app

ROOT = Path(__file__).resolve().parents[1]

PIN = """
pins:
  - title: "Acme appoints Jane Rivera as chief people officer"
    url: "https://press.example.com/acme-cpo"
    source: "Example Press"
    published: 2026-08-18
    type: Appointed
    until: 2026-10-24
"""


def _write(tmp, text):
    path = Path(tmp) / 'pins.yaml'
    path.write_text(text, encoding='utf-8')
    return path


def _now():
    return datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')


def _article(title, url, image='https://example.com/p.jpg'):
    return {'title': title, 'summary': '', 'url': url, 'image': image, 'date': _now()}


class TestLoadPinnedMoves(unittest.TestCase):

    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_an_in_date_pin_keeps_its_real_date_and_is_marked(self):
        pins = load_pinned_moves(_write(self.tmp.name, PIN), today=date(2026, 9, 24))
        self.assertEqual(len(pins), 1)
        pin = pins[0]
        self.assertTrue(pin['pinned'])
        self.assertEqual(pin['date'], '18 Aug')
        self.assertEqual((pin['type'], pin['kind'], pin['source']),
                         ('Appointed', 'appointment', 'Example Press'))

    def test_shown_on_its_last_day_and_gone_the_day_after(self):
        path = _write(self.tmp.name, PIN)
        self.assertEqual(len(load_pinned_moves(path, today=date(2026, 10, 24))), 1)
        self.assertEqual(load_pinned_moves(path, today=date(2026, 10, 25)), [])

    def test_an_exit_reads_as_steps_down(self):
        pins = load_pinned_moves(_write(self.tmp.name, PIN.replace('type: Appointed', 'type: Steps down')),
                                 today=date(2026, 9, 24))
        self.assertEqual((pins[0]['type'], pins[0]['kind']), ('Steps down', 'exit'))

    def test_incomplete_pins_are_skipped(self):
        for broken in (PIN.replace('url: "https://press.example.com/acme-cpo"', 'url: ""'),
                       PIN.replace('    until: 2026-10-24\n', ''),
                       PIN.replace('title: "Acme appoints Jane Rivera as chief people officer"', 'title: ""')):
            self.assertEqual(load_pinned_moves(_write(self.tmp.name, broken), today=date(2026, 9, 24)), [])

    def test_a_missing_or_broken_file_never_fails_the_build(self):
        self.assertEqual(load_pinned_moves(Path(self.tmp.name) / 'absent.yaml'), [])
        self.assertEqual(load_pinned_moves(_write(self.tmp.name, 'pins: [unclosed')), [])

    def test_the_shipped_pin_is_valid_and_expires(self):
        """Dimple Kaloya's move to MetLife GCC, pinned on 2026-09-24 for a month.
        Remove this test with the pin once it has expired."""
        pins = load_pinned_moves(PINNED_MOVES, today=date(2026, 9, 24))
        self.assertEqual([p['url'] for p in pins], [
            'https://www.peoplematters.in/news/appointments/ex-hsbc-hr-leader-dimple-kaloya-joins-metlife-gcc-as-chro-51515'])
        self.assertEqual((pins[0]['source'], pins[0]['date']), ('People Matters', '18 Aug'))
        self.assertEqual(load_pinned_moves(PINNED_MOVES, today=date(2026, 10, 25)), [])


class TestPinsOnTheRow(unittest.TestCase):

    pin = {'title': 'Acme appoints Jane Rivera as chief people officer', 'url': 'https://press.example.com/acme-cpo',
           'type': 'Appointed', 'kind': 'appointment', 'source': 'Example Press', 'date': '18 Aug', 'ts': 0,
           'pinned': True}

    def test_pins_lead_the_row(self):
        rows = build_people_rows([_article('Globex names Omar Haddad chief executive officer',
                                           'https://example.com/globex')],
                                 {'quotes': [], 'leaders': []}, pinned=[self.pin])
        self.assertEqual([m['url'] for m in rows['_movers']],
                         ['https://press.example.com/acme-cpo', 'https://example.com/globex'])

    def test_a_pinned_story_is_not_shown_twice(self):
        rows = build_people_rows([_article(self.pin['title'], self.pin['url'])],
                                 {'quotes': [], 'leaders': []}, pinned=[self.pin])
        self.assertEqual(len(rows['_movers']), 1)
        self.assertTrue(rows['_movers'][0]['pinned'])

    def test_pins_count_toward_the_row_limit(self):
        stories = [_article(f'Firm{i} appoints Person{i} Smith as chief executive officer', f'https://example.com/{i}')
                   for i in range(10)]
        rows = build_people_rows(stories, {'quotes': [], 'leaders': []}, pinned=[self.pin])
        self.assertEqual(len(rows['_movers']), 8)
        self.assertEqual(rows['_movers'][0]['url'], self.pin['url'])

    def test_pulse_does_not_repeat_a_pinned_story(self):
        rows = build_people_rows([_article('Acme CEO Jane Rivera opens a new campus', self.pin['url'])],
                                 {'quotes': [], 'leaders': []}, pinned=[self.pin])
        self.assertEqual(rows['_pulse'], [])

    def test_no_pins_by_default(self):
        rows = build_people_rows([], {'quotes': [], 'leaders': []})
        self.assertEqual(rows['_movers'], [])

    def test_the_live_endpoint_passes_pins_through(self):
        with mock.patch('app.api.routes.get_articles', return_value=[]), \
             mock.patch('app.api.routes.get_leader_quotes', return_value={'quotes': [], 'leaders': []}), \
             mock.patch('app.api.routes.load_pinned_moves', return_value=[self.pin]):
            payload = create_app().test_client().get('/api/command-center').get_json()
        self.assertEqual(payload['_movers'][0]['url'], self.pin['url'])
        self.assertTrue(payload['_movers'][0]['pinned'])

    def test_the_page_labels_pins_and_counts_them_apart(self):
        page = (ROOT / 'app' / 'static' / 'command_center_source.html').read_text(encoding='utf-8')
        self.assertIn("${m.pinned ? ' &middot; Pinned' : ''}", page)
        self.assertIn("plural(moves.length - pinned, 'recent move', 'recent moves') + (pinned ? ` · ${pinned} pinned` : '')", page)


class TestPublisherCredits(unittest.TestCase):

    def test_every_curated_feed_is_credited_by_name(self):
        """No curated feed may fall through to a guess from its hostname."""
        from app.scraper import sources
        hosts = {urlparse(url).netloc
                 for tier in (sources.TIER_1_SOURCES, sources.TIER_2_SOURCES)
                 for urls in tier.values() for url in urls}
        for host in hosts:
            parts = host.split('.')
            listed = any('.'.join(parts[i:]) in PUBLISHERS for i in range(len(parts) - 1))
            self.assertTrue(listed, f'{host} has no publisher name')

    def test_trade_press_is_named(self):
        self.assertEqual(publisher_for('www.supplychaindive.com'), 'Supply Chain Dive')
        self.assertEqual(publisher_for('www.freightwaves.com'), 'FreightWaves')
        self.assertEqual(publisher_for('theloadstar.com'), 'The Loadstar')

    def test_fallback_names_the_site_not_its_subdomain(self):
        self.assertEqual(publisher_for('www.some-trade-journal.com'), 'Some Trade Journal')
        self.assertEqual(publisher_for('m.example.co.uk'), 'Example')
        self.assertEqual(publisher_for('sports.yahoo.com'), 'Yahoo')

    def test_pulse_credits_the_publisher_by_name(self):
        cards = build_pulse_cards([_article('Microsoft CEO Satya Nadella lauds Seattle tech community',
                                            'https://www.livemint.com/story')])
        self.assertEqual(cards[0]['source'], 'Mint')


if __name__ == '__main__':
    unittest.main()
