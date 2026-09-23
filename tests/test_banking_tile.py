"""Banking: the first tile-only domain, replacing a "coming soon" tile.

Scored like the other tiles (weighted keywords, headline counts double, one
article per tile), but only for the Command Center: the Signals page keeps
its six signals and classifies exactly as before.
"""
import unittest

from app.analysis.command_center import COMING_SOON_ENGINES, SIGNAL_TO_ENGINE
from app.analysis.signals import SIGNALS, classify_article, synthesize_signals


def banking(title, summary=''):
    result = classify_article(title, summary, include_tile_signals=True)
    return result[0] if result else None


class TestBankingClassifies(unittest.TestCase):

    def test_central_bank_policy(self):
        self.assertEqual(banking('RBI keeps repo rate unchanged, flags liquidity'), 'Signal Banking')

    def test_bank_results_are_banking_not_business(self):
        self.assertEqual(banking('HDFC Bank Q2 profit rises 12% on loan growth'), 'Signal Banking')

    def test_lenders_and_bad_loans(self):
        self.assertEqual(banking('NBFCs face tighter norms as bad loans climb'), 'Signal Banking')


class TestBankingIgnoresLookalikes(unittest.TestCase):
    """Phrases that contain "bank" or "deposits" but are not banking."""

    def test_west_bank_is_geopolitics(self):
        self.assertNotEqual(banking('Israel expands settlements in the occupied West Bank'), 'Signal Banking')

    def test_world_bank_is_not_a_bank_story(self):
        self.assertNotEqual(banking('World Bank cuts South Asia growth forecast'), 'Signal Banking')

    def test_food_bank_is_charity(self):
        self.assertNotEqual(banking('Food bank demand soars as prices bite'), 'Signal Banking')

    def test_mineral_deposits_are_geology(self):
        self.assertNotEqual(banking('Chile confirms vast lithium deposits in the north'), 'Signal Banking')


class TestSignalsPageUnchanged(unittest.TestCase):
    """Banking is a tile only; the Signals page keeps its six."""

    def test_without_the_flag_banking_never_wins(self):
        result = classify_article('RBI keeps repo rate unchanged, flags liquidity')
        self.assertTrue(result is None or result[0] != 'Signal Banking')

    def test_signals_page_output_keeps_six(self):
        out = synthesize_signals([], require_current=False)
        self.assertEqual([s['name'] for s in out['signals']], [s['name'] for s in SIGNALS])

    def test_command_center_output_adds_banking(self):
        out = synthesize_signals([], require_current=False, include_tile_signals=True)
        self.assertIn('Signal Banking', [s['name'] for s in out['signals']])


class TestBankingTileIsLive(unittest.TestCase):

    def test_banking_maps_to_its_tile(self):
        self.assertEqual(SIGNAL_TO_ENGINE['Signal Banking'], ('banking', 'Banking'))

    def test_banking_is_no_longer_coming_soon(self):
        self.assertNotIn('banking', COMING_SOON_ENGINES)


if __name__ == '__main__':
    unittest.main()
