"""Executive Pulse on a phone.

A phone has room for one Pulse card. The row could not be swiped (overflow:
hidden) and relied on its auto-scroll, which added 0.6px to scrollLeft each
frame. Safari keeps scrollLeft to whole pixels, so on an iPhone the row never
moved and only the first card was ever seen (2026-09-25). The row now keeps
its own position, can be swiped, shows the edge of the next card, and has the
same side arrows as the other rows.
"""
import re
import unittest
from pathlib import Path

from app.main import create_app

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'app' / 'static' / 'command_center_source.html'


class TestPulseOnPhones(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.page = create_app().test_client().get('/').get_data(as_text=True)

    def _scroller(self):
        at = self.page.index('id="pulseViewport"')
        start = self.page.rindex('<div class="row-scroller', 0, at)
        end = self.page.index('</button>\n    </div>', at)
        return self.page[start:end]

    def test_the_row_can_be_swiped(self):
        self.assertIn('.pulse-viewport { overflow-x: auto;', self.page)
        self.assertNotIn('.pulse-viewport { overflow: hidden;', self.page)
        self.assertIn('.pulse-viewport::-webkit-scrollbar { display: none; }', self.page)

    def test_the_auto_scroll_keeps_its_own_position(self):
        """Fractional steps accumulate in pos; scrollLeft only receives it."""
        self.assertNotIn('viewport.scrollLeft += 0.6', self.page)
        self.assertIn('pos += 0.6;', self.page)
        self.assertIn('viewport.scrollLeft = pos;', self.page)

    def test_a_swipe_or_an_arrow_is_picked_up_where_it_left_the_row(self):
        self.assertIn('if (Math.abs(viewport.scrollLeft - pos) > 2) pos = viewport.scrollLeft;', self.page)
        self.assertIn("viewport.addEventListener('touchend', release(5000), { passive: true });", self.page)
        self.assertIn("viewport.addEventListener('signal:pause', release(6000));", self.page)

    def test_a_phone_shows_the_edge_of_the_next_card(self):
        self.assertIn('@media (max-width: 640px) { .pulse-card { flex-basis: calc(100% - 48px); } }', self.page)

    def test_the_row_has_both_arrows_hidden_until_measured(self):
        block = self._scroller()
        self.assertIn('aria-label="Scroll Executive Pulse left"', block)
        self.assertIn('aria-label="Scroll Executive Pulse right"', block)
        buttons = re.findall(r'<button type="button" class="row-arrow[^>]*>', block)
        self.assertEqual(len(buttons), 2)
        for button in buttons:
            self.assertIn(' hidden', button)
        self.assertIn("wrap.querySelector('.ribbon, .people-row, .pulse-viewport')", self.page)

    def test_static_page_carries_the_same_row(self):
        public = (ROOT / 'public' / 'command_center.html').read_text(encoding='utf-8')
        self.assertEqual(public, SOURCE.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
