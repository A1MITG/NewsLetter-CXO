# tests/test_scraper.py
import unittest

from app.scraper import scraper


class TestScraper(unittest.TestCase):
    def test_module_imports_cleanly(self):
        self.assertTrue(hasattr(scraper, 'run_scraper'))

if __name__ == '__main__':
    unittest.main()
