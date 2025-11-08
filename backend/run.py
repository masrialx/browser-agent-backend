#!/usr/bin/env python3
"""
Main entry point for the Browser Automation Backend Application.

This file serves as the main entry point to run the Flask application.
It can be executed directly from the backend directory.

Usage:
    python run.py
    python run.py --port 5000
    python run.py --host 0.0.0.0 --port 5000
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add current directory to Python path
backend_dir = os.path.abspath(os.path.dirname(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import Flask app creation function
from flask_app.app import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run the Browser Automation Backend Application')
    parser.add_argument(
        '--host',
        type=str,
        default=os.getenv('HOST', '0.0.0.0'),
        help='Host to bind to (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=int(os.getenv('PORT', 5000)),
        help='Port to bind to (default: 5000)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        default=os.getenv('DEBUG', 'False').lower() == 'true',
        help='Enable debug mode'
    )
    parser.add_argument(
        '--reload',
        action='store_true',
        help='Enable auto-reload on code changes'
    )
    return parser.parse_args()

def main():
    """Main function to run the Flask application."""
    # Load environment variables
    from dotenv import load_dotenv
    
    # Try to load .env from backend directory
    env_path = Path(backend_dir) / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Loaded environment variables from {env_path}")
    else:
        # Try loading from flask_app directory
        flask_app_env = Path(backend_dir) / 'flask_app' / '.env'
        if flask_app_env.exists():
            load_dotenv(flask_app_env)
            logger.info(f"Loaded environment variables from {flask_app_env}")
        else:
            load_dotenv()  # Try default locations
            logger.info("Using default environment variable locations")
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Check for required environment variables
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        logger.warning("GEMINI_API_KEY not found in environment variables. Some features may not work.")
        logger.warning("Please set GEMINI_API_KEY in your .env file or environment variables.")
    else:
        logger.info("GEMINI_API_KEY found in environment variables")
    
    # Create Flask app
    try:
        app = create_app()
        logger.info("Flask app created successfully")
    except Exception as e:
        logger.error(f"Failed to create Flask app: {e}", exc_info=True)
        sys.exit(1)
    
    # Get configuration
    host = args.host
    port = args.port
    debug = args.debug or args.reload
    
    logger.info("=" * 60)
    logger.info("Browser Automation Backend Application")
    logger.info("=" * 60)
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Auto-reload: {args.reload}")
    logger.info("=" * 60)
    logger.info(f"API Endpoint: http://{host}:{port}/api/v1/browser-agent/execute")
    logger.info(f"Health Check: http://{host}:{port}/api/v1/browser-agent/health")
    logger.info("=" * 60)
    
    # Run the application
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=args.reload
        )
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Error running application: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

