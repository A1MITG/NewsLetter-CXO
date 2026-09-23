"""Cyber: the fifth tile-only domain, replacing a "coming soon" tile.

Same rules as Defence: the headline must name it, a floor of 5 keeps weak
words ("privacy", "breach", "scam") from qualifying alone, everyday senses of
its words are blanked, and companies appear only in unambiguous forms. Cyber
insurance stays with Insurance.
"""
import unittest

from app.analysis.command_center import COMING_SOON_ENGINES, SIGNAL_TO_ENGINE
from app.analysis.signals import SIGNALS, classify_article, synthesize_signals


def tile(title, summary=''):
    result = classify_article(title, summary, include_tile_signals=True)
    return result[0] if result else None


class TestCyberClassifies(unittest.TestCase):
    """Headlines from the 2026-09-23 scan, and the shapes around them."""

    def test_breach(self):
        self.assertEqual(tile("FBI investigates breach of jobs website as hackers claim 'very sensitive data' stolen"),
                         'Signal Cyber')

    def test_security_industry_moves_from_ai(self):
        self.assertEqual(tile('Palo Alto Networks unveils AI-powered cybersecurity service using Claude, GPT models'),
                         'Signal Cyber')

    def test_cyber_defence_from_defence(self):
        """Defence blanks "cyber defence" and leaves it to this tile."""
        self.assertEqual(tile('OpenAI gives cyber defence tools to Ukraine'), 'Signal Cyber')

    def test_ransomware(self):
        self.assertEqual(tile('Ransomware attack shuts hospital systems across three states'), 'Signal Cyber')


class TestCyberLeavesOtherTilesTheirStories(unittest.TestCase):

    def test_cyber_insurance_is_insurance(self):
        self.assertNotEqual(tile('Cyber insurance premiums fall as underwriters compete for share'),
                            'Signal Cyber')

    def test_privacy_alone_is_not_enough(self):
        self.assertNotEqual(tile('Meta leans into AI, smart glasses amid privacy pushback'), 'Signal Cyber')

    def test_breach_of_contract(self):
        self.assertNotEqual(tile('Supplier sues retailer for breach of contract over unpaid invoices'),
                            'Signal Cyber')

    def test_everyday_senses(self):
        self.assertNotEqual(tile('Cyber Monday sales hit record as shoppers chase life hacks'), 'Signal Cyber')


class TestCyberNeedsItsHeadline(unittest.TestCase):

    def test_hackers_only_in_the_summary(self):
        result = tile('Retailer shares slide after weak quarterly results',
                      'The company also disclosed that hackers had accessed some customer records.')
        self.assertNotEqual(result, 'Signal Cyber')


class TestSignalsPageUnchanged(unittest.TestCase):

    def test_without_the_flag_cyber_never_wins(self):
        result = classify_article('Ransomware attack shuts hospital systems across three states')
        self.assertTrue(result is None or result[0] != 'Signal Cyber')

    def test_signals_page_output_keeps_six(self):
        out = synthesize_signals([], require_current=False)
        self.assertEqual([s['name'] for s in out['signals']], [s['name'] for s in SIGNALS])


class TestCyberTileIsLive(unittest.TestCase):

    def test_cyber_maps_to_its_tile(self):
        self.assertEqual(SIGNAL_TO_ENGINE['Signal Cyber'], ('cyber', 'Cyber Intelligence'))

    def test_cyber_is_no_longer_coming_soon(self):
        self.assertNotIn('cyber', COMING_SOON_ENGINES)


if __name__ == '__main__':
    unittest.main()
