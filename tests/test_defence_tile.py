"""Defence: the third tile-only domain, replacing a "coming soon" tile.

Same rules as Energy: the headline must name it, everyday senses of its words
are blanked, companies appear only in unambiguous forms. It takes its stories
mostly from Signal Global, which keeps diplomacy, ceasefires and war in general.
"""
import unittest

from app.analysis.command_center import COMING_SOON_ENGINES, SIGNAL_TO_ENGINE
from app.analysis.signals import SIGNALS, classify_article, synthesize_signals


def tile(title, summary=''):
    result = classify_article(title, summary, include_tile_signals=True)
    return result[0] if result else None


class TestDefenceClassifies(unittest.TestCase):
    """Headlines from the 2026-09-23 scan, and the shapes around them."""

    def test_fighter_jets(self):
        self.assertEqual(tile('Australia investigating how F-35 fighter jet parts bound for US went missing in Hong Kong'),
                         'Signal Defence')

    def test_airspace_violation(self):
        self.assertEqual(tile('Poland accuses Russian military helicopter of violating its airspace'), 'Signal Defence')

    def test_bases_move_from_global(self):
        self.assertEqual(tile('US to build two military bases in Greenland under new deal with Denmark'),
                         'Signal Defence')

    def test_defence_industry(self):
        self.assertEqual(tile('HAL wins Rs 26,000 crore order as Hindustan Aeronautics ramps up Tejas output'),
                         'Signal Defence')


class TestDefenceIgnoresEverydaySenses(unittest.TestCase):

    def test_sport(self):
        self.assertNotEqual(tile("Arsenal's title defence falters as Chelsea's defence holds firm"), 'Signal Defence')

    def test_law(self):
        self.assertNotEqual(tile('Defence lawyers seek bail in insider trading case'), 'Signal Defence')

    def test_veterans_personal_stories(self):
        """"How did US Army veteran Chris Spatola die?" reached the draft tile."""
        self.assertNotEqual(tile('How did US Army veteran Chris Spatola die?'), 'Signal Defence')

    def test_cyber_defence_belongs_to_cyber(self):
        self.assertNotEqual(tile('OpenAI gives cyber defence tools to Ukraine'), 'Signal Defence')

    def test_metaphors(self):
        self.assertNotEqual(tile('An army of fans greets the band; their secret weapon is the chorus'),
                            'Signal Defence')


class TestDefenceNeedsItsHeadline(unittest.TestCase):

    def test_troops_only_in_the_summary_stay_in_global(self):
        result = tile('G20 leaders call for a ceasefire in Gaza',
                      'Troops remained on the border as diplomats met.')
        self.assertNotEqual(result, 'Signal Defence')


class TestSignalsPageUnchanged(unittest.TestCase):

    def test_without_the_flag_defence_never_wins(self):
        result = classify_article('Poland accuses Russian military helicopter of violating its airspace')
        self.assertTrue(result is None or result[0] != 'Signal Defence')

    def test_signals_page_output_keeps_six(self):
        out = synthesize_signals([], require_current=False)
        self.assertEqual([s['name'] for s in out['signals']], [s['name'] for s in SIGNALS])


class TestDefenceTileIsLive(unittest.TestCase):

    def test_defence_maps_to_its_tile(self):
        self.assertEqual(SIGNAL_TO_ENGINE['Signal Defence'], ('defence', 'Defence'))

    def test_defence_is_no_longer_coming_soon(self):
        self.assertNotIn('defence', COMING_SOON_ENGINES)


if __name__ == '__main__':
    unittest.main()
