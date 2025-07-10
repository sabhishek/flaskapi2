import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # GitOps Configuration
    GIT_REPO_URL = os.environ.get('GIT_REPO_URL') or 'https://github.com/your-org/infrastructure-manifests.git'
    GIT_BRANCH = os.environ.get('GIT_BRANCH') or 'main'
    GIT_USERNAME = os.environ.get('GIT_USERNAME')
    GIT_PASSWORD = os.environ.get('GIT_PASSWORD')
    
    # ArgoCD Configuration
    ARGOCD_URL = os.environ.get('ARGOCD_URL') or 'https://argocd.example.com'
    ARGOCD_USERNAME = os.environ.get('ARGOCD_USERNAME')
    ARGOCD_PASSWORD = os.environ.get('ARGOCD_PASSWORD')
    ARGOCD_TOKEN = os.environ.get('ARGOCD_TOKEN')
    
    # Template Configuration
    TEMPLATES_DIR = os.environ.get('TEMPLATES_DIR') or 'templates'
    MANIFESTS_DIR = os.environ.get('MANIFESTS_DIR') or 'manifests'
    
    # Tenant Configuration
    TENANT_HEADER = os.environ.get('TENANT_HEADER') or 'X-Tenant-ID'
    REQUIRE_TENANT = os.environ.get('REQUIRE_TENANT', 'true').lower() == 'true'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dev.db'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://user:pass@localhost/proddb'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}