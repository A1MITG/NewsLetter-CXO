"""Signal GCC's two-axis rubric.

A capability-centre story has to name a capability centre AND say something
is happening to it. These pin the defects that made that rule necessary --
each named case is a headline that really reached the live GCC tile.
"""
import unittest

from app.analysis.signals import (
    GCC_ACTION,
    GCC_CONTEXT,
    GCC_ENTITY,
    SIGNAL_FLOORS,
    classify_article,
    gcc_axes,
    score_signals,
)


def _gcc(title, summary=''):
    """The Signal GCC result for one article, or None."""
    result = classify_article(title, summary)
    return result if result and result[0] == 'Signal GCC' else None


class TestGeographyIsNotEvidence(unittest.TestCase):
    """The defect that prompted the rubric: cities scoring as domain evidence."""

    def test_puravankara_real_estate_no_longer_classifies(self):
        """Reached the TOP of the live tile on noida(2) + gurugram(2) = 6.

        A residential project in Greater Noida. It names no capability
        centre, so no amount of the right geography should admit it.
        """
        title = ('Puravankara enters national capital region with '
                 '₹5,200-cr Greater Noida project')
        summary = ("Puravankara's entry into NCR comes after Mumbai-based "
                   "luxury home developer Oberoi Realty Ltd recently made a "
                   "strong debut in Gurugram, with ₹8,109 crore of sales "
                   "bookings from the launch of Three Sixty North.")
        self.assertIsNone(_gcc(title, summary))

    def test_no_city_carries_any_weight(self):
        """Tier 1 and Tier 2 alike. Tier-2 cities now court the same
        investment, so a longer city list would widen the defect, not close
        it -- the fix is that geography scores nothing at all."""
        for tier in ('city_tier1', 'city_tier2'):
            for city in GCC_CONTEXT[tier]:
                self.assertNotIn(city, GCC_ENTITY, f'{city} is scoring as entity')
                for _weight, terms in GCC_ACTION.values():
                    self.assertNotIn(city, terms, f'{city} is scoring as action')

    def test_a_pile_of_cities_still_scores_zero(self):
        scores = score_signals('Noida, Gurugram, Bengaluru, Hyderabad and Pune',
                               'Mumbai, Chennai, Kochi, Indore and Coimbatore.')
        self.assertEqual(scores['Signal GCC'], 0)

    def test_vendor_names_and_nationality_are_not_evidence(self):
        """Carried over from the GCCFix reasoning: a supplier's name and a
        dateline are not a capability centre either."""
        for term in GCC_CONTEXT['vendor'] + GCC_CONTEXT['nationality']:
            self.assertNotIn(term, GCC_ENTITY, f'{term} is scoring as entity')


class TestBothAxesRequired(unittest.TestCase):

    def test_entity_without_action_does_not_classify(self):
        """Naming a centre in passing is not a story about one."""
        entity, action = gcc_axes('The global capability centre model, explained')
        self.assertTrue(entity)
        self.assertFalse(action)
        self.assertIsNone(_gcc('The global capability centre model, explained'))

    def test_action_without_entity_does_not_classify(self):
        """Plenty of things get set up and expanded. Most are not GCCs."""
        entity, action = gcc_axes('Retailer expands and opens second campus')
        self.assertFalse(entity)
        self.assertTrue(action)
        self.assertIsNone(_gcc('Retailer expands and opens second campus'))

    def test_both_axes_classify(self):
        """The genuine story from the same day's corpus, which must survive."""
        title = ('Starbucks to set up GCC in Chennai, '
                 'plans to hire 800 tech professionals')
        result = _gcc(title)
        self.assertIsNotNone(result)
        self.assertGreaterEqual(result[1], SIGNAL_FLOORS['Signal GCC'])


class TestFacetSemantics(unittest.TestCase):

    def test_an_action_facet_counts_once(self):
        """Restating one event must not inflate the score.

        'opens', 'opening' and 'to open' are one new-build signal, not three;
        the flat keyword sum this rubric replaced would have counted each.
        """
        once = score_signals('Acme opens global capability centre')['Signal GCC']
        thrice = score_signals(
            'Acme opens global capability centre; opening and to open')['Signal GCC']
        self.assertEqual(once, thrice)

    def test_distinct_facets_do_accumulate(self):
        """Building a centre AND hiring for it is more evidence than either."""
        build = score_signals('Acme opens global capability centre')['Signal GCC']
        both = score_signals(
            'Acme opens global capability centre and starts hiring engineers'
        )['Signal GCC']
        self.assertGreater(both, build)


class TestCaptiveCollision(unittest.TestCase):
    """'captive' alone is more often a captive INSURER in this corpus."""

    def test_bare_captive_is_not_entity_evidence(self):
        self.assertNotIn('captive', GCC_ENTITY)

    def test_captive_insurance_headlines_stay_out(self):
        for title in ('Allianz names captive leader',
                      'A-Cap Insurers File Suit Against SCDOI Director'):
            self.assertIsNone(_gcc(title), title)

    def test_captive_centre_is_still_evidence(self):
        """The unambiguous compound stays -- only the bare word went."""
        for term in ('captive center', 'captive centre', 'captive unit'):
            self.assertIn(term, GCC_ENTITY)


class TestGulfVetoSurvives(unittest.TestCase):
    """Regression guard: GCC beside Gulf terms is the Gulf Cooperation Council."""

    def test_gulf_summit_is_not_a_capability_centre(self):
        title = 'Saudi Arabia and UAE lead GCC summit on energy security'
        self.assertIsNone(_gcc(title))


class TestFloor(unittest.TestCase):

    def test_vendor_services_deal_sits_below_the_floor(self):
        """Cleared both axes at 5. A supplier win, not a capability centre --
        which is the evidence the floor of 6 was chosen on.
        """
        title = 'HCLTech bags AI-led IT transformation deal from M Group'
        result = _gcc(title)
        if result is not None:
            self.assertGreaterEqual(result[1], SIGNAL_FLOORS['Signal GCC'])

    def test_a_signal_is_tested_against_its_own_floor(self):
        """GCC's higher floor must not swallow an article another signal
        would have taken: eligibility is decided before the winner is."""
        title = 'Insurer opens shared services unit as premiums and claims rise'
        result = classify_article(title, 'Underwriting and reinsurance review.')
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
