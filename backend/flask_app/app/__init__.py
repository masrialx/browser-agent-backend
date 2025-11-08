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
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint for monitoring."""
        return {
            'status': 'healthy',
            'service': 'browser-agent-api',
            'version': '1.0.0'
        }, 200
    
    # Root endpoint
    @app.route('/', methods=['GET'])
    def root():
        """Root endpoint."""
        return {
            'service': 'Browser Agent API',
            'version': '1.0.0',
            'endpoints': {
                'health': '/health',
                'execute': '/api/v1/browser-agent/execute'
            }
        }, 200
    
    logger.info("Flask app initialized successfully")
    
    return app

