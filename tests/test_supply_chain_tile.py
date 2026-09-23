"""Supply Chain: the eighth tile-only domain, replacing a "coming soon" tile.

Same rules as Defence: the headline must name it, a floor of 5 keeps weak
words ("shortage", "port", "UPS") from qualifying alone, everyday senses of
its words are blanked. The context rule: a housing or talent "shortage" is
not a supply-chain story. Fed mainly by the logistics trade press added
2026-09-24.
"""
import unittest

from app.analysis.command_center import COMING_SOON_ENGINES, SIGNAL_TO_ENGINE
from app.analysis.signals import SIGNALS, classify_article, synthesize_signals


def tile(title, summary=''):
    result = classify_article(title, summary, include_tile_signals=True)
    return result[0] if result else None


class TestSupplyChainClassifies(unittest.TestCase):
    """Headlines from the 2026-09-24 scan, and the shapes around them."""

    def test_shipping(self):
        self.assertEqual(tile('Box shipping and air freight – whither earnings when disruption passes?'),
                         'Signal Supply Chain')

    def test_carrier_rate_hike_is_not_banking(self):
        """"Rate hike" put this in Banking before the tile existed."""
        self.assertEqual(tile('FedEx preps 5.9% rate hike, surcharge increases for 2027'), 'Signal Supply Chain')

    def test_logistics_contract(self):
        self.assertEqual(tile('Kuehne+Nagel takes logistics lead for Amazon data center expansion'),
                         'Signal Supply Chain')

    def test_driver_shortage_counts(self):
        self.assertEqual(tile('Truck driver shortage deepens as freight volumes climb'), 'Signal Supply Chain')


class TestSupplyChainContextRule(unittest.TestCase):

    def test_housing_shortage(self):
        self.assertNotEqual(tile('Housing shortage pushes rents to record in Mumbai'), 'Signal Supply Chain')

    def test_talent_shortage(self):
        self.assertNotEqual(tile('Talent shortage slows GCC hiring in Bengaluru'), 'Signal Supply Chain')


class TestSupplyChainLeavesOtherTilesTheirStories(unittest.TestCase):

    def test_ups_pension_scheme(self):
        self.assertNotEqual(tile('Railways starts UPS pension scheme for its employees'), 'Signal Supply Chain')

    def test_freight_insurance_is_insurance(self):
        self.assertNotEqual(tile('Trucking Insurance Fraud: Is Your Fleet Really Covered?'),
                            'Signal Supply Chain')

    def test_software_supply_chain_attack_is_cyber(self):
        self.assertNotEqual(tile('Hackers behind software supply chain attack on npm packages'),
                            'Signal Supply Chain')

    def test_metaphor(self):
        self.assertNotEqual(tile('Founder mode for agency owners: Stay hands-on, not the bottleneck'),
                            'Signal Supply Chain')


class TestSupplyChainNeedsItsHeadline(unittest.TestCase):

    def test_freight_only_in_the_summary(self):
        result = tile('Retailer beats earnings estimates on strong holiday demand',
                      'Freight costs and port congestion eased during the quarter.')
        self.assertNotEqual(result, 'Signal Supply Chain')


class TestSignalsPageUnchanged(unittest.TestCase):

    def test_without_the_flag_supply_chain_never_wins(self):
        result = classify_article('Box shipping and air freight – whither earnings when disruption passes?')
        self.assertTrue(result is None or result[0] != 'Signal Supply Chain')

    def test_signals_page_output_keeps_six(self):
        out = synthesize_signals([], require_current=False)
        self.assertEqual([s['name'] for s in out['signals']], [s['name'] for s in SIGNALS])


class TestSupplyChainTileIsLive(unittest.TestCase):

    def test_supply_chain_maps_to_its_tile(self):
        self.assertEqual(SIGNAL_TO_ENGINE['Signal Supply Chain'], ('supplychain', 'Supply Chain'))

    def test_supply_chain_is_no_longer_coming_soon(self):
        self.assertNotIn('supplychain', COMING_SOON_ENGINES)


if __name__ == '__main__':
    unittest.main()
