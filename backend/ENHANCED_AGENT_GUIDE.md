# Enhanced Browser Agent Guide

## Overview

The Enhanced Browser Agent is an advanced AI-powered browser automation system that uses reasoning to execute tasks intelligently. It supports:

- **Automatic website detection** from queries
- **Intelligent action selection** (OPEN_URL, SEARCH_GOOGLE, READ_PAGE, FIX_ISSUE)
- **Page analysis and issue detection**
- **Structured JSON output** with detailed step tracking
- **Gemini 2.0 Flash** for reasoning and decision-making

## API Endpoint

### Execute Browser Task

**Endpoint:** `POST /api/v1/browser-agent/execute`

#### Request Format

```json
{
    "query": "<user query>",
    "agent_id": "<agent_id>"  // Optional
}
```

#### Response Format (Strict JSON)

```json
{
    "success": true,
    "data": {
        "agent_id": "<agent_id>",
        "overall_success": true,
        "query": "<original query>",
        "steps": [
            {
                "step": "<description of action taken>",
                "result": {
                    "data": {
                        "title": "<page title or resource title>",
                        "url": "<accessed url>"
                    },
                    "error": null,
                    "message": "<short execution message>",
                    "success": true
                },
                "success": true
            }
        ]
    }
}
```

## Internal Commands

The agent uses these internal commands:

### 1. REASON_AND_DECIDE(query)
- Analyzes the user query using Gemini 2.0 Flash
- Determines the best action (OPEN_URL, SEARCH_GOOGLE, READ_PAGE, FIX_ISSUE)
- Returns an ActionPlan with target and reasoning

### 2. OPEN_URL(url)
- Opens a specified URL in the browser
- Waits for page to load
- Returns page title and URL

### 3. SEARCH_GOOGLE(query)
- Performs a Google search
- Extracts search results
- Returns search results page information

### 4. READ_PAGE(url?)
- Reads and analyzes the current or specified page
- Extracts content, headings, meta description
- Detects potential errors or issues
- Returns comprehensive page analysis

### 5. FIX_ISSUE(issue_description)
- Analyzes an issue using LLM
- Provides solutions or fix suggestions
- Returns fix recommendations

### 6. RECORD_STEP(description, result)
- Records each step in the execution log
- Maintains step-by-step history
- Returns formatted step record

## Usage Examples

### Example 1: Open a URL

**Request:**
```json
{
    "query": "Open https://www.github.com",
    "agent_id": "agent_001"
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "agent_id": "agent_001",
        "overall_success": true,
        "query": "Open https://www.github.com",
        "steps": [
            {
                "step": "Reasoned about query: Open https://www.github.com",
                "success": true,
                "result": {
                    "success": true,
                    "message": "Decided to OPEN_URL: https://www.github.com",
                    "data": {
                        "title": "GitHub",
                        "url": "https://github.com"
                    },
                    "error": null
                }
            },
            {
                "step": "Opened URL: https://www.github.com",
                "success": true,
                "result": {
                    "success": true,
                    "message": "Successfully opened https://www.github.com",
                    "data": {
                        "title": "GitHub: Where the world builds software",
                        "url": "https://github.com"
                    },
                    "error": null
                }
            },
            {
                "step": "Read page content from https://www.github.com",
                "success": true,
                "result": {
                    "success": true,
                    "message": "Successfully read page: GitHub: Where the world builds software",
                    "data": {
                        "title": "GitHub: Where the world builds software",
                        "url": "https://github.com",
                        "content_preview": "...",
                        "meta_description": "...",
                        "headings": {...},
                        "issues": []
                    },
                    "error": null
                }
            }
        ]
    }
}
```

### Example 2: Search Google

**Request:**
```json
{
    "query": "Search for Python tutorials",
    "agent_id": "agent_002"
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "agent_id": "agent_002",
        "overall_success": true,
        "query": "Search for Python tutorials",
        "steps": [
            {
                "step": "Reasoned about query: Search for Python tutorials",
                "success": true,
                "result": {
                    "success": true,
                    "message": "Decided to SEARCH_GOOGLE: Python tutorials",
                    "data": {
                        "title": "Python tutorials - Google Search",
                        "url": "https://www.google.com/search?q=Python+tutorials"
                    },
                    "error": null
                }
            },
            {
                "step": "Searched Google for: Python tutorials",
                "success": true,
                "result": {
                    "success": true,
                    "message": "Successfully searched for: Python tutorials",
                    "data": {
                        "title": "Python tutorials - Google Search",
                        "url": "https://www.google.com/search?q=Python+tutorials",
                        "query": "Python tutorials",
                        "results": [
                            {"title": "...", "url": "..."},
                            ...
                        ]
                    },
                    "error": null
                }
            },
            {
                "step": "Read search results page",
                "success": true,
                "result": {
                    "success": true,
                    "message": "Successfully read page: Python tutorials - Google Search",
                    "data": {
                        "title": "Python tutorials - Google Search",
                        "url": "https://www.google.com/search?q=Python+tutorials",
                        "content_preview": "...",
                        "issues": []
                    },
                    "error": null
                }
            }
        ]
    }
}
```

### Example 3: Query without URL (Auto-detect)

**Request:**
```json
{
    "query": "Find information about artificial intelligence"
}
```

The agent will:
1. Reason that no URL is provided
2. Decide to search Google
3. Execute the search
4. Return results

## How It Works

1. **Query Analysis**: The agent receives a query and uses Gemini 2.0 Flash to analyze it
2. **Action Planning**: Based on the analysis, it decides on the best action:
   - If URL is detected → OPEN_URL
   - If search intent is detected → SEARCH_GOOGLE
   - If analysis is needed → READ_PAGE
   - If issue is mentioned → FIX_ISSUE
3. **Execution**: The agent executes the planned action using Playwright
4. **Page Analysis**: After opening/searching, it reads and analyzes the page
5. **Step Recording**: Each step is recorded with detailed information
6. **Response**: Returns structured JSON with all steps and results

## Features

### Intelligent Reasoning
- Automatically detects URLs in queries
- Identifies search intent
- Chooses appropriate actions
- Provides reasoning for decisions

### Comprehensive Page Analysis
- Extracts page title and URL
- Reads page content
- Extracts headings (H1, H2)
- Gets meta descriptions
- Detects potential errors

### Error Handling
- Graceful error handling at each step
- Detailed error messages
- Continues execution even if one step fails
- Records all errors in response

### Step Tracking
- Every action is recorded
- Detailed step descriptions
- Success/failure status for each step
- Overall success calculation

## Testing

Run the test script:

```bash
python test_enhanced_agent.py
```

Or test manually with curl:

```bash
curl -X POST http://localhost:5000/api/v1/browser-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Search for AI",
    "agent_id": "test_001"
  }'
```

## Requirements

- Gemini API Key (set in GEMINI_API_KEY environment variable)
- Playwright browsers installed: `playwright install chromium`
- All dependencies from requirements.txt

## Next Steps

- Add support for more actions (click, fill form, etc.)
- Implement issue fixing automation
- Add screenshot capture
- Implement retry logic for failed steps
- Add database persistence for execution history

