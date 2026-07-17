# app/api/routes.py
import asyncio
import logging
from datetime import datetime
from flask import Blueprint, jsonify
from ..scraper.scraper import run_scraper
from ..analysis.synthesis import synthesize_articles

api_blueprint = Blueprint('api', __name__)

logging.basicConfig(level=logging.INFO)

@api_blueprint.route('/newsletter', methods=['GET'])
def get_newsletter():
    """
    This endpoint triggers the scraper, analysis, and returns the
    synthesized newsletter.
    """
    logging.info("Received request for newsletter.")
    try:
        # In a production environment, this would be a scheduled task,
        # not a synchronous API call.
        # TODO: Implement a background job queue (e.g., Celery).
        logging.info("Starting scraper...")
        scraped_articles = asyncio.run(run_scraper(tier='all'))
        logging.info(f"Scraper found {len(scraped_articles)} articles.")
        
        logging.info("Starting synthesis...")
        newsletter_data = synthesize_articles(scraped_articles)
        logging.info("Synthesis complete.")
        
        # Debug: check if any data
        has_data = any(len(v) > 0 for k, v in newsletter_data.items() if k not in ['date', 'executive_takeaway', 'cxo_action_lens'])
        logging.info(f"Has data: {has_data}")
        
        if not has_data:
            logging.info("No data, returning mock")
            newsletter_data = {
                'date': datetime.now().strftime('%B %d, %Y'),
                'Macro & Geo-Political': [{'signal': 'Sample Macro Signal', 'impact': 'Test impact', 'metlife_exposure': 'Test exposure', 'url': '#', 'score': 0, 'primary_cxo': 'CEO'}],
                'executive_takeaway': 'Sample takeaway',
                'cxo_action_lens': ['Watch sample', 'Prepare sample']
            }
        
        return jsonify(newsletter_data)
    except Exception as e:
        logging.error(f"Error generating newsletter: {e}", exc_info=True)
        return jsonify({"error": "Failed to generate newsletter"}), 500
