"""Signal GCC's rubric (app/analysis/gcc_rubric.py), section by section.

A GCC story names a capability centre AND says what is happening to one, and
"GCC" beside Gulf words is the Gulf Cooperation Council. Named cases are
headlines that really reached, or should have reached, the live GCC tile.
"""
import unittest

from app.analysis.gcc_rubric import (BRANCHES, ENTITY, FACETS, MIN_SCORE, NAMED_CENTRE,
                                     NOT_EVIDENCE, gcc_axes, gcc_branches, gcc_means_gulf,
                                     gcc_vocabulary, names_a_centre)
from app.analysis.signals import KEYWORDS, SIGNAL_FLOORS, classify_article, score_signals


def _gcc(title, summary=''):
    """The Signal GCC result on the Signals page, or None."""
    result = classify_article(title, summary)
    return result if result and result[0] == 'Signal GCC' else None


def _tile(title, summary=''):
    """The Command Center tile a story lands on (tile Signals competing too)."""
    result = classify_article(title, summary, include_tile_signals=True)
    return result[0] if result else None


# ═════════════════════════════════════════════════════════════════════════════
# 1. ENTITY
# ═════════════════════════════════════════════════════════════════════════════

class TestEntity(unittest.TestCase):

    def test_bare_captive_is_not_entity_evidence(self):
        """'captive' alone is more often a captive INSURER in this corpus."""
        self.assertNotIn('captive', ENTITY)

    def test_captive_insurance_headlines_stay_out(self):
        for title in ('Allianz names captive leader',
                      'A-Cap Insurers File Suit Against SCDOI Director'):
            self.assertIsNone(_gcc(title), title)

    def test_captive_centre_is_still_evidence(self):
        """The unambiguous compound stays -- only the bare word went."""
        for term in ('captive center', 'captive centre', 'captive unit'):
            self.assertIn(term, ENTITY)

    def test_plural_centres_are_named(self):
        """Word-bounded matching: 'engineering centre' misses "centres"."""
        for title in ('Airbus opens engineering centres in Bengaluru and Chennai',
                      'Siemens to double headcount at its Pune R&D centres'):
            self.assertEqual(_tile(title), 'Signal GCC', title)

    def test_every_named_centre_is_an_entity_worth_four(self):
        for term in NAMED_CENTRE:
            self.assertEqual(ENTITY.get(term), 4, term)


# ═════════════════════════════════════════════════════════════════════════════
# 2. FACETS -- the India GCC taxonomy
# ═════════════════════════════════════════════════════════════════════════════

class TestBothAxesRequired(unittest.TestCase):

    def test_entity_without_a_facet_does_not_classify(self):
        """Naming a centre in passing is not a story about one."""
        entity, facet = gcc_axes('The global capability centre model, explained')
        self.assertTrue(entity)
        self.assertFalse(facet)
        self.assertIsNone(_gcc('The global capability centre model, explained'))

    def test_a_facet_without_an_entity_does_not_classify(self):
        """Plenty of things get set up and expanded. Most are not GCCs."""
        entity, facet = gcc_axes('Retailer expands and opens second campus')
        self.assertFalse(entity)
        self.assertTrue(facet)
        self.assertIsNone(_gcc('Retailer expands and opens second campus'))

    def test_both_axes_classify(self):
        """The genuine story from the same day's corpus, which must survive."""
        result = _gcc('Starbucks to set up GCC in Chennai, plans to hire 800 tech professionals')
        self.assertIsNotNone(result)
        self.assertGreaterEqual(result[1], SIGNAL_FLOORS['Signal GCC'])


class TestFacetSemantics(unittest.TestCase):

    def test_a_facet_counts_once(self):
        """'opens', 'opening' and 'to open' are one new-build signal, not three."""
        once = score_signals('Acme opens global capability centre')['Signal GCC']
        thrice = score_signals('Acme opens global capability centre; opening and to open')['Signal GCC']
        self.assertEqual(once, thrice)

    def test_distinct_facets_do_accumulate(self):
        """Building a centre AND hiring for it is more evidence than either."""
        build = score_signals('Acme opens global capability centre')['Signal GCC']
        both = score_signals('Acme opens global capability centre and starts hiring engineers')['Signal GCC']
        self.assertGreater(both, build)

    def test_every_facet_has_a_taxonomy_branch(self):
        for name, facet in FACETS.items():
            self.assertIn(facet.branch, BRANCHES, name)
        self.assertEqual({f.branch for f in FACETS.values()}, set(BRANCHES))


class TestTaxonomyBranches(unittest.TestCase):
    """One real or representative headline per branch of the India GCC tree."""

    CASES = {
        'New GCC': 'Syneos Health opens GCC in Hyderabad',
        'Expansion': 'Enterprises tap GCCs for bigger cybersecurity mandate as global roles expand',
        'Leadership': 'Ex-HSBC HR leader Dimple Kaloya joins MetLife GCC as CHRO',
        'Capability': "Nearly 70% of India's GCCs stuck at AI pilot stage: Dell-Zinnov report",
        'Sector': 'Manufacturing, transport firms overtake banks to lead India’s GCC boom',
        'Talent': 'The talent paradox facing India’s GCCs',
        'Policy': 'Maharashtra unveils GCC policy with incentives for tier-2 cities',
        'Real estate': 'GCCs lease a record 12 million sq ft of office space',
        'Consolidation': 'TCS is buying into GCCs. What does it mean for India’s captive model?',
    }

    def test_each_branch_reaches_the_gcc_tile(self):
        for branch, title in self.CASES.items():
            self.assertEqual(_tile(title), 'Signal GCC', title)
            self.assertIn(branch, gcc_branches(title), title)

    def test_job_cuts_are_consolidation(self):
        """Moneycontrol, 25 Sep 2026: "cut", not "cuts"."""
        title = 'GCCs cut thousands of jobs even as India takes on bigger global mandates'
        self.assertIn('Consolidation', gcc_branches(title))

    def test_a_centres_leaders_are_a_gcc_story(self):
        """ET's GCC-leader profiles name the centre only in the summary."""
        summary = ('Faces of Change is a limited-edition photo essay series that looks past '
                   'the titles; what shaped these GCC leaders and country heads.')
        self.assertEqual(_tile('Faces of Change: Manish Tambe', summary), 'Signal GCC')
        self.assertEqual(gcc_branches('Faces of Change: Manish Tambe', summary), ['Leadership'])


class TestTopicFacetsNeedANamedCentre(unittest.TestCase):
    """Leadership, capability, sector, ... count only beside a named centre."""

    def test_a_supplier_deal_is_still_not_a_gcc_story(self):
        """Supporting terms ('it services', 'outsourcing') are not named centres."""
        for title in ('Infosys wins manufacturing IT services deal from European carmaker',
                      'Bosch outsourcing arm eyes automotive clients',
                      'HCLTech appoints new head of its outsourcing business'):
            self.assertNotEqual(_tile(title), 'Signal GCC', title)

    def test_a_centres_own_name_is_not_evidence_of_its_work(self):
        """'engineering' in "engineering centre" is the entity, not a facet."""
        self.assertIsNone(_gcc('The engineering centre model, explained'))
        self.assertEqual(gcc_axes('The engineering centre model, explained'), (True, False))

    def test_manufacturing_and_engineering_gccs(self):
        for title in ('Manufacturing, transport firms overtake banks to lead India’s GCC boom',
                      'Engineering GCCs drive ER&D spend in India'):
            self.assertEqual(_tile(title), 'Signal GCC', title)


# ═════════════════════════════════════════════════════════════════════════════
# 3. NOT EVIDENCE
# ═════════════════════════════════════════════════════════════════════════════

class TestGeographyIsNotEvidence(unittest.TestCase):
    """The defect that prompted the rubric: cities scoring as domain evidence."""

    def test_puravankara_real_estate_no_longer_classifies(self):
        """Reached the TOP of the live tile on noida(2) + gurugram(2) = 6.

        A residential project in Greater Noida. It names no capability
        centre, so no amount of the right geography should admit it.
        """
        title = 'Puravankara enters national capital region with ₹5,200-cr Greater Noida project'
        summary = ("Puravankara's entry into NCR comes after Mumbai-based luxury home developer "
                   "Oberoi Realty Ltd recently made a strong debut in Gurugram, with ₹8,109 "
                   "crore of sales bookings from the launch of Three Sixty North.")
        self.assertIsNone(_gcc(title, summary))

    def test_no_city_carries_any_weight(self):
        """A longer city list would widen the defect: geography scores nothing."""
        for tier in ('city_tier1', 'city_tier2'):
            for city in NOT_EVIDENCE[tier]:
                self.assertNotIn(city, ENTITY, f'{city} is scoring as entity')
                for name, facet in FACETS.items():
                    self.assertNotIn(city, facet.terms, f'{city} is scoring in {name}')

    def test_a_pile_of_cities_still_scores_zero(self):
        scores = score_signals('Noida, Gurugram, Bengaluru, Hyderabad and Pune',
                               'Mumbai, Chennai, Kochi, Indore and Coimbatore.')
        self.assertEqual(scores['Signal GCC'], 0)

    def test_vendor_names_and_nationality_are_not_evidence(self):
        for term in NOT_EVIDENCE['vendor'] + NOT_EVIDENCE['nationality']:
            self.assertNotIn(term, ENTITY, f'{term} is scoring as entity')
            for name, facet in FACETS.items():
                self.assertNotIn(term, facet.terms, f'{term} is scoring in {name}')


# ═════════════════════════════════════════════════════════════════════════════
# 4. GULF
# ═════════════════════════════════════════════════════════════════════════════

class TestGulfCooperationCouncil(unittest.TestCase):

    GULF = (
        'Saudi Arabia and UAE lead GCC summit on energy security',
        'India, GCC to resume free trade agreement talks next month',
        'India-GCC trade crosses $160 billion',
        'GCC countries approve unified tourist visa',
        'Gulf Cooperation Council secretary-general meets Jaishankar',
        'GCC ministers discuss Red Sea shipping security',
        'Remittances from GCC nations rise 12%',
        'Saudi Arabia and UAE lead GCC summit on manufacturing',
    )

    CENTRES = (
        'Dubai-based Emirates NBD opens GCC in Chennai, to hire 500',
        'Abu Dhabi bank expands its GCC in Hyderabad',
        'GCC leaders say AI adoption is stalling',
        'NASSCOM GCC Summit: capability centres bet on agentic AI',
    )

    def test_the_bloc_is_never_a_capability_centre(self):
        for title in self.GULF:
            self.assertTrue(gcc_means_gulf(title), title)
            self.assertNotEqual(_tile(title), 'Signal GCC', title)
            self.assertFalse(gcc_axes(title)[1], title)

    def test_a_gulf_company_opening_an_indian_gcc_is_a_gcc_story(self):
        """Stated plainly ("GCC in Chennai", "its GCC"), the centre wins."""
        for title in self.CENTRES:
            self.assertFalse(gcc_means_gulf(title), title)
            self.assertEqual(_tile(title), 'Signal GCC', title)

    def test_gulf_evidence_moves_to_global(self):
        scores = score_signals('Saudi Arabia and UAE lead GCC summit on energy security')
        self.assertEqual(scores['Signal GCC'], 0)
        self.assertGreater(scores['Signal Global'], 0)


# ═════════════════════════════════════════════════════════════════════════════
# 5. SCORING
# ═════════════════════════════════════════════════════════════════════════════

class TestScoring(unittest.TestCase):

    def test_vendor_services_deal_sits_below_the_floor(self):
        """Cleared both axes at 5: a supplier win, which the floor of 6 keeps out."""
        result = _gcc('HCLTech bags AI-led IT transformation deal from M Group')
        if result is not None:
            self.assertGreaterEqual(result[1], SIGNAL_FLOORS['Signal GCC'])

    def test_a_signal_is_tested_against_its_own_floor(self):
        """GCC's higher floor must not swallow an article another signal
        would have taken: eligibility is decided before the winner is."""
        result = classify_article('Insurer opens shared services unit as premiums and claims rise',
                                  'Underwriting and reinsurance review.')
        self.assertIsNotNone(result)

    def test_the_signal_uses_the_rubric_floor_and_vocabulary(self):
        self.assertEqual(SIGNAL_FLOORS['Signal GCC'], MIN_SCORE)
        self.assertEqual(KEYWORDS['Signal GCC'], gcc_vocabulary())

    def test_names_a_centre_is_the_first_gate_for_broad_sources(self):
        """A Moneycontrol headline must name a centre before its page is read."""
        for title in ('Syneos Health opens GCC in Hyderabad',
                      'Airbus opens engineering centres in Bengaluru',
                      'India’s Tier-2 GCC growth brings infrastructure, talent into focus'):
            self.assertTrue(names_a_centre(title), title)
        for title in ('GCC countries approve unified tourist visa',
                      'Infosys wins outsourcing deal from European carmaker',
                      'Govt approves interest-free loan for tobacco farmers'):
            self.assertFalse(names_a_centre(title), title)


if __name__ == '__main__':
    unittest.main()
