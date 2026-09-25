"""The engine tiles are on screen when the Command Center loads.

On a 1366 x 768 laptop the tiles used to open at 514px and end below the
fold, with their headlines (which sit at the foot of each tile) out of view;
on a phone they opened at 614px of 844. The hero was compacted and the
pin / hide / drag bar, with its long note, folded into the engines header
line (2026-09-25), so the whole first row shows at load.
"""
import re
import unittest

from app.main import create_app


class TestLandingFold(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.page = create_app().test_client().get('/').get_data(as_text=True)

    def _css(self, selector):
        match = re.search(re.escape(selector) + r' \{([^}]*)\}', self.page)
        self.assertIsNotNone(match, selector)
        return match.group(1)

    def test_the_hero_no_longer_takes_a_third_of_the_screen(self):
        hero = self._css('.hero')
        self.assertNotIn('min-height', hero)
        self.assertIn('padding: 10px 0 2px', hero)
        self.assertIn('min-height: 44px', self._css('.hero-stage'))

    def test_the_layout_tools_sit_on_the_engines_header_line(self):
        head = self.page[self.page.index('<div id="engines" class="band-head">'):self.page.index('<div class="row-scroller ribbon-wrap">')]
        self.assertIn('<span class="engine-tools">', head)
        self.assertIn('drag to reorder', head)
        self.assertIn('<button class="persona-reset" id="personaReset">Reset layout</button>', head)
        self.assertNotIn('persona-bar', self.page)
        self.assertNotIn('persona-note', self.page)

    def test_where_a_layout_is_saved_is_still_explained(self):
        self.assertIn('Your pins, hides and order are saved in this browser only.', self.page)
        self.assertIn('aria-label="Your layout is saved in this browser only"', self.page)


if __name__ == '__main__':
    unittest.main()
