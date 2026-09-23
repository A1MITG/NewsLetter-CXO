"""Telecom: the seventh tile-only domain, replacing a "coming soon" tile.

Same rules as Defence: the headline must name it, a floor of 5 keeps weak
words ("subscribers", "satellite") from qualifying alone, everyday senses of
its words are blanked. The tile is "Telecom & Digital Infrastructure", so
data centres count. Fed mainly by the telecom trade press added 2026-09-24.
"""
import unittest

from app.analysis.command_center import COMING_SOON_ENGINES, SIGNAL_TO_ENGINE
from app.analysis.signals import SIGNALS, classify_article, synthesize_signals


def tile(title, summary=''):
    result = classify_article(title, summary, include_tile_signals=True)
    return result[0] if result else None


class TestTelecomClassifies(unittest.TestCase):
    """Headlines from the 2026-09-24 scan, and the shapes around them."""

    def test_operators(self):
        self.assertEqual(tile('T-Mobile US, Jio claim first in SA 5G roaming'), 'Signal Telecom')

    def test_spectrum(self):
        self.assertEqual(tile('AT&T strikes spectrum leasing deal with N Squared'), 'Signal Telecom')

    def test_regulator_beats_trade_tariffs(self):
        """Global's "tariffs" is trade policy; TRAI's are phone plans."""
        self.assertEqual(tile('TRAI’s amended rules on voice & SMS-only tariffs may drive churn'),
                         'Signal Telecom')

    def test_data_centres(self):
        self.assertEqual(tile("China's Alibaba launches international data centre push"), 'Signal Telecom')


class TestTelecomLeavesOtherTilesTheirStories(unittest.TestCase):

    def test_airtel_money_ipo_is_markets(self):
        self.assertNotEqual(tile('Airtel Money plans biggest London listing since 2021'), 'Signal Telecom')

    def test_jio_financial_is_finance(self):
        self.assertNotEqual(tile('Jio Financial Services shares jump after quarterly profit'), 'Signal Telecom')

    def test_itu_ai_course_is_ai(self):
        self.assertNotEqual(tile('Google, ITU launch global AI training push'), 'Signal Telecom')

    def test_everyday_senses(self):
        self.assertNotEqual(tile('Voters across the political spectrum back a high-fibre diet campaign'),
                            'Signal Telecom')

    def test_submarine_cable_is_not_defence(self):
        self.assertEqual(tile('Ships suspected of cutting Baltic submarine cables, operators say'),
                         'Signal Telecom')


class TestTelecomNeedsItsHeadline(unittest.TestCase):

    def test_telecom_only_in_the_summary(self):
        result = tile('Quarterly results beat estimates across the Sensex',
                      'Bharti Airtel and Reliance Jio led the gains on 5G subscriber growth.')
        self.assertNotEqual(result, 'Signal Telecom')


class TestSignalsPageUnchanged(unittest.TestCase):

    def test_without_the_flag_telecom_never_wins(self):
        result = classify_article('T-Mobile US, Jio claim first in SA 5G roaming')
        self.assertTrue(result is None or result[0] != 'Signal Telecom')

    def test_signals_page_output_keeps_six(self):
        out = synthesize_signals([], require_current=False)
        self.assertEqual([s['name'] for s in out['signals']], [s['name'] for s in SIGNALS])


class TestTelecomTileIsLive(unittest.TestCase):

    def test_telecom_maps_to_its_tile(self):
        self.assertEqual(SIGNAL_TO_ENGINE['Signal Telecom'], ('telecom', 'Telecom & Digital Infrastructure'))

    def test_telecom_is_no_longer_coming_soon(self):
        self.assertNotIn('telecom', COMING_SOON_ENGINES)


if __name__ == '__main__':
    unittest.main()
