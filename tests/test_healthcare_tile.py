"""Healthcare: the fourth tile-only domain, replacing a "coming soon" tile.

Same rules as Defence: the headline must name it, a floor of 5 keeps weak
words ("medical", "drug") from qualifying alone, everyday senses of its words
are blanked, and companies appear only in unambiguous forms. Health insurance
stays with Insurance.
"""
import unittest

from app.analysis.command_center import COMING_SOON_ENGINES, SIGNAL_TO_ENGINE
from app.analysis.signals import SIGNALS, classify_article, synthesize_signals


def tile(title, summary=''):
    result = classify_article(title, summary, include_tile_signals=True)
    return result[0] if result else None


class TestHealthcareClassifies(unittest.TestCase):
    """Headlines from the 2026-09-23 scan, and the shapes around them."""

    def test_health_systems(self):
        self.assertEqual(tile('Healthcare in Africa ‘under growing strain’ after US withdrawal from aid programs'),
                         'Signal Healthcare')

    def test_health_policy(self):
        self.assertEqual(tile('Task force axed health care for hundreds of thousands of Medicaid recipients'),
                         'Signal Healthcare')

    def test_pharma(self):
        self.assertEqual(tile('Sun Pharma gets USFDA nod for generic cancer drug'), 'Signal Healthcare')

    def test_public_health(self):
        self.assertEqual(tile('Dengue cases surge as hospitals in Delhi run short of beds'), 'Signal Healthcare')


class TestHealthcareLeavesOtherTilesTheirStories(unittest.TestCase):

    def test_covid_insurance_claim_is_insurance(self):
        """"Judge rules for Sompo unit in COVID cover fight" reached the draft tile."""
        self.assertNotEqual(tile('Judge rules for Sompo unit in COVID cover fight',
                                 'Sompo America has defeated a $75.9 million COVID-19 insurance claim.'),
                            'Signal Healthcare')

    def test_health_insurance_is_insurance(self):
        self.assertNotEqual(tile('Health insurance premiums set to rise 12% as insurers reprice cover'),
                            'Signal Healthcare')

    def test_medical_ai_is_ai(self):
        self.assertNotEqual(tile('Anthropic, OpenEvidence partner to bring medical AI worldwide'),
                            'Signal Healthcare')

    def test_drug_crime(self):
        self.assertNotEqual(tile('Police bust drug cartel in major drug seizure at port'), 'Signal Healthcare')

    def test_financial_health_and_pandemic_era(self):
        self.assertNotEqual(tile("Bank's financial health improves as pandemic-era loans wind down"),
                            'Signal Healthcare')

    def test_computer_virus(self):
        self.assertNotEqual(tile('New computer virus spreads through retail payment terminals'),
                            'Signal Healthcare')


class TestHealthcareNeedsItsHeadline(unittest.TestCase):

    def test_weak_word_alone_does_not_qualify(self):
        self.assertNotEqual(tile('Startup raises funds for medical billing software'), 'Signal Healthcare')

    def test_health_only_in_the_summary(self):
        result = tile('Budget session opens with focus on growth',
                      'Allocations for hospitals and vaccines rise sharply.')
        self.assertNotEqual(result, 'Signal Healthcare')


class TestSignalsPageUnchanged(unittest.TestCase):

    def test_without_the_flag_healthcare_never_wins(self):
        result = classify_article('Sun Pharma gets USFDA nod for generic cancer drug')
        self.assertTrue(result is None or result[0] != 'Signal Healthcare')

    def test_signals_page_output_keeps_six(self):
        out = synthesize_signals([], require_current=False)
        self.assertEqual([s['name'] for s in out['signals']], [s['name'] for s in SIGNALS])


class TestHealthcareTileIsLive(unittest.TestCase):

    def test_healthcare_maps_to_its_tile(self):
        self.assertEqual(SIGNAL_TO_ENGINE['Signal Healthcare'], ('healthcare', 'Healthcare'))

    def test_healthcare_is_no_longer_coming_soon(self):
        self.assertNotIn('healthcare', COMING_SOON_ENGINES)


if __name__ == '__main__':
    unittest.main()
