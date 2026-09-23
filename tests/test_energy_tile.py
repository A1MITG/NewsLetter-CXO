"""Energy: the second tile-only domain, replacing a "coming soon" tile.

Built with the Banking review's rules from the start: the headline must name
it, everyday senses of its words are blanked, and companies appear only in
unambiguous forms.
"""
import unittest

from app.analysis.command_center import COMING_SOON_ENGINES, SIGNAL_TO_ENGINE
from app.analysis.signals import SIGNALS, classify_article, synthesize_signals


def tile(title, summary=''):
    result = classify_article(title, summary, include_tile_signals=True)
    return result[0] if result else None


class TestEnergyClassifies(unittest.TestCase):
    """Headlines from the 2026-09-23 scan, and the shapes around them."""

    def test_oil_prices(self):
        self.assertEqual(tile('Oil prices ease as Saudi restores key pipeline, traders optimistic on US-Iran talks'),
                         'Signal Energy')

    def test_indian_oil_marketing_companies(self):
        self.assertEqual(tile('OMCs face Rs 530 crore daily losses as crude surges'), 'Signal Energy')

    def test_power_sector(self):
        self.assertEqual(tile('Power demand hits record as heatwave strains the grid'), 'Signal Energy')

    def test_refinery_deal(self):
        self.assertEqual(tile("Africa's richest man picks Indian PSU for $450 million refinery contract in Kenya"),
                         'Signal Energy')

    def test_companies_by_unambiguous_name(self):
        self.assertEqual(tile('NTPC commissions 1,600 MW unit in Odisha'), 'Signal Energy')


class TestEnergyIgnoresEverydaySenses(unittest.TestCase):

    def test_kitchen_oils(self):
        self.assertNotEqual(tile('Palm oil imports rise as edible oil prices soften'), 'Signal Energy')

    def test_nuclear_weapons_are_defence(self):
        self.assertNotEqual(tile('Iran nuclear talks stall as inspectors are refused entry'), 'Signal Energy')

    def test_shell_companies_are_fraud(self):
        self.assertNotEqual(tile('ED raids 40 shell companies in money laundering probe'), 'Signal Energy')

    def test_solar_eclipse_is_astronomy(self):
        self.assertNotEqual(tile('Solar eclipse visible across India on Sunday'), 'Signal Energy')

    def test_greenhouse_gas_is_climate(self):
        self.assertNotEqual(tile('Greenhouse gas concentrations hit new high, WMO says'), 'Signal Energy')

    def test_bare_shell_and_bp_do_not_count(self):
        """"Shell" and "BP" alone are too ambiguous (shell companies, basis points)."""
        self.assertNotEqual(tile('RBI cuts rates by 25 bp; Shell of old policy remains'), 'Signal Energy')


class TestEnergyNeedsItsHeadline(unittest.TestCase):

    def test_oil_only_in_the_summary_stays_where_it_was(self):
        """Geopolitics that mentions oil in passing stays in Global."""
        result = tile('NATO allies meet in Brussels amid rising tensions with Russia',
                      'Oil markets were calm; the summit focused on defence spending.')
        self.assertNotEqual(result, 'Signal Energy')


class TestSignalsPageUnchanged(unittest.TestCase):

    def test_without_the_flag_energy_never_wins(self):
        result = classify_article('Oil prices ease as Saudi restores key pipeline')
        self.assertTrue(result is None or result[0] != 'Signal Energy')

    def test_signals_page_output_keeps_six(self):
        out = synthesize_signals([], require_current=False)
        self.assertEqual([s['name'] for s in out['signals']], [s['name'] for s in SIGNALS])


class TestEnergyTileIsLive(unittest.TestCase):

    def test_energy_maps_to_its_tile(self):
        self.assertEqual(SIGNAL_TO_ENGINE['Signal Energy'], ('energy', 'Energy'))

    def test_energy_is_no_longer_coming_soon(self):
        self.assertNotIn('energy', COMING_SOON_ENGINES)


if __name__ == '__main__':
    unittest.main()
