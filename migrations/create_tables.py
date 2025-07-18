import os
import sys

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from core.database import db, Resource, ResourceOperation

def create_tables(app):
    """Create database tables"""
    with app.app_context():
        db.create_all()
        print("Database tables created successfully")

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    create_tables(app)