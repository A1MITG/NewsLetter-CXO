# tests/test_scorer.py
import unittest
from app.analysis.scorer import score_article

class TestScorer(unittest.TestCase):

    def test_score_article_high_impact(self):
        """Test scoring for a high-impact article title."""
        article = {'title': 'Breaking: Major Insurer Announces Strategic M&A for Tech Leverage'}
        scores, total_score = score_article(article)
        self.assertGreater(scores['Strategic Impact'], 0)
        self.assertGreater(scores['Technology Leverage'], 0)
        self.assertGreater(total_score, 1)

    def test_score_article_low_impact(self):
        """Test scoring for a low-impact article title."""
        article = {'title': 'Local Agent Wins Community Award'}
        scores, total_score = score_article(article)
        self.assertEqual(total_score, 0)

    def test_score_article_regulatory(self):
        """Test scoring for a regulatory article title."""
        article = {'title': 'New Solvency II Regulation Rules Impact European Insurers'}
        scores, total_score = score_article(article)
        self.assertGreater(scores['Regulatory Impact'], 0)
        self.assertGreater(scores['Risk & Resilience'], 0) # Solvency is a risk keyword
        self.assertGreater(total_score, 1)

if __name__ == '__main__':
    unittest.main()
