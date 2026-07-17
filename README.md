# CXO Insurance Intelligence Newsletter App

This application is a proof-of-concept for a modular and maintainable app that curates, scores, and synthesizes insurance intelligence for executive leadership.

## Project Goal

The app aims to provide a high-signal, low-noise intelligence briefing that can be consumed in under 5 minutes, much like a daily brief from a Chief of Staff.

## Architecture

The application is built with a modular structure:

-   `app/`: Main application package.
    -   `scraper/`: Modules for fetching data from various sources.
    -   `analysis/`: Modules for scoring and synthesizing articles.
    -   `api/`: Flask-based API to serve the newsletter data.
    -   `models/`: Data models (currently a placeholder).
    -   `static/`: Static assets (CSS, JS).
    -   `templates/`: HTML templates.
-   `config/`: Configuration files.
-   `scripts/`: Standalone scripts for tasks like running the scraper.
-   `tests/`: Unit and integration tests.

## How to Run

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Flask application:**
    ```bash
    python -m flask run
    ```
    Or for development mode:
    ```bash
    flask --app app/main.py --debug run
    ```

3.  **Access the application:**
    Open your web browser and navigate to `http://127.0.0.1:5000`.

## TODOs and Next Steps

This is an initial version with many areas for improvement. Key TODOs are marked in the code and include:

-   Implementing a robust database schema for storing articles and results.
-   Building a more sophisticated scraping engine, potentially with source-specific selectors and headless browser support.
-   Developing a more advanced NLP-based scoring and synthesis engine.
-   Setting up a background job queue (e.g., Celery) for the scraping and analysis tasks.
-   Adding comprehensive tests.
-   Implementing user authentication and personalization features.
