"""Executive Pulse: a leader's name and face over a story about them.

Was four hardcoded cards — name, photo and hand-written commentary baked into
the HTML, each stamped "today" while pointing at July 2026 articles.

This row is the highest-risk surface on the page: it prints a real person's
name over their photograph, so a wrong pairing is a defect about a named
individual, not just a stale headline.
"""
import unittest

import pytest

from app.analysis.command_center import _looks_like_a_person, build_pulse_cards
from app.main import create_app


class TestNameValidation(unittest.TestCase):
    """The Sprint 5 extractor keys off "ROLE + Capitalised Words", which picks
    up verbs and qualifiers next to a role term."""

    def test_accepts_real_names(self):
        for name in ('Satya Nadella', 'Warren Buffett', 'Shapoor Mistry',
                     'Sundar Pichai', 'Paul J. Stock'):
            self.assertTrue(_looks_like_a_person(name), name)

    def test_rejects_verbs_caught_beside_a_role(self):
        """"Boohoo's New Chairman Stirs Controversy" -> "Stirs Controversy"."""
        for name in ('Stirs Controversy', 'Noel Opposed', 'Backs Open'):
            self.assertFalse(_looks_like_a_person(name), name)

    def test_rejects_role_qualifiers(self):
        """"CEO Designate Tewolde Gebremariam" keeps the qualifier."""
        self.assertFalse(_looks_like_a_person('Designate Tewolde Gebremariam'))
        self.assertFalse(_looks_like_a_person('Interim Jane Doe'))

    def test_rejects_single_and_overlong_names(self):
        self.assertFalse(_looks_like_a_person('Buffett'))
        self.assertFalse(_looks_like_a_person('A B C D E'))


class TestPulseCardBuilding(unittest.TestCase):

    def _article(self, title, image='https://example.com/p.jpg', when=None):
        from datetime import datetime, timezone
        return {
            'title': title,
            'url': 'https://example.com/story',
            'image': image,
            'summary': '',
            'date': when or datetime.now(timezone.utc).strftime(
                '%a, %d %b %Y %H:%M:%S +0000'),
        }

    def test_builds_a_card_for_a_named_leader(self):
        cards = build_pulse_cards([
            self._article('Microsoft CEO Satya Nadella lauds Seattle tech community'),
        ])
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]['name'], 'Satya Nadella')
        self.assertEqual(cards[0]['source'], 'example')

    def test_skips_articles_without_a_photograph(self):
        """The layout puts the name over the image; no image, no card."""
        cards = build_pulse_cards([
            self._article('Microsoft CEO Satya Nadella lauds Seattle', image=''),
        ])
        self.assertEqual(cards, [])

    def test_skips_stale_articles(self):
        cards = build_pulse_cards([
            self._article('Microsoft CEO Satya Nadella lauds Seattle',
                          when='Tue, 23 Apr 2024 18:51:45 +0530'),
        ])
        self.assertEqual(cards, [])

    def test_rejects_a_leader_who_is_only_incidental(self):
        """A name from the summary that the headline never mentions."""
        article = self._article('Brazil’s Lula announces higher welfare payments')
        article['summary'] = 'President Jair Bolsonaro was not present.'
        self.assertEqual(build_pulse_cards([article]), [])

    def test_accepts_a_headline_that_uses_only_the_surname(self):
        """"Buffett Steps Down" is entirely about him, first name or not."""
        article = self._article('Buffett Steps Down as Berkshire Chair')
        article['summary'] = 'Warren Buffett, the founder, ends a six-decade run.'
        cards = build_pulse_cards([article])
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]['name'], 'Warren Buffett')

    def test_surname_match_respects_word_boundaries(self):
        """"Gray" must not match "Grayscale"."""
        from app.analysis.command_center import _is_the_subject
        self.assertFalse(_is_the_subject('Jane Gray', 'Grayscale launches a fund'))
        self.assertTrue(_is_the_subject('Jane Gray', 'Gray named as new chair'))

    def test_does_not_repeat_a_leader(self):
        cards = build_pulse_cards([
            self._article('Microsoft CEO Satya Nadella lauds Seattle tech'),
            self._article('Microsoft CEO Satya Nadella opens a new campus'),
        ])
        self.assertEqual(len(cards), 1)

    def test_respects_the_limit(self):
        arts = [self._article(f'Company{i} CEO Firstname Lastname{i} speaks today')
                for i in range(12)]
        self.assertLessEqual(len(build_pulse_cards(arts, limit=3)), 3)


@pytest.mark.usefixtures("raw_cache")
class TestPulseIsLive(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.payload = create_app().test_client() \
            .get('/api/command-center').get_json()

    def test_endpoint_returns_pulse(self):
        self.assertIsInstance(self.payload.get('_pulse'), list)

    def test_every_card_has_what_the_layout_needs(self):
        for card in self.payload['_pulse']:
            for field in ('name', 'title', 'url', 'image'):
                self.assertTrue(card.get(field), f'card missing {field}')
            self.assertTrue(card['image'].startswith('http'))
            self.assertTrue(_looks_like_a_person(card['name']), card['name'])

    def test_card_subject_appears_in_its_headline(self):
        """At minimum the surname, so the card is about the person it pictures."""
        from app.analysis.command_center import _is_the_subject
        for card in self.payload['_pulse']:
            self.assertTrue(_is_the_subject(card['name'], card['title']),
                            f"{card['name']} not the subject of {card['title']!r}")


class TestPulseMarkup(unittest.TestCase):
    """The template alone, so it runs without a corpus (CI has none)."""

    @classmethod
    def setUpClass(cls):
        cls.page = create_app().test_client().get('/').get_data(as_text=True)

    def test_no_hardcoded_leaders_remain(self):
        self.assertIn('id="pulseTrack"', self.page)
        for stale in ('Pawan Kumar Chanda', 'The Boring Company seeks funding'):
            self.assertNotIn(stale, self.page)


if __name__ == '__main__':
    unittest.main()


class TestSupplementaryHeadlinePatterns(unittest.TestCase):
    """Shapes app/intelligence/entities.py does not match.

    Each miss costs this row a card, so they are covered here rather than by
    widening the shared Sprint 5 extractor.
    """

    def setUp(self):
        from app.analysis.command_center import _names_from_headline
        self.f = _names_from_headline

    def test_appointment_without_the_word_as(self):
        """entities.py needs "names X as ROLE"; real headlines drop the "as"."""
        self.assertEqual(self.f('Helmsman names Emily Drew president, CEO'),
                         ['Emily Drew'])

    def test_profile_piece(self):
        self.assertEqual(
            self.f('Who is Karandeep Anand? The Character.AI CEO joins Disney'),
            ['Karandeep Anand'])

    def test_departure(self):
        self.assertEqual(self.f('Warren Buffett steps down as Berkshire chair'),
                         ['Warren Buffett'])

    def test_requires_a_role_word_in_the_headline(self):
        """"Who is <Name>?" alone matches athletes and celebrities."""
        self.assertEqual(self.f('Who is Suchika Tariyal? India MMA medal hope'), [])

    def test_ignores_a_role_with_nobody_named(self):
        self.assertEqual(self.f('Sompo names new U.K. CEO'), [])

    def test_does_not_swallow_the_role_into_the_name(self):
        """Case-sensitivity is load-bearing: a global IGNORECASE turns the name
        pattern into "any word" and it absorbs the role that follows."""
        for name in self.f('Helmsman names Emily Drew president, CEO'):
            self.assertNotIn('president', name.lower())

    def test_furniture_is_not_a_chairman(self):
        self.assertEqual(self.f('Apple unveils a new chair for its offices'), [])
