"""Climate: the sixth tile-only domain, replacing a "coming soon" tile.

Same rules as Defence: the headline must name it, a floor of 5 keeps weak
words ("storm", "flood", "monsoon") from qualifying alone, everyday senses of
its words are blanked. Renewables stay with Energy; insured losses and cat
bonds stay with Insurance.
"""
import unittest

from app.analysis.command_center import COMING_SOON_ENGINES, SIGNAL_TO_ENGINE
from app.analysis.signals import SIGNALS, classify_article, synthesize_signals


def tile(title, summary=''):
    result = classify_article(title, summary, include_tile_signals=True)
    return result[0] if result else None


class TestClimateClassifies(unittest.TestCase):
    """Headlines from the 2026-09-23 scan, and the shapes around them."""

    def test_extreme_weather(self):
        self.assertEqual(tile('At least four people killed in Japan as typhoon Dujuan triggers heavy rain, landslides'),
                         'Signal Climate')

    def test_adaptation(self):
        self.assertEqual(tile('Europe Seen Spending More Than $500 Billion to Adapt to Climate Change'),
                         'Signal Climate')

    def test_pollution(self):
        self.assertEqual(tile('Watch: How toxic smog from wildfires is making Indonesians sick'), 'Signal Climate')

    def test_carbon_policy(self):
        self.assertEqual(tile('EU carbon border tax: Indian steelmakers brace for CBAM costs'), 'Signal Climate')


class TestClimateLeavesOtherTilesTheirStories(unittest.TestCase):

    def test_cat_bond_is_insurance(self):
        self.assertNotEqual(tile('Hurricane Polo could trigger $175M Mexico cat bond'), 'Signal Climate')

    def test_listing_drought_is_business(self):
        """"London's listing drought" reached the draft tile."""
        self.assertNotEqual(tile('Does Airtel Money mark the end of London’s listing drought? Not yet'),
                            'Signal Climate')

    def test_business_climate(self):
        self.assertNotEqual(tile('Investment climate improves as RBI signals rate cut'), 'Signal Climate')

    def test_typhoon_hackers_are_cyber(self):
        self.assertNotEqual(tile('Salt Typhoon hackers breached more telecom networks, FBI says'),
                            'Signal Climate')

    def test_renewables_stay_in_energy(self):
        self.assertEqual(tile('India adds record renewable energy capacity as solar installations surge'),
                         'Signal Energy')

    def test_metaphors(self):
        self.assertNotEqual(tile('Startup takes the market by storm after landslide victory in funding round'),
                            'Signal Climate')


class TestClimateNeedsItsHeadline(unittest.TestCase):

    def test_weather_only_in_the_summary(self):
        result = tile('Retail sales slow in August as shoppers hold back',
                      'Hurricane damage and flooding kept stores shut in the southeast.')
        self.assertNotEqual(result, 'Signal Climate')


class TestSignalsPageUnchanged(unittest.TestCase):

    def test_without_the_flag_climate_never_wins(self):
        result = classify_article('Europe Seen Spending More Than $500 Billion to Adapt to Climate Change')
        self.assertTrue(result is None or result[0] != 'Signal Climate')

    def test_signals_page_output_keeps_six(self):
        out = synthesize_signals([], require_current=False)
        self.assertEqual([s['name'] for s in out['signals']], [s['name'] for s in SIGNALS])


class TestClimateTileIsLive(unittest.TestCase):

    def test_climate_maps_to_its_tile(self):
        self.assertEqual(SIGNAL_TO_ENGINE['Signal Climate'], ('climate', 'Climate & Sustainability'))

    def test_climate_is_no_longer_coming_soon(self):
        self.assertNotIn('climate', COMING_SOON_ENGINES)


if __name__ == '__main__':
    unittest.main()
