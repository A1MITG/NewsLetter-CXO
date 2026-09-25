"""The Featured Analysis picture is shown whole.

The card was a wide strip (about 3.7:1 on a 1896px screen) with the picture
zoomed to fill it (object-fit: cover), so a 3:2 portrait lost its top 30%:
the head (2026-09-25, Marc Rowan). The picture now sits whole beside the
text on navy, and on a phone above it. BP-41 shaped the frame to each
picture; since BP-42 the cards rotate, so the frame is a fixed 16:9 (the
shape most share images come in, so nothing below jumps as they change) and
a picture of another shape sits whole over a blurred copy of itself.
"""
import unittest
from pathlib import Path

from app.main import create_app

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'app' / 'static' / 'command_center_source.html'


class TestFeaturedPicture(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.page = create_app().test_client().get('/').get_data(as_text=True)

    def test_the_picture_is_never_cropped(self):
        self.assertIn('.featured-media img { position: absolute; inset: 0; width: 100%; height: 100%; '
                      'object-fit: contain; }', self.page)
        self.assertNotIn('.featured img {', self.page)

    def test_a_fixed_frame_filled_by_the_picture_itself(self):
        self.assertIn('.featured-media { position: relative; aspect-ratio: 16 / 9;', self.page)
        self.assertIn('.featured-media .featured-fill {', self.page)
        self.assertIn('<img class="featured-fill" src="${esc(f.image)}" alt="" aria-hidden="true"', self.page)

    def test_text_beside_the_picture_not_over_it(self):
        self.assertIn('grid-template-columns: minmax(0, 5fr) minmax(0, 6fr)', self.page)
        self.assertNotIn('.featured::after', self.page)
        card = self.page[self.page.index('<a class="featured${i ?'):]
        card = card[:card.index('</a>')]
        self.assertLess(card.index('class="featured-body"'), card.index('class="featured-media"'))

    def test_on_a_phone_the_picture_goes_on_top(self):
        """The phone rule must follow the base rules it overrides (same specificity)."""
        phone = self.page.index('@media (max-width: 860px) { .featured { grid-template-columns: 1fr;')
        self.assertIn('.featured-media { order: -1; }', self.page[phone:phone + 200])
        self.assertLess(self.page.index('.featured-body h2 { font-family'), phone)

    def test_static_page_carries_the_same_card(self):
        public = (ROOT / 'public' / 'command_center.html').read_text(encoding='utf-8')
        self.assertEqual(public, SOURCE.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
