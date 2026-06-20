# =======================================================
# Al-Khwarizmi University Recruitment Portal
# Designed & Developed by: Omonbayev Jaloliddin
# Telegram: https://t.me/jaloliddin_omonbaev
# =======================================================

import os
from dotenv import load_dotenv

# Load variables from .env file if it exists
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'akhu-secret-key-change-in-production-123')
    
    # Database (Fallback to SQLite if no PostgreSQL database is specified)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "akhu_recruitment.db")}')
    # If the URL starts with postgres://, replace it with postgresql:// for SQLAlchemy compatibility
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20 Megabytes limit
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}
    
    # Languages / Babel
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_DEFAULT_TIMEZONE = 'Asia/Tashkent'
