"""The people rows: People Movers, Executive Pulse, Leaders on Record.

Each prints claims about a named person — a job change, a news story, their
own words — so each has one rule that keeps it true, and the three together
show a person only once, in the most specific row.
"""
import unittest
from datetime import datetime, timezone

from app.analysis.command_center import (build_featured, build_movers, build_people_rows,
                                         build_pulse_cards, build_record)
from app.scraper import leader_quotes


def _now():
    return datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')


def _article(title, summary='', url='https://example.com/story', image='https://example.com/p.jpg', when=None):
    return {'title': title, 'summary': summary, 'url': url, 'image': image, 'date': when or _now()}


class TestPeopleMovers(unittest.TestCase):

    def test_headline_appointment_is_a_move(self):
        moves = build_movers([_article('Acme appoints Jane Rivera as chief executive officer')])
        self.assertEqual(len(moves), 1)
        self.assertEqual(moves[0]['type'], 'Appointed')

    def test_move_must_be_stated_in_the_headline(self):
        """The event detector also fires on "names OpenAI and its CEO" in a
        lawsuit summary; that is not a move."""
        moves = build_movers([_article(
            'British Columbia sues OpenAI over school shooting',
            'The lawsuit names OpenAI and its CEO as defendants.')])
        self.assertEqual(moves, [])

    def test_named_as_someone_steps_down_is_one_change(self):
        moves = build_movers([_article('Jamieson Named President of SSRU as Stewart Steps Down')])
        self.assertEqual(moves[0]['type'], 'Leadership change')

    def test_a_plain_exit_reads_as_steps_down(self):
        moves = build_movers([_article('Globex chief executive resigns amid probe')])
        self.assertEqual(moves[0]['type'], 'Steps down')
        self.assertEqual(moves[0]['kind'], 'exit')

    def test_stale_moves_are_not_today(self):
        moves = build_movers([_article('Acme appoints Jane Rivera as CEO',
                                       when='Tue, 23 Apr 2024 18:51:45 +0530')])
        self.assertEqual(moves, [])


class TestFeaturedPriority(unittest.TestCase):

    def _engines(self, **urls):
        return {eid: {'name': eid, 'articles': [{'title': t, 'url': t}]} for eid, t in urls.items()}

    def _by_title(self, *titles, image='https://example.com/i.jpg'):
        return {t: {'title': t, 'image': image, 'summary': ''} for t in titles}

    def test_gcc_first(self):
        data = self._engines(gcc='g', insurance='i', global_='x')
        data['global'] = data.pop('global_')
        self.assertEqual(build_featured(data, self._by_title('g', 'i', 'x'))['url'], 'g')

    def test_insurance_when_no_gcc(self):
        data = {'insurance': {'name': 'i', 'articles': [{'title': 'i', 'url': 'i'}]},
                'global': {'name': 'x', 'articles': [{'title': 'x', 'url': 'x'}]}}
        self.assertEqual(build_featured(data, self._by_title('i', 'x'))['url'], 'i')

    def test_falls_back_to_global_not_economy(self):
        data = {'economy': {'name': 'e', 'articles': [{'title': 'e', 'url': 'e'}]},
                'global': {'name': 'x', 'articles': [{'title': 'x', 'url': 'x'}]}}
        self.assertEqual(build_featured(data, self._by_title('e', 'x'))['url'], 'x')

    def test_needs_a_picture(self):
        data = {'gcc': {'name': 'g', 'articles': [{'title': 'g', 'url': 'g'}]},
                'global': {'name': 'x', 'articles': [{'title': 'x', 'url': 'x'}]}}
        by_title = {'g': {'title': 'g', 'image': ''}, 'x': {'title': 'x', 'image': 'https://e.com/i.jpg'}}
        self.assertEqual(build_featured(data, by_title)['url'], 'x')


class TestPulseIsForExecutives(unittest.TestCase):

    def test_a_politician_named_only_as_president_is_not_an_executive(self):
        """How "President Donald Trump" in a summary reached the row."""
        cards = build_pulse_cards([_article(
            'What is the White House pool and why is it in a row with Trump?',
            'President Donald Trump has clashed with the press corps.')])
        self.assertEqual(cards, [])

    def test_political_titles_never_qualify(self):
        cards = build_pulse_cards([_article('Governor Jane Smith unveils new budget')])
        self.assertEqual(cards, [])

    def test_a_ceo_still_qualifies(self):
        cards = build_pulse_cards([_article('JPMorgan CEO Jamie Dimon warns on rates')])
        self.assertEqual([c['name'] for c in cards], ['Jamie Dimon'])


class TestEachPersonOnce(unittest.TestCase):

    def test_pulse_skips_a_move_story(self):
        """Movers wins: the appointment story must not also be a Pulse card."""
        story = _article('Acme names CEO Jane Rivera as chief executive',
                         url='https://example.com/move')
        rows = build_people_rows([story], {'quotes': [], 'leaders': []})
        self.assertEqual(len(rows['_movers']), 1)
        self.assertEqual(rows['_pulse'], [])

    def test_pulse_skips_a_leader_on_record(self):
        cards = build_pulse_cards([_article('Nvidia CEO Jensen Huang opens a new campus')],
                                  exclude_names={'Jensen Huang'})
        self.assertEqual(cards, [])

    def test_pulse_skips_someone_named_in_a_move_headline(self):
        cards = build_pulse_cards([_article('Ryan Specialty CEO Pat Jamieson speaks at summit')],
                                  exclude_text=['Jamieson Named President of SSRU'])
        self.assertEqual(cards, [])

    def test_record_drops_a_leader_who_moved(self):
        quote_set = {'quotes': [{'leader': 'Sam Altman', 'quote': 'x'}, {'leader': 'Lisa Su', 'quote': 'y'}]}
        record = build_record(quote_set, [{'title': 'OpenAI names new chair as Altman steps down'}])
        self.assertEqual([q['leader'] for q in record['quotes']], ['Lisa Su'])


def _page(*paras):
    filler = '<p>' + 'Context sentence for the article body. ' * 40 + '</p>'
    return ('<html><body>' + filler + ''.join(f'<p>{p}</p>' for p in paras) + '</body></html>').encode()


ARTICLE = {'source': 'Test Press', 'url': 'https://press.example.com/a', 'when': datetime(2026, 9, 15, tzinfo=timezone.utc)}


class TestVerbatimQuotes(unittest.TestCase):

    def test_quote_with_speaker_after(self):
        q = leader_quotes.extract_quotes(ARTICLE, _page(
            '“We are building the infrastructure for a new industry,” said Jensen Huang, founder of NVIDIA.'))
        self.assertEqual(len(q), 1)
        self.assertEqual(q[0]['leader'], 'Jensen Huang')
        self.assertEqual(q[0]['company'], 'NVIDIA')
        self.assertEqual(q[0]['quote'], 'We are building the infrastructure for a new industry')

    def test_quote_with_speaker_before(self):
        q = leader_quotes.extract_quotes(ARTICLE, _page(
            'Sam Altman said: “The next model will be meaningfully better at reasoning.”'))
        self.assertEqual([x['leader'] for x in q], ['Sam Altman'])

    def test_unattributed_quote_is_dropped(self):
        q = leader_quotes.extract_quotes(ARTICLE, _page(
            'Sam Altman leads OpenAI. “This is a turning point for the whole industry,” one analyst said.'))
        self.assertEqual(q, [])

    def test_speaker_not_on_the_watchlist_is_dropped(self):
        q = leader_quotes.extract_quotes(ARTICLE, _page(
            '“The grid needs to be risk informed in every decision,” said Josh Wong, founder of ThinkLabs.'))
        self.assertEqual(q, [])

    def test_bare_surname_needs_the_full_name_somewhere(self):
        without = leader_quotes.extract_quotes(ARTICLE, _page(
            '“With electricity, we could power everything,” Huang said.'))
        self.assertEqual(without, [])
        with_full = leader_quotes.extract_quotes(ARTICLE, _page(
            'Jensen Huang spoke on stage.', '“With electricity, we could power everything,” Huang said.'))
        self.assertEqual(len(with_full), 1)

    def test_same_speaker_continuing_is_joined(self):
        q = leader_quotes.extract_quotes(ARTICLE, _page(
            'Jensen Huang spoke.',
            '“With electricity, we could power everything,” Huang said, tracing the arc. '
            '“With the internet, you can find anything.”'))
        self.assertEqual(q[0]['quote'],
                         'With electricity, we could power everything … With the internet, you can find anything.')

    def test_long_quote_is_excerpted_at_a_sentence(self):
        long = 'This is a sentence about the future of compute. ' * 12
        q = leader_quotes.extract_quotes(ARTICLE, _page(f'“{long.strip()}” said Jensen Huang.'))
        self.assertTrue(q[0]['quote'].endswith('…'))
        self.assertLessEqual(len(q[0]['quote']), 285)

    def test_thin_pages_are_skipped(self):
        thin = b'<html><body><p>\xe2\x80\x9cA quote that is long enough to count,\xe2\x80\x9d said Jensen Huang.</p></body></html>'
        self.assertEqual(leader_quotes.extract_quotes(ARTICLE, thin), [])


class TestQuoteSetOffline(unittest.TestCase):

    def test_offline_set_still_names_who_is_listened_to(self):
        """FETCH_LEADER_QUOTES=0 in tests: no network, but a usable shape."""
        from unittest import mock
        with mock.patch.object(leader_quotes, 'CACHE', leader_quotes.ROOT / 'instance' / '__missing__.json'):
            data = leader_quotes.get_leader_quotes()
        self.assertEqual(data['quotes'], [])
        self.assertTrue(any(l['name'] == 'Jensen Huang' for l in data['leaders']))

    def test_quotes_older_than_the_window_are_dropped_at_read_time(self):
        import json
        import tempfile
        from pathlib import Path
        from unittest import mock
        old = {'generated': '2020-01-01T00:00+00:00',
               'quotes': [{'leader': 'Sam Altman', 'quote': 'old', 'ts': 1_577_836_800}]}
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'q.json'
            path.write_text(json.dumps(old), encoding='utf-8')
            with mock.patch.object(leader_quotes, 'CACHE', path):
                self.assertEqual(leader_quotes.get_leader_quotes()['quotes'], [])


if __name__ == '__main__':
    unittest.main()
