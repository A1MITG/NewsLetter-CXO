"""Manufacturing: the ninth and last tile-only domain, replacing the last
"coming soon" tile.

Same rules as Defence: the headline must name it, a floor of 5 keeps weak
words ("plant", "production") from qualifying alone, everyday senses of its
words are blanked. Power plants and oil production stay with Energy. Fed
mainly by the manufacturing trade press added 2026-09-24.
"""
import unittest

from app.analysis.command_center import COMING_SOON_ENGINES, SIGNAL_TO_ENGINE
from app.analysis.signals import SIGNALS, classify_article, synthesize_signals


def tile(title, summary=''):
    result = classify_article(title, summary, include_tile_signals=True)
    return result[0] if result else None


class TestManufacturingClassifies(unittest.TestCase):
    """Headlines from the 2026-09-24 scan, and the shapes around them."""

    def test_investment(self):
        self.assertEqual(tile('Coca-Cola to spend $10B on US manufacturing by 2030'), 'Signal Manufacturing')

    def test_industrial_policy(self):
        self.assertEqual(tile("Beyond assembly: How 'Make for India' is forging the next global manufacturing hub"),
                         'Signal Manufacturing')

    def test_factories(self):
        self.assertEqual(tile('How manufacturers can improve factory sustainability through AI'),
                         'Signal Manufacturing')

    def test_electronics(self):
        self.assertEqual(tile('Foxconn to double iPhone production lines in Tamil Nadu'), 'Signal Manufacturing')


class TestManufacturingLeavesOtherTilesTheirStories(unittest.TestCase):

    def test_power_plant_is_energy(self):
        self.assertNotEqual(tile('NTPC commissions new coal power plant units in Odisha'), 'Signal Manufacturing')

    def test_oil_production_is_energy(self):
        self.assertNotEqual(tile('OPEC+ agrees to raise oil production in November'), 'Signal Manufacturing')

    def test_film_production(self):
        self.assertNotEqual(tile('Netflix film production moves to Hyderabad studios'), 'Signal Manufacturing')

    def test_plant_as_a_verb(self):
        self.assertNotEqual(tile('Volunteers plant trees along the Yamuna riverfront'), 'Signal Manufacturing')

    def test_munitions_factory_stays_defence(self):
        """The headline says manufacturing; the summary says artillery, so Defence wins."""
        self.assertEqual(tile('Hanwha Defense to establish $2.2B manufacturing campus in Arkansas',
                              'The subsidiary will produce propellant charges for 155mm artillery on the '
                              'U.S. Army’s Pine Bluff Arsenal installation.'),
                         'Signal Defence')


class TestManufacturingNeedsItsHeadline(unittest.TestCase):

    def test_factory_only_in_the_summary(self):
        result = tile('Company reports record quarterly revenue',
                      'The new factory in Pune added manufacturing capacity.')
        self.assertNotEqual(result, 'Signal Manufacturing')


class TestSignalsPageUnchanged(unittest.TestCase):

    def test_without_the_flag_manufacturing_never_wins(self):
        result = classify_article('Coca-Cola to spend $10B on US manufacturing by 2030')
        self.assertTrue(result is None or result[0] != 'Signal Manufacturing')

    def test_signals_page_output_keeps_six(self):
        out = synthesize_signals([], require_current=False)
        self.assertEqual([s['name'] for s in out['signals']], [s['name'] for s in SIGNALS])


class TestAllTilesAreLive(unittest.TestCase):

    def test_manufacturing_maps_to_its_tile(self):
        self.assertEqual(SIGNAL_TO_ENGINE['Signal Manufacturing'], ('manufacturing', 'Manufacturing'))

    def test_no_tile_is_coming_soon(self):
        self.assertEqual(COMING_SOON_ENGINES, {})


if __name__ == '__main__':
    unittest.main()
