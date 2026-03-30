import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # File upload
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 500000000))  # 500MB
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # OCR
    TESSERACT_PATH = os.getenv('TESSERACT_PATH', r'C:/Program Files/Tesseract-OCR/tesseract.exe')
    
    # Server
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # Processing
    MAX_CHUNK_TOKENS = int(os.getenv('MAX_CHUNK_TOKENS', 50000))
    CHUNK_PAGE_SIZE = int(os.getenv('CHUNK_PAGE_SIZE', 10))
    
    # Language
    INPUT_LANGUAGE = os.getenv('INPUT_LANGUAGE', 'english')
    OUTPUT_LANGUAGE = os.getenv('OUTPUT_LANGUAGE', 'english')
    AUTO_TRANSLATE = os.getenv('AUTO_TRANSLATE', 'false').lower() == 'true'

# Ensure upload folder exists
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
