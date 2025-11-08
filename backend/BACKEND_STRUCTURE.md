# Backend Structure and Entry Points

## Directory Structure

```
backend/
├── run.py                    # Main entry point (NEW - can run from backend/)
├── app.py                    # Alternative entry point (alias to run.py)
├── requirements.txt          # Main requirements file
├── .env                      # Environment variables (create this)
│
├── flask_app/                # Flask application package
│   ├── run.py               # Flask app entry point (original)
│   ├── app/
│   │   ├── __init__.py      # Flask app factory
│   │   ├── views/
│   │   │   └── browser_agent.py  # API endpoints
│   │   └── ...
│   ├── config.py            # Configuration
│   └── requirements.txt     # Flask app requirements
│
├── src/                      # Source code
│   └── usecases/
│       └── browser_usecase.py
│
├── infrastructure/           # Infrastructure layer
│   ├── browser_automation_latest/
│   │   └── browser_agent.py
│   ├── llm/
│   │   └── open_ai_llm.py
│   └── repositories/
│
└── domain/                   # Domain models
    └── models/
```

## Entry Points

### 1. Main Entry Point: `backend/run.py`

**Location:** `/home/masri/Desktop/Hackthon/backend/run.py`

**Usage:**
```bash
# From backend directory
cd /home/masri/Desktop/Hackthon/backend
python run.py

# With custom port
python run.py --port 8080

# With custom host and port
python run.py --host 127.0.0.1 --port 8080

# With debug mode
python run.py --debug

# With auto-reload
python run.py --reload
```

**Features:**
- ✅ Command-line argument parsing
- ✅ Environment variable loading
- ✅ Configuration validation
- ✅ Logging setup
- ✅ Error handling
- ✅ Can be run from backend root directory

### 2. Alternative Entry Point: `backend/app.py`

**Location:** `/home/masri/Desktop/Hackthon/backend/app.py`

**Usage:**
```bash
# From backend directory
python app.py
```

**Features:**
- ✅ Alias to `run.py`
- ✅ Convenience entry point
- ✅ Same functionality as `run.py`

### 3. Flask App Entry Point: `backend/flask_app/run.py`

**Location:** `/home/masri/Desktop/Hackthon/backend/flask_app/run.py`

**Usage:**
```bash
# From flask_app directory
cd /home/masri/Desktop/Hackthon/backend/flask_app
python run.py
```

**Features:**
- ✅ Original Flask app entry point
- ✅ Simple configuration
- ✅ Environment variable loading

## File Mapping

### `backend/run.py` (NEW)
- **Purpose:** Main entry point from backend root
- **Imports:** `from flask_app.app import create_app`
- **Features:** 
  - Command-line arguments
  - Enhanced logging
  - Configuration validation
  - Error handling

### `backend/flask_app/run.py` (EXISTING)
- **Purpose:** Flask app entry point from flask_app directory
- **Imports:** `from flask_app.app import create_app`
- **Features:**
  - Simple Flask app runner
  - Environment variable loading
  - Basic configuration

### `backend/flask_app/app/__init__.py`
- **Purpose:** Flask app factory
- **Creates:** Flask application instance
- **Registers:** Blueprints (browser_agent_bp)
- **Configures:** CORS, logging

### `backend/flask_app/app/views/browser_agent.py`
- **Purpose:** API endpoints
- **Endpoints:**
  - `POST /api/v1/browser-agent/execute` - Execute browser task
  - `GET /api/v1/browser-agent/health` - Health check

## Running the Application

### Option 1: From Backend Root (Recommended)

```bash
cd /home/masri/Desktop/Hackthon/backend
python run.py
```

### Option 2: From Flask App Directory

```bash
cd /home/masri/Desktop/Hackthon/backend/flask_app
python run.py
```

### Option 3: Using app.py

```bash
cd /home/masri/Desktop/Hackthon/backend
python app.py
```

## Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=5000
DEBUG=False

# Optional: Secret Key
SECRET_KEY=your-secret-key-here
```

## API Endpoints

### Execute Browser Task
```bash
POST http://localhost:5000/api/v1/browser-agent/execute
Content-Type: application/json

{
  "query": "visit wikipedia and find about ethiopia and sumz",
  "agent_id": "agent_123"
}
```

### Health Check
```bash
GET http://localhost:5000/api/v1/browser-agent/health
```

## Dependencies

Main requirements are in:
- `backend/requirements.txt` - Main requirements
- `backend/flask_app/requirements.txt` - Flask app requirements

Install dependencies:
```bash
pip install -r requirements.txt
pip install -r flask_app/requirements.txt
```

## Logging

Logs are written to:
- Console (stdout)
- `backend/app.log` (file)

## Summary

- ✅ **`backend/run.py`** - Main entry point (NEW, recommended)
- ✅ **`backend/app.py`** - Alternative entry point (NEW, convenience)
- ✅ **`backend/flask_app/run.py`** - Original Flask app entry point (EXISTING)

All three entry points work and can be used interchangeably. The new `backend/run.py` provides enhanced features like command-line arguments and better error handling.

