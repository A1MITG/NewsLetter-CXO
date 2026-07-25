# app/scraper/sources.py

# Cleaned sources: reliable RSS feeds only. Dead domains (lifehealthpro,
# insurancegate) and persistent bot-blockers (insurancenewsnet, insuranceerm,
# canadianunderwriter, theinsurer, feedburner mirror) removed 2026-07-18.

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
        "https://www.livemint.com/rss/companies",
        "https://www.moneycontrol.com/rss/business.xml",
        "https://timesofindia.indiatimes.com/rssfeeds/1898055.cms",
    ],
}
