# app/main.py
import logging

from flask import Flask, jsonify, render_template
from dotenv import load_dotenv

from .api.routes import api_blueprint
from .scraper.store import start_background_refresh
from config.env_check import is_production, validate_environment

load_dotenv()
logging.basicConfig(level=logging.INFO)


def create_app():
    """Create and configure an instance of the Flask application."""
    validate_environment()

    app = Flask(__name__)
    app.config.from_object('config.config.Config')

    app.register_blueprint(api_blueprint, url_prefix='/api')

    # Keep the article cache warm on a timer so no reader ever waits on a
    # scrape, and the news moves on even when nobody is looking. Started on
    # the first request, not at import: the dev server's reloader imports this
    # module in two processes, and starting here would orphan a thread in the
    # parent that scrapes on the same timer as the child's.
    @app.before_request
    def _ensure_refresher():
        start_background_refresh()

    @app.route('/')
    def command_center():
        """The Command Center is the front door: full executive intelligence layout."""
        return render_template('command_center.html')

    @app.route('/brief')
    def brief():
        """Compact five-lens Daily Brief — the low-bandwidth view for mobile/travel."""
        return render_template('index.html')

    @app.route('/signals')
    def signals():
        """Compact terminal-style Signals view — the other low-bandwidth reading view."""
        return render_template('signals.html')

    @app.route('/health')
    def health():
        return jsonify({"status": "ok"})

    return app

# Create app instance for Flask CLI / WSGI servers
app = create_app()

if __name__ == '__main__':
    app.run(debug=not is_production())
