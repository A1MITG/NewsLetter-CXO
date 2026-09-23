"""The rubric table in app/analysis/signals.py stays complete and consistent.

Guards for whoever edits a rubric next: every Signal has exactly one rubric
and one place in PRIORITY, and the tables the scoring code reads are derived
from the rubrics rather than kept by hand.
"""
import unittest

from app.analysis.signals import (KEYWORDS, NEUTRALIZE, PRIORITY, RUBRICS, SIGNAL_FLOORS,
                                  SIGNALS, THRESHOLD, TILE_SIGNALS, TITLE_REQUIRED, Rubric)

NAMES = [s['name'] for s in SIGNALS + TILE_SIGNALS]


class TestEverySignalHasOneRubric(unittest.TestCase):

    def test_rubrics_match_the_signal_list(self):
        self.assertEqual(list(RUBRICS), NAMES)

    def test_priority_lists_every_signal_once(self):
        self.assertEqual(sorted(PRIORITY), sorted(NAMES))

    def test_every_rubric_has_keywords(self):
        for name, rubric in RUBRICS.items():
            self.assertTrue(rubric.keywords, name)


class TestTablesComeFromTheRubrics(unittest.TestCase):

    def test_keywords(self):
        for name in NAMES:
            self.assertIs(KEYWORDS[name], RUBRICS[name].keywords)

    def test_settings(self):
        for name, rubric in RUBRICS.items():
            self.assertEqual(SIGNAL_FLOORS[name], rubric.min_score)
            self.assertEqual(name in TITLE_REQUIRED, rubric.headline_must_match)
            self.assertEqual(name in NEUTRALIZE, bool(rubric.ignore))

    def test_no_signal_is_easier_than_the_shared_threshold(self):
        for name, rubric in RUBRICS.items():
            self.assertGreaterEqual(rubric.min_score, THRESHOLD, name)

    def test_every_tile_needs_its_headline(self):
        for s in TILE_SIGNALS:
            self.assertTrue(RUBRICS[s['name']].headline_must_match, s['name'])


class TestRubricRejectsMistakes(unittest.TestCase):

    def test_upper_case_keyword(self):
        with self.assertRaises(ValueError):
            Rubric(headline_must_match=False, min_score=3, keywords={'Pfizer': 4})

    def test_points_out_of_range(self):
        with self.assertRaises(ValueError):
            Rubric(headline_must_match=False, min_score=3, keywords={'pfizer': 5})


if __name__ == '__main__':
    unittest.main()
