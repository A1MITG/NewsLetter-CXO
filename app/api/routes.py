# app/api/routes.py
import logging
from flask import Blueprint, jsonify, request
from ..scraper.store import get_articles
from ..analysis.synthesis import synthesize_articles
from ..analysis.signals import synthesize_signals

logger = logging.getLogger(__name__)
api_blueprint = Blueprint('api', __name__)


@api_blueprint.route('/newsletter', methods=['GET'])
def get_newsletter():
    """
    This endpoint triggers the scraper, analysis, and returns the
    synthesized newsletter.
    """
    try:
        scraped_articles = get_articles(force_refresh='refresh' in request.args)
        logger.info("Serving %d articles for newsletter (daily cache).", len(scraped_articles))

        newsletter_data = synthesize_articles(scraped_articles)
        return jsonify(newsletter_data)
    except Exception:
        logger.exception("Error generating newsletter")
        return jsonify({"error": "Failed to generate newsletter"}), 500


@api_blueprint.route('/signals', methods=['GET'])
def get_signals():
    """Scrape and group articles under the six launch Signals."""
    try:
        scraped_articles = get_articles(force_refresh='refresh' in request.args)
        logger.info("Serving %d articles for signals (daily cache).", len(scraped_articles))
        return jsonify(synthesize_signals(scraped_articles))
    except Exception:
        logger.exception("Error generating signals")
        return jsonify({"error": "Failed to generate signals"}), 500
