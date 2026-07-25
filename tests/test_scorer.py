# tests/test_scorer.py
import unittest

from app.analysis.scorer import score_article


class TestScorer(unittest.TestCase):

    def test_non_insurance_article_is_excluded(self):
        """Articles with no insurance-domain keyword score nothing."""
        result = score_article("Local Bakery Wins Community Award")
        self.assertEqual(result, {})

    def test_regulatory_article_scores_and_flags_urgency(self):
        text = ("Breaking: Major Insurer Faces Regulatory Fine "
                "Over Solvency Breach")
        result = score_article(text)
        self.assertIn('Primary Signal', result)
        primary_category, primary_score = result['Primary Signal']
        self.assertEqual(primary_category, 'Regulatory & Compliance')
        self.assertGreater(primary_score, 0)
        self.assertTrue(result['Urgency Flag'])

    def test_macro_article_scores_without_urgency(self):
        text = ("Global interest rate hikes and geopolitical tensions "
                "weigh on the insurance market")
        result = score_article(text)
        self.assertIn('Primary Signal', result)
        primary_category, _ = result['Primary Signal']
        self.assertEqual(primary_category, 'Macro & Geo-Political')
        self.assertFalse(result['Urgency Flag'])
        self.assertIn('All Scores', result)
        self.assertGreaterEqual(len(result['All Scores']), 1)


if __name__ == '__main__':
    unittest.main()
