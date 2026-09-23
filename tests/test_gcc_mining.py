"""The keyword miner's two gates, proven on a synthetic history.

The live store needs weeks to reach a usable pool, so these build one
directly. The cases that matter are the ones the rubric got wrong by hand:
a frequent place name must never be proposed, and a term that genuinely
describes a capability centre must be.
"""
import unittest

from app.intelligence.gcc_mining import (MIN_SUPPORT, demotions, mine)


def _gcc(title, summary=''):
    return {'signal': 'Signal GCC', 'title': title, 'summary': summary,
            'url': 'https://example.com/' + str(abs(hash(title)))}


def _other(title, summary=''):
    return {'signal': 'Signal Global', 'title': title, 'summary': summary,
            'url': 'https://example.com/' + str(abs(hash(title)))}


class TestPoolSize(unittest.TestCase):

    def test_refuses_to_mine_a_pool_that_is_too_small(self):
        """A ranking off two articles is a number someone would act on."""
        records = [_gcc('Acme opens global capability centre')] * 2
        candidates, stats = mine(records)
        self.assertFalse(stats['ready'])
        self.assertEqual(candidates, [])

    def test_reports_what_it_has(self):
        records = [_gcc('Acme opens global capability centre')] + \
                  [_other('Unrelated story %d' % i) for i in range(4)]
        _candidates, stats = mine(records)
        self.assertEqual(stats['confirmed_gcc'], 1)
        self.assertEqual(stats['rest'], 4)
        self.assertEqual(stats['min_support'], MIN_SUPPORT)


class TestGates(unittest.TestCase):
    """The defect this module exists to avoid re-creating."""

    def _corpus(self):
        # Six confirmed GCC stories. Every one mentions Noida, and every one
        # also uses the word "charter" beside a capability centre. Frequency
        # alone cannot tell these apart -- both appear in 6 of 6.
        positives = [
            _gcc('Acme opens global capability centre in Noida',
                 'The charter covers engineering and analytics.'),
            _gcc('Beta sets up global capability centre near Noida',
                 'A broad charter spanning product and platform work.'),
            _gcc('Gamma establishes capability centre, Noida site chosen',
                 'Its charter includes end-to-end ownership.'),
            _gcc('Delta launches global capability centre outside Noida',
                 'The charter will expand next year.'),
            _gcc('Epsilon opens capability centre in Noida',
                 'Leaders described the charter as strategic.'),
            _gcc('Zeta sets up global capability centre, Noida',
                 'The charter grows to include design.'),
        ]
        # Noida is just as common in news that is not about capability
        # centres. "charter" is not.
        negatives = [
            _other('Noida authority clears new residential towers'),
            _other('Noida expressway widening approved'),
            _other('Property prices climb across Noida and Greater Noida'),
            _other('Noida metro extension gets funding'),
            _other('Retailer opens flagship store in Noida'),
            _other('Noida hospital adds two hundred beds'),
            _other('Cricket stadium proposed for Noida'),
            _other('Noida civic body announces budget'),
        ]
        return positives + negatives

    def test_a_frequent_place_name_is_not_proposed(self):
        """'noida' appears in 6 of 6 GCC stories and is still rejected.

        This is the exact term that put a real-estate story at the top of the
        live tile. Lift catches it: it is equally at home outside GCC news.
        """
        candidates, stats = mine(self._corpus())
        self.assertTrue(stats['ready'])
        self.assertNotIn('noida', [c['term'] for c in candidates])
        self.assertNotIn('greater noida', [c['term'] for c in candidates])

    def test_a_genuinely_directed_term_is_proposed(self):
        """'charter' rides with the centre, not merely near it."""
        candidates, _stats = mine(self._corpus())
        terms = [c['term'] for c in candidates]
        self.assertIn('charter', terms)

    def test_a_proposal_carries_its_evidence(self):
        candidates, _stats = mine(self._corpus())
        charter = next(c for c in candidates if c['term'] == 'charter')
        self.assertGreaterEqual(charter['lift'], 3.0)
        self.assertGreaterEqual(charter['cooccurrence'], 0.6)
        self.assertGreaterEqual(charter['support'], MIN_SUPPORT)
        self.assertTrue(charter['samples'])
        self.assertIn(charter['facet'],
                      {'entity', 'new_build', 'expansion', 'coe_standup',
                       'augment_capability', 'new_development', 'talent_scale'})

    def test_weight_four_is_never_proposed(self):
        """Naming what counts as a capability centre stays a human call."""
        candidates, _stats = mine(self._corpus())
        for c in candidates:
            self.assertLessEqual(c['weight'], 3)

    def test_terms_already_live_are_not_re_proposed(self):
        candidates, _stats = mine(self._corpus())
        terms = [c['term'] for c in candidates]
        for live in ('global capability centre', 'opens', 'expansion'):
            self.assertNotIn(live, terms)

    def test_a_term_below_cooccurrence_is_rejected(self):
        """Appears often in GCC stories, but never beside a centre."""
        positives = [
            _gcc('Acme opens global capability centre', 'Quarterly monsoon update.'),
            _gcc('Beta opens global capability centre', 'Quarterly monsoon update.'),
            _gcc('Gamma opens global capability centre', 'Quarterly monsoon update.'),
        ] + [
            # three more where the term appears WITHOUT any decisive entity
            {'signal': 'Signal GCC', 'url': 'u%d' % i,
             'title': 'Firm %d expands offshoring team' % i,
             'summary': 'Quarterly monsoon update.'} for i in range(4)
        ]
        negatives = [_other('Unrelated %d' % i) for i in range(10)]
        candidates, stats = mine(positives + negatives)
        self.assertTrue(stats['ready'])
        self.assertNotIn('monsoon', [c['term'] for c in candidates])


class TestProperNouns(unittest.TestCase):

    def test_capitalised_names_are_rejected(self):
        """Company and person names are exactly what must not be proposed."""
        positives = [
            _gcc('Acme opens global capability centre',
                 'Hexaworth Consulting advised on the Hexaworth mandate.'),
        ] * 3 + [
            _gcc('Beta sets up global capability centre',
                 'Hexaworth Consulting advised on the Hexaworth mandate.'),
        ] * 3
        negatives = [_other('Unrelated story %d' % i) for i in range(10)]
        candidates, _stats = mine(positives + negatives)
        self.assertNotIn('hexaworth', [c['term'] for c in candidates])


class TestDemotions(unittest.TestCase):

    def test_a_live_keyword_losing_discrimination_is_flagged(self):
        """The automated form of the review that caught 'noida' by hand.

        'outsourcing' is a live weight-2 entity term. Here it appears in one
        GCC story and many non-GCC ones, so it has stopped discriminating.
        """
        positives = [_gcc('Firm %d opens global capability centre' % i)
                     for i in range(6)]
        positives[0]['summary'] = 'An outsourcing arrangement ends.'
        negatives = [_other('Retail outsourcing deal signed %d' % i,
                            'More outsourcing news.') for i in range(12)]
        flagged = demotions(positives + negatives)
        self.assertIn('outsourcing', [f['term'] for f in flagged])

    def test_nothing_is_flagged_when_the_pool_is_too_small(self):
        self.assertEqual(demotions([_gcc('Acme opens capability centre')]), [])


if __name__ == '__main__':
    unittest.main()
