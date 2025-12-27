import os
from pathlib import Path

basedir = Path(__file__).parent


class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{basedir / "instance" / "cdc_pr.db"}'
    
    # SharePoint
    SHAREPOINT_SITE_URL = os.environ.get('SHAREPOINT_SITE_URL', '')
    SHAREPOINT_USERNAME = os.environ.get('SHAREPOINT_USERNAME', '')
    SHAREPOINT_PASSWORD = os.environ.get('SHAREPOINT_PASSWORD', '')
    SHAREPOINT_ROOT_FOLDER = os.environ.get('SHAREPOINT_ROOT_FOLDER', 'CDC-PR-Cases')
    
    # Application
    CASE_NUMBER_PREFIX = os.environ.get('CASE_NUMBER_PREFIX', 'CDC-PR')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
    
    # Local storage fallback (when SharePoint is not configured)
    LOCAL_STORAGE_PATH = basedir / "instance" / "storage"


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
