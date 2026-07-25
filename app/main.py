# app/main.py
import logging

from flask import Flask, jsonify, render_template
from dotenv import load_dotenv

from .api.routes import api_blueprint
from config.env_check import is_production, validate_environment

load_dotenv()
logging.basicConfig(level=logging.INFO)


def create_app():
    """Create and configure an instance of the Flask application."""
    validate_environment()

    app = Flask(__name__)
    app.config.from_object('config.config.Config')

    app.register_blueprint(api_blueprint, url_prefix='/api')

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/signals')
    def signals():
        return render_template('signals.html')

    @app.route('/health')
    def health():
        return jsonify({"status": "ok"})

    return app

# Create app instance for Flask CLI / WSGI servers
app = create_app()

if __name__ == '__main__':
    app.run(debug=not is_production())
