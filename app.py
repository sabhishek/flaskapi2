from flask import Flask
from flask_restx import Api
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
from config import Config
from core.middleware import TenantMiddleware
from core.database import db
from core.job_manager import JobManager
from api.resources import register_resources

# Load environment variables
load_dotenv()

def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    if not app.config.get('DEV_MODE'):
        db.init_app(app)
        migrate = Migrate(app, db)
    
    # Initialize job manager
    job_manager = JobManager(app)
    app.job_manager = job_manager
    
    # Initialize Flask-RESTX API
    api = Api(
        app,
        version='2.0',
        title='GitOps Infrastructure API',
        description='Declarative infrastructure provisioning via Git with async job processing',
        doc='/docs/',
        prefix='/api/v1'
    )
    
    # Add tenant middleware
    app.wsgi_app = TenantMiddleware(app.wsgi_app)
    
    # Register resource endpoints
    register_resources(api)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)