#!/usr/bin/env python3
"""
Alternative entry point for the Browser Automation Backend Application.

This is an alias to run.py for convenience. You can use either:
    python run.py
    python app.py

Both will start the Flask application.
"""

import sys
import os

# Add current directory to Python path
backend_dir = os.path.abspath(os.path.dirname(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import and run main from run.py
from run import main

if __name__ == "__main__":
    main()

