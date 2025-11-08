# Browser Agent API

This document describes how to use the Browser Agent API endpoint that executes browser automation tasks using Gemini 2.0 Flash.

## Setup

### 1. Install Dependencies

Make sure you have all required packages installed:

```bash
pip install -r requirements.txt
```

### 2. Install Playwright Browsers

The browser agent uses Playwright for automation. Install the browsers:

```bash
playwright install chromium
```

### 3. Configure Environment Variables

Create a `.env` file in the `backend` directory:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=your-secret-key-here
DEBUG=True
HOST=0.0.0.0
PORT=5000
```

Get your Gemini API key from: https://makersuite.google.com/app/apikey

## Running the Server

### Option 1: Using run.py

```bash
cd backend/flask_app
python run.py
```

### Option 2: Using Flask CLI

```bash
cd backend/flask_app
export FLASK_APP=run.py
flask run
```

The server will start on `http://localhost:5000` by default.

## API Endpoints

### 1. Execute Browser Task

**Endpoint:** `POST /api/v1/browser-agent/execute`

**Description:** Executes a browser automation task based on the provided query.

**Request Body:**
```json
{
    "query": "Search for AI on Google",
    "agent_id": "agent_123",  // Optional
    "user_id": "user_456"      // Optional
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "query": "Search for AI on Google",
        "steps": [
            {
                "step": "Open Google",
                "success": true,
                "result": {
                    "success": true,
                    "message": "Successfully navigated to Google",
                    "data": {
                        "url": "https://www.google.com",
                        "title": "Google"
                    }
                }
            }
        ],
        "overall_success": true,
        "agent_id": "agent_123"
    }
}
```

**Example using curl:**
```bash
curl -X POST http://localhost:5000/api/v1/browser-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Search for AI on Google",
    "agent_id": "agent_123"
  }'
```

**Example using Python:**
```python
import requests

url = "http://localhost:5000/api/v1/browser-agent/execute"
payload = {
    "query": "Search for AI on Google",
    "agent_id": "agent_123"
}
response = requests.post(url, json=payload)
print(response.json())
```

### 2. Health Check

**Endpoint:** `GET /api/v1/browser-agent/health`

**Description:** Checks if the browser agent service is running and properly configured.

**Response:**
```json
{
    "status": "healthy",
    "message": "Browser agent service is running"
}
```

## How It Works

1. **Query Processing**: The API receives a natural language query describing the browser task.
2. **Step Generation**: The query is broken down into actionable steps using Gemini 2.0 Flash.
3. **Browser Execution**: Each step is executed using Playwright browser automation.
4. **Result Aggregation**: Results from all steps are aggregated and returned.

## Configuration

### Gemini Model

The service uses Gemini 2.0 Flash by default. You can modify the model in `infrastructure/llm/open_ai_llm.py`:

```python
# Try Gemini 2.0 Flash Experimental
self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

# Or use Gemini 2.0 Flash Latest
self.model = genai.GenerativeModel('gemini-2.0-flash-latest')

# Fallback to Gemini 1.5 Flash
self.model = genai.GenerativeModel('gemini-1.5-flash')
```

### Browser Settings

Browser settings can be modified in `infrastructure/browser_automation_latest/browser_agent.py`:

- `headless=False`: Set to `True` to run browser in headless mode
- `viewport`: Adjust browser viewport size
- `user_agent`: Customize user agent string

## Error Handling

The API returns appropriate error messages:

- **400 Bad Request**: Missing or invalid request parameters
- **500 Internal Server Error**: Server-side errors (e.g., missing API key, browser errors)

## Troubleshooting

### Issue: "GEMINI_API_KEY environment variable is not set"

**Solution:** Make sure you have set the `GEMINI_API_KEY` in your `.env` file or environment variables.

### Issue: Browser fails to launch

**Solution:** Make sure Playwright browsers are installed:
```bash
playwright install chromium
```

### Issue: Import errors

**Solution:** Make sure you're running from the correct directory and Python path is set correctly. The Flask app adds the backend directory to the Python path automatically.

## Next Steps

- Extend `BrowserAgent` to handle more complex browser tasks
- Add authentication and authorization
- Implement database persistence for workstreams
- Add task queue for asynchronous execution
- Implement retry logic for failed steps

