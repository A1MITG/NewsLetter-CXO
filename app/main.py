# app/main.py
from flask import Flask, render_template
from .api.routes import api_blueprint
from .models.article import db
from dotenv import load_dotenv

load_dotenv()

def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)
    app.config.from_object('config.config.Config')
    db.init_app(app)

    app.register_blueprint(api_blueprint, url_prefix='/api')

    @app.route('/')
    def index():
        # This will be replaced by a call to the synthesis module
        # to get the latest newsletter data.
        # For now, it just renders a template.
        return render_template('index.html', newsletter_data={})

    @app.route('/themes')
    def themes():
        return render_template('themes.html')

    return app

# Create app instance for Flask CLI
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
