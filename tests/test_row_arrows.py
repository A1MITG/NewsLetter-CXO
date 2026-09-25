"""Side arrows on the Command Center's scrolling rows.

The engine tiles, People Movers and Leaders on Record scroll sideways. Each
showed a scrollbar under it; round arrows on the row's left and right edges
replaced them (2026-09-25). Swipe, trackpad and keyboard scrolling still work.
"""
import re
import unittest
from pathlib import Path

from app.main import create_app

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'app' / 'static' / 'command_center_source.html'

ROWS = {'ribbon': 'the engine tiles', 'moversRow': 'People Movers', 'recordRow': 'Leaders on Record'}


class TestRowArrows(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.page = create_app().test_client().get('/').get_data(as_text=True)

    def _scroller(self, row_id):
        """The .row-scroller block that holds the row with this id."""
        at = self.page.index(f'id="{row_id}"')
        start = self.page.rindex('<div class="row-scroller', 0, at)
        end = self.page.index('</button>\n    </div>', at)
        return self.page[start:end]

    def test_each_scrolling_row_has_both_arrows(self):
        for row_id, label in ROWS.items():
            block = self._scroller(row_id)
            self.assertIn(f'aria-label="Scroll {label} left"', block, row_id)
            self.assertIn(f'aria-label="Scroll {label} right"', block, row_id)
            self.assertEqual(block.count('<button type="button" class="row-arrow'), 2, row_id)

    def test_arrows_start_hidden_until_the_row_is_measured(self):
        """An arrow shows only when there is more that way; the script decides."""
        for row_id in ROWS:
            for button in re.findall(r'<button type="button" class="row-arrow[^>]*>', self._scroller(row_id)):
                self.assertIn(' hidden', button)

    def test_the_scrollbars_are_gone(self):
        self.assertIn('.ribbon, .people-row { scrollbar-width: none; }', self.page)
        self.assertIn('.ribbon::-webkit-scrollbar, .people-row::-webkit-scrollbar { display: none; }', self.page)

    def test_the_drifting_row_pauses_for_its_arrows(self):
        self.assertIn("rib.addEventListener('signal:pause', nudge(6000));", self.page)
        self.assertIn("row.dispatchEvent(new Event('signal:pause'));", self.page)

    def test_arrows_are_wired(self):
        self.assertIn('function initRowArrows()', self.page)
        self.assertIn('initRowArrows();', self.page)

    def test_static_page_carries_the_same_arrows(self):
        public = (ROOT / 'public' / 'command_center.html').read_text(encoding='utf-8')
        self.assertEqual(public, SOURCE.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
