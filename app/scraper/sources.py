# app/scraper/sources.py

# Cleaned sources: Reliable RSS feeds for insurance news

TIER_1_SOURCES = {
    "Industry & Market Intelligence": [
        "https://www.insurancejournal.com/rss",
        "https://www.businessinsurance.com/rss",
        "https://www.propertycasualty360.com",
        "https://www.claimsjournal.com/rss",
        "https://www.insurancebusinessmag.com",
        "https://www.insuranceerm.com",
        "https://www.insurancenewsnet.com",
        "https://www.insurancegate.com",
    ]
}

TIER_2_SOURCES = {
    "North America (US & Canada)": [
        "https://www.nationalunderwriter.com",
        "https://www.lifehealthpro.com",
        "https://www.thinkadvisor.com",
        "https://www.canadianunderwriter.ca/rss",
        "https://feeds.feedburner.com/InsuranceNewsNetMagazine",
        "https://www.insurancejournal.com/rss/news",
    ],
    "Global & Emerging Markets": [
        "https://www.reinsurancene.ws/rss",
        "https://www.theinsurer.com/rss",
    ]
}

TIER_3_SOURCES = {
    "Regulatory & Supervisory Bodies": [
        "https://content.naic.org/rss",
    ]
}
