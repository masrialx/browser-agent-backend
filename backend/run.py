#!/usr/bin/env python3
"""
Production-ready run script for the Browser Agent Flask API.

This script is designed for production deployment with:
- Proper logging configuration
- Environment variable management
- Error handling
- Graceful shutdown
- Health checks
"""

import os
import sys
import logging
import signal
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(backend_dir))

# Configure logging before importing app
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log') if os.path.exists('app.log') or os.access('.', os.W_OK) else logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def setup_environment():
    """Load environment variables from .env file if it exists."""
    try:
        from dotenv import load_dotenv
        env_path = backend_dir / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(f"Loaded environment variables from {env_path}")
        else:
            logger.warning(f".env file not found at {env_path}. Using system environment variables.")
    except ImportError:
        logger.warning("python-dotenv not installed. Environment variables must be set manually.")
    except Exception as e:
        logger.error(f"Error loading environment variables: {e}")

def check_required_env_vars():
    """Check that required environment variables are set."""
    required_vars = ['GEMINI_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables in your .env file or environment.")
        return False
    
    return True

def create_app():
    """Create and configure the Flask application."""
    try:
        # Import after path setup
        from flask_app.app import create_app as flask_create_app
        app = flask_create_app()
        return app
    except Exception as e:
        logger.error(f"Error creating Flask app: {e}", exc_info=True)
        raise

def setup_signal_handlers(app):
    """Setup signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}. Shutting down gracefully...")
        # Flask's development server handles shutdown automatically
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def run_production_server(app, host='0.0.0.0', port=5000, debug=False):
    """Run the Flask application in production mode."""
    try:
        logger.info("=" * 60)
        logger.info("Starting Browser Agent Flask API Server")
        logger.info("=" * 60)
        logger.info(f"Host: {host}")
        logger.info(f"Port: {port}")
        logger.info(f"Debug Mode: {debug}")
        logger.info(f"Environment: {os.getenv('FLASK_ENV', 'production')}")
        logger.info("=" * 60)
        
        # Run the application
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True,  # Enable multi-threading
            use_reloader=False  # Disable reloader in production
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error running server: {e}", exc_info=True)
        raise

def run_with_waitress(app, host='0.0.0.0', port=5000, threads=4):
    """Run the Flask application using Waitress WSGI server (production)."""
    try:
        from waitress import serve
        logger.info("=" * 60)
        logger.info("Starting Browser Agent Flask API Server (Waitress)")
        logger.info("=" * 60)
        logger.info(f"Host: {host}")
        logger.info(f"Port: {port}")
        logger.info(f"Threads: {threads}")
        logger.info("=" * 60)
        
        serve(app, host=host, port=port, threads=threads)
    except ImportError:
        logger.warning("Waitress not installed. Install with: pip install waitress")
        logger.info("Falling back to Flask development server...")
        run_production_server(app, host=host, port=port, debug=False)
    except Exception as e:
        logger.error(f"Error running Waitress server: {e}", exc_info=True)
        raise

def run_with_gunicorn(app, host='0.0.0.0', port=5000, workers=4):
    """Run the Flask application using Gunicorn WSGI server (production)."""
    try:
        from gunicorn.app.wsgiapp import WSGIApplication
        
        class StandaloneApplication(WSGIApplication):
            def init(self, parser, opts, args):
                self.cfg.set('bind', f'{host}:{port}')
                self.cfg.set('workers', workers)
                self.cfg.set('threads', 2)
                self.cfg.set('timeout', 120)
                self.cfg.set('access-logfile', '-')
                self.cfg.set('error-logfile', '-')
                self.cfg.set('log-level', 'info')
                self.cfg.set('preload_app', True)
                
            def load(self):
                return app
        
        logger.info("=" * 60)
        logger.info("Starting Browser Agent Flask API Server (Gunicorn)")
        logger.info("=" * 60)
        logger.info(f"Host: {host}")
        logger.info(f"Port: {port}")
        logger.info(f"Workers: {workers}")
        logger.info("=" * 60)
        
        StandaloneApplication().run()
    except ImportError:
        logger.warning("Gunicorn not installed. Install with: pip install gunicorn")
        logger.info("Falling back to Flask development server...")
        run_production_server(app, host=host, port=port, debug=False)
    except Exception as e:
        logger.error(f"Error running Gunicorn server: {e}", exc_info=True)
        raise

def main():
    """Main entry point for the production server."""
    try:
        # Setup environment
        setup_environment()
        
        # Check required environment variables
        if not check_required_env_vars():
            sys.exit(1)
        
        # Create Flask app
        app = create_app()
        
        # Setup signal handlers
        setup_signal_handlers(app)
        
        # Get configuration from environment
        host = os.getenv('HOST', '0.0.0.0')
        port = int(os.getenv('PORT', 5000))
        debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        server_type = os.getenv('SERVER_TYPE', 'flask').lower()  # flask, waitress, gunicorn
        
        # Run the appropriate server
        if server_type == 'waitress':
            threads = int(os.getenv('WAITRESS_THREADS', '4'))
            run_with_waitress(app, host=host, port=port, threads=threads)
        elif server_type == 'gunicorn':
            workers = int(os.getenv('GUNICORN_WORKERS', '4'))
            run_with_gunicorn(app, host=host, port=port, workers=workers)
        else:
            # Default: Flask development server (not recommended for production)
            logger.warning("Using Flask development server. For production, use SERVER_TYPE=waitress or SERVER_TYPE=gunicorn")
            run_production_server(app, host=host, port=port, debug=debug)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()

