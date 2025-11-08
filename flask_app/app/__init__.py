import os
import sys
import logging
from flask import Flask
from flask_cors import CORS

# Add backend directory to Python path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app(config_name=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    from flask_app.config import Config
    app.config.from_object(Config)
    
    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Register blueprints
    from flask_app.app.views.browser_agent import browser_agent_bp
    app.register_blueprint(browser_agent_bp, url_prefix='/api/v1/browser-agent')
    
    logger.info("Flask app initialized successfully")
    
    return app

