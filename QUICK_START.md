# Quick Start Guide - Browser Agent API

## Setup (One-time)

1. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Install Playwright browsers:**
   ```bash
   playwright install chromium
   ```

3. **Set up environment variables:**
   Create a `.env` file in the `backend` directory:
   ```bash
   GEMINI_API_KEY=your_gemini_api_key_here
   SECRET_KEY=dev-secret-key
   DEBUG=True
   PORT=5000
   ```

## Run the Server

```bash
cd backend/flask_app
python run.py
```

The server will start on `http://localhost:5000`

## API Endpoint

### Execute Browser Task

**URL:** `POST http://localhost:5000/api/v1/browser-agent/execute`

**Request:**
```json
{
    "query": "Search for AI on Google",
    "agent_id": "optional_agent_id",
    "user_id": "optional_user_id"
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "query": "Search for AI on Google",
        "steps": [...],
        "overall_success": true,
        "agent_id": "optional_agent_id"
    }
}
```

## Example Usage

### Using curl:
```bash
curl -X POST http://localhost:5000/api/v1/browser-agent/execute \
  -H "Content-Type: application/json" \
  -d '{"query": "Search for AI on Google"}'
```

### Using Python:
```python
import requests

response = requests.post(
    "http://localhost:5000/api/v1/browser-agent/execute",
    json={"query": "Search for AI on Google"}
)
print(response.json())
```

### Using JavaScript (fetch):
```javascript
fetch('http://localhost:5000/api/v1/browser-agent/execute', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: 'Search for AI on Google'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

## Health Check

```bash
curl http://localhost:5000/api/v1/browser-agent/health
```

## Features

- ✅ Uses Gemini 2.0 Flash for intelligent task breakdown
- ✅ Playwright-based browser automation
- ✅ Automatic step generation from natural language queries
- ✅ Error handling and recovery
- ✅ Workstream tracking (when agent_id is provided)

