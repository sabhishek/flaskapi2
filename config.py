import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Development mode - disables PostgreSQL dependencies
    DEV_MODE = os.environ.get('DEV_MODE', 'false').lower() == 'true'
    
    # Database Configuration
    if DEV_MODE:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://user:pass@localhost/gitops_api'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Redis Configuration for Celery (disabled in dev mode)
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    
    # Git Repository Configuration
    TEMPLATE_REPO_URL = os.environ.get('TEMPLATE_REPO_URL') or 'https://github.com/org/infra-templates.git'
    TEMPLATE_REPO_BRANCH = os.environ.get('TEMPLATE_REPO_BRANCH') or 'main'
    
    # Git Authentication
    GIT_USERNAME = os.environ.get('GIT_USERNAME')
    GIT_PASSWORD = os.environ.get('GIT_PASSWORD')
    
    # Webhook Configuration
    WEBHOOK_TIMEOUT = int(os.environ.get('WEBHOOK_TIMEOUT', '30'))
    WEBHOOK_RETRIES = int(os.environ.get('WEBHOOK_RETRIES', '3'))
    
    # Tenant Configuration
    TENANT_HEADER = os.environ.get('TENANT_HEADER') or 'X-Tenant-ID'
    CLUSTER_HEADER = os.environ.get('CLUSTER_HEADER') or 'X-Cluster-ID'
    REQUIRE_TENANT = os.environ.get('REQUIRE_TENANT', 'true').lower() == 'true'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    DEV_MODE = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    DEV_MODE = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEV_MODE = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}