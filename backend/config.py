import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32).hex()
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{os.environ.get("DATABASE_PATH", "/app/data/masina_dock.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    DISABLE_SIGNUPS = os.environ.get('DISABLE_SIGNUPS', 'False').lower() == 'true'
    
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@masinadock.local')
    
    ENABLE_EMAIL_VERIFICATION = os.environ.get('ENABLE_EMAIL_VERIFICATION', 'False').lower() == 'true'
    ENABLE_2FA = os.environ.get('ENABLE_2FA', 'True').lower() == 'true'
