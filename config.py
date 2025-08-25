import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Database
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///school.db'
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    # File uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'mp3', 'wav', 'mp4'}

    # Security
    WTF_CSRF_ENABLED = True
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)

    # Payment Gateway Configuration
    PAYMENT_API_KEY = os.environ.get('PAYMENT_API_KEY')
    PAYMENT_API_URL = os.environ.get('PAYMENT_API_URL')
    PAYMENT_WEBHOOK_URL = os.environ.get('PAYMENT_WEBHOOK_URL')
    PAYMENT_ENABLED = bool(os.environ.get('PAYMENT_ENABLED', 'false').lower() in ['true', '1', 'yes'])