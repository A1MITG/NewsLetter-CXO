"""The cache must expire, so an afternoon reader sees afternoon news.

Before this, get_articles() kept one snapshot per calendar day: whatever the
first visitor triggered was served until midnight.
"""
import json
import unittest
from datetime import date, datetime, timedelta, timezone
from unittest import mock

from app.scraper import store


class TestCacheFreshness(unittest.TestCase):

    def _cache(self, minutes_ago=None, on_date=None):
        c = {'articles': [{'title': 'x'}]}
        if minutes_ago is not None:
            c['fetched_at'] = (datetime.now(timezone.utc)
                               - timedelta(minutes=minutes_ago)).isoformat()
        if on_date is not None:
            c['date'] = on_date
        return c

    def test_cache_inside_ttl_is_fresh(self):
        self.assertTrue(store._is_fresh(self._cache(minutes_ago=1)))

    def test_cache_past_ttl_is_stale(self):
        stale = store.CACHE_TTL_MINUTES + 1
        self.assertFalse(store._is_fresh(self._cache(minutes_ago=stale)))

    def test_missing_cache_is_stale(self):
        self.assertFalse(store._is_fresh(None))

    def test_legacy_cache_without_timestamp_falls_back_to_date(self):
        """Pre-TTL files carry only a date; same-day is trusted, older is not."""
        today = date.today().isoformat()
        self.assertTrue(store._is_fresh(self._cache(on_date=today)))
        self.assertFalse(store._is_fresh(self._cache(on_date='2024-04-23')))

    def test_corrupt_timestamp_is_treated_as_stale(self):
        self.assertFalse(store._is_fresh({'fetched_at': 'not-a-date',
                                          'articles': []}))
    def test_expired_cache_triggers_a_rescrape(self):
        expired = self._cache(minutes_ago=store.CACHE_TTL_MINUTES + 5)
        with mock.patch.object(store, '_load', return_value=expired),              mock.patch.object(store, '_save'),              mock.patch.object(store, 'run_scraper'),              mock.patch.object(store.asyncio, 'run',
                               return_value=[{'title': 'fresh'}]) as run:
            out = store.get_articles()
        run.assert_called_once()
        self.assertEqual(out, [{'title': 'fresh'}])

    def test_warm_cache_does_not_scrape(self):
        warm = self._cache(minutes_ago=0)
        with mock.patch.object(store, '_load', return_value=warm),              mock.patch.object(store.asyncio, 'run') as run:
            store.get_articles()
        run.assert_not_called()

    def test_failed_scrape_serves_previous_cache_not_an_empty_page(self):
        """Sources down must not blank the page."""
        expired = self._cache(minutes_ago=store.CACHE_TTL_MINUTES + 5)
        with mock.patch.object(store, '_load', return_value=expired),              mock.patch.object(store, '_save'),              mock.patch.object(store, 'run_scraper'),              mock.patch.object(store.asyncio, 'run', return_value=[]):
            out = store.get_articles()
        self.assertEqual(out, expired['articles'])


if __name__ == '__main__':
    unittest.main()


class TestBackgroundRefresh(unittest.TestCase):
    """The cache must move on even when nobody is looking."""

    def setUp(self):
        store._refresher_started = False

    def tearDown(self):
        store._refresher_started = False

    def test_disabled_by_env_flag(self):
        with mock.patch.object(store, 'BACKGROUND_REFRESH', False), \
             mock.patch.object(store.threading, 'Thread') as thread:
            store.start_background_refresh()
        thread.assert_not_called()

    def test_starts_a_daemon_thread_when_enabled(self):
        with mock.patch.object(store, 'BACKGROUND_REFRESH', True), \
             mock.patch.object(store.threading, 'Thread') as thread:
            store.start_background_refresh()
        thread.assert_called_once()
        self.assertTrue(thread.call_args.kwargs['daemon'],
                        "refresher must not hold up shutdown")

    def test_is_idempotent(self):
        """A second call must not start a second scraping thread."""
        with mock.patch.object(store, 'BACKGROUND_REFRESH', True), \
             mock.patch.object(store.threading, 'Thread') as thread:
            store.start_background_refresh()
            store.start_background_refresh()
        thread.assert_called_once()
