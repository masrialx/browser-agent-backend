#!/bin/bash
# Production startup script for Browser Agent API

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Browser Agent API...${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found. Using system environment variables.${NC}"
fi

# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${RED}Error: GEMINI_API_KEY environment variable is not set${NC}"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo -e "${GREEN}Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Install Playwright browsers if not already installed
if ! command -v playwright &> /dev/null; then
    echo -e "${YELLOW}Playwright not found. Installing...${NC}"
    pip install playwright
    playwright install chromium
fi

# Set default environment variables
export FLASK_ENV=${FLASK_ENV:-production}
export SERVER_TYPE=${SERVER_TYPE:-waitress}
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-5000}

# Run the application
echo -e "${GREEN}Starting server on ${HOST}:${PORT}...${NC}"
python run.py

