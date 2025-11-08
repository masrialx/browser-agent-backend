# Entry Points Comparison

## Overview

The backend now has multiple entry points for running the Flask application. This document compares them and provides usage guidelines.

## Entry Points

### 1. `backend/run.py` (NEW - Recommended)

**Location:** `/home/masri/Desktop/Hackthon/backend/run.py`

**Features:**
- ✅ Command-line argument parsing (`--host`, `--port`, `--debug`, `--reload`)
- ✅ Enhanced logging (console + file)
- ✅ Environment variable validation
- ✅ Configuration validation
- ✅ Error handling
- ✅ Can be run from backend root directory
- ✅ Detailed startup information

**Usage:**
```bash
# Basic usage
python run.py

# Custom port
python run.py --port 8080

# Custom host and port
python run.py --host 127.0.0.1 --port 8080

# Debug mode
python run.py --debug

# Auto-reload on code changes
python run.py --reload

# Combined options
python run.py --host 0.0.0.0 --port 5000 --debug --reload
```

**Code Structure:**
```python
# Imports Flask app factory
from flask_app.app import create_app

# Features:
# - argparse for command-line arguments
# - Enhanced logging setup
# - Environment variable loading
# - Configuration validation
# - Error handling
```

---

### 2. `backend/app.py` (NEW - Convenience)

**Location:** `/home/masri/Desktop/Hackthon/backend/app.py`

**Features:**
- ✅ Alias to `run.py`
- ✅ Same functionality as `run.py`
- ✅ Convenience entry point
- ✅ Can be run from backend root directory

**Usage:**
```bash
# Same as run.py
python app.py
python app.py --port 8080
python app.py --debug
```

**Code Structure:**
```python
# Simply imports and runs main from run.py
from run import main
```

---

### 3. `backend/flask_app/run.py` (EXISTING)

**Location:** `/home/masri/Desktop/Hackthon/backend/flask_app/run.py`

**Features:**
- ✅ Simple Flask app runner
- ✅ Environment variable loading
- ✅ Basic configuration
- ✅ Can be run from flask_app directory

**Usage:**
```bash
# From flask_app directory
cd flask_app
python run.py
```

**Code Structure:**
```python
# Imports Flask app factory
from flask_app.app import create_app

# Features:
# - Simple configuration
# - Environment variable loading
# - Basic logging
```

---

## File Mapping

### Import Flow

```
backend/run.py
    ↓
from flask_app.app import create_app
    ↓
backend/flask_app/app/__init__.py
    ↓
Creates Flask app
    ↓
Registers blueprints
    ↓
backend/flask_app/app/views/browser_agent.py
    ↓
API endpoints
```

### Path Resolution

```
backend/run.py
    ├── Adds backend_dir to sys.path
    ├── Imports: from flask_app.app import create_app
    └── Runs: app.run()

backend/flask_app/run.py
    ├── Adds backend_dir to sys.path
    ├── Imports: from flask_app.app import create_app
    └── Runs: app.run()
```

---

## Comparison Table

| Feature | backend/run.py | backend/app.py | flask_app/run.py |
|---------|---------------|----------------|------------------|
| **Location** | backend/ | backend/ | flask_app/ |
| **Command-line args** | ✅ Yes | ✅ Yes (via run.py) | ❌ No |
| **Enhanced logging** | ✅ Yes | ✅ Yes | ⚠️ Basic |
| **Error handling** | ✅ Yes | ✅ Yes | ⚠️ Basic |
| **Config validation** | ✅ Yes | ✅ Yes | ❌ No |
| **Auto-reload** | ✅ Yes | ✅ Yes | ❌ No |
| **Run from root** | ✅ Yes | ✅ Yes | ❌ No (needs cd) |
| **Recommended** | ✅ **YES** | ✅ Alternative | ⚠️ Legacy |

---

## Recommended Usage

### For Development
```bash
# Use backend/run.py with auto-reload
cd /home/masri/Desktop/Hackthon/backend
python run.py --debug --reload
```

### For Production
```bash
# Use backend/run.py with custom host/port
cd /home/masri/Desktop/Hackthon/backend
python run.py --host 0.0.0.0 --port 5000
```

### For Quick Testing
```bash
# Use backend/app.py (simpler command)
cd /home/masri/Desktop/Hackthon/backend
python app.py
```

---

## Environment Variables

All entry points support environment variables via `.env` file:

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

**Location:** Create `.env` file in `backend/` directory

---

## API Endpoints

All entry points expose the same API endpoints:

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

---

## Summary

- ✅ **`backend/run.py`** - **Recommended** main entry point with enhanced features
- ✅ **`backend/app.py`** - Convenience alias to `run.py`
- ⚠️ **`flask_app/run.py`** - Legacy entry point (still works)

**Best Practice:** Use `backend/run.py` for all new deployments and development.

