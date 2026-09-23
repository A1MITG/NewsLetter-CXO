"""Share-image recovery for feed items that carried no picture (offline)."""
from app.scraper import article_images as ai


def setup_function(_):
    ai._seen.clear()


def test_reads_og_image_in_either_attribute_order():
    html = ('<meta content="https://x.com/a.jpg" property="og:image" />'
            '<meta name="twitter:image" content="https://x.com/b.jpg">')
    assert ai.share_image(html) == 'https://x.com/a.jpg'


def test_falls_back_to_twitter_image():
    assert ai.share_image('<meta name="twitter:image" content="https://x.com/b.jpg">') \
        == 'https://x.com/b.jpg'


def test_publisher_logo_cards_are_generic():
    # The two real defaults that left the Insurance tile imageless.
    assert ai.is_generic('https://www.insurancejournal.com/img/social/opengraph/ij-social-default-1200x630.png')
    assert ai.is_generic('https://www.businessinsurance.com/wp-content/uploads/2023/03/cropped-BI-square-blue.png')
    assert not ai.is_generic('https://www.businessinsurance.com/wp-content/uploads/2026/09/Chubb-2.jpg')


def test_fills_only_missing_and_drops_images_shared_across_stories():
    articles = [
        {'url': 'https://p/1', 'image': ''},
        {'url': 'https://p/2', 'image': None},
        {'url': 'https://p/3'},
        {'url': 'https://p/4', 'image': 'https://feed/own.jpg'},
    ]
    served = {'https://p/1': 'https://p/story1.jpg',
              'https://p/2': 'https://p/masthead.png',
              'https://p/3': 'https://p/masthead.png'}
    asked = []

    def fetch(urls):
        asked.extend(urls)
        return [(u, served[u]) for u in urls]

    assert ai.fill_missing_images(articles, fetch=fetch) == 1
    assert sorted(asked) == ['https://p/1', 'https://p/2', 'https://p/3']
    assert articles[0]['image'] == 'https://p/story1.jpg'
    assert not articles[1]['image'] and 'image' not in articles[2]
    assert articles[3]['image'] == 'https://feed/own.jpg'


def test_disabled_by_env_never_touches_the_network(monkeypatch):
    monkeypatch.setenv('FETCH_ARTICLE_IMAGES', '0')
    assert ai.fill_missing_images([{'url': 'https://p/1'}]) == 0
