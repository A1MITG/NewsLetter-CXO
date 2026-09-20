# app/scraper/sources.py

# Cleaned sources: reliable RSS feeds only. Dead domains (lifehealthpro,
# insurancegate) and persistent bot-blockers (insurancenewsnet, insuranceerm,
# canadianunderwriter, theinsurer, feedburner mirror) removed 2026-07-18.
#
# 2026-09-20: moneycontrol.com/rss/* dropped. Every Moneycontrol feed still
# returns HTTP 200 but is abandoned upstream — business.xml, latestnews.xml
# and economy.xml are frozen at 23 Apr 2024, MCtopnews.xml at Oct 2016. It was
# the sole source of the April-2024 articles that reached the front page.
# Replaced with Business Standard + ET top stories, both verified same-day.

TIER_1_SOURCES = {
    "Industry & Market Intelligence": [
        "https://www.insurancejournal.com/rss",
        "https://www.businessinsurance.com/rss",
        "https://www.propertycasualty360.com",
        "https://www.claimsjournal.com/rss",
        "https://www.insurancebusinessmag.com",
    ]
}

TIER_2_SOURCES = {
    "North America (US & Canada)": [
        "https://www.nationalunderwriter.com",
        "https://www.thinkadvisor.com",
        "https://www.insurancejournal.com/rss/news",
    ],
    "Global & Emerging Markets": [
        "https://www.reinsurancene.ws/rss",
    ],
    "Geopolitics & Global Affairs": [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://www.theguardian.com/world/rss",
        "https://www.aljazeera.com/xml/rss/all.xml",
    ],
    "India & GCC Business": [
        "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms",
        "https://economictimes.indiatimes.com/rssfeedstopstories.cms",
        "https://www.livemint.com/rss/companies",
        "https://www.business-standard.com/rss/home_page_top_stories.rss",
        "https://timesofindia.indiatimes.com/rssfeeds/1898055.cms",
    ],
}
