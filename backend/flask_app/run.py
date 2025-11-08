import os
import sys
import logging

# Add backend directory to Python path
backend_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from flask_app.app import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Run the Flask application."""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Create app
    app = create_app()
    
    # Get port from environment or use default
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    logger.info(f"Starting Flask app on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    
    # Run app
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    main()

