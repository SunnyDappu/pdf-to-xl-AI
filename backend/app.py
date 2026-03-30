"""
PDF-to-Excel AI Extraction Bot
Main Flask application entry point
"""

from flask import Flask, render_template
from flask_cors import CORS
from utils.config import Config
from api.routes import api_bp
import os

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__, 
                template_folder='../frontend/public',
                static_folder='../frontend/public/static')
    
    # Configuration
    app.config.from_object(Config)
    
    # Enable CORS
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    # Create upload folder
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    
    @app.route('/')
    def index():
        """Serve main app"""
        return render_template('index.html')
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        """Handle file too large error"""
        return {'error': f'File too large. Max size: {Config.MAX_FILE_SIZE / 1000000}MB'}, 413
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        return {'error': 'Resource not found'}, 404
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=(Config.FLASK_ENV == 'development')
    )
