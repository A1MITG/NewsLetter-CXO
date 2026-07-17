# app/models/article.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# TODO: Define a proper data model for storing articles, scores, and newsletter versions.
# This is a placeholder.

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(255), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=True)
    # ... add other fields for scores, etc.

    def __repr__(self):
        return f'<Article {self.title}>'
