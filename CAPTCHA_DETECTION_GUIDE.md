# CAPTCHA Detection and Handling Guide

## Overview

The Enhanced Browser Agent includes comprehensive CAPTCHA detection and handling capabilities. The agent **never attempts to circumvent security measures** and immediately pauses automation when a CAPTCHA is detected.

## Features

### 1. Automatic CAPTCHA Detection

The agent detects CAPTCHAs through multiple methods:

- **Element Detection**: Searches for common CAPTCHA elements:
  - reCAPTCHA: `iframe[src*="recaptcha"]`, `.g-recaptcha`, `[data-sitekey]`
  - hCaptcha: `iframe[src*="hcaptcha"]`, `.h-captcha`
  - Cloudflare Turnstile: `iframe[src*="challenges.cloudflare.com"]`, `.cf-turnstile`
  - Generic CAPTCHA indicators: `div[class*="captcha"]`, `input[name*="captcha"]`

- **Content Analysis**: Checks page content for CAPTCHA-related keywords:
  - "recaptcha", "hcaptcha", "captcha"
  - "verify you are human"
  - "prove you are not a robot"
  - "I'm not a robot"
  - "security check", "human verification"
  - "cloudflare", "turnstile", "challenge"

- **Text Detection**: Searches for CAPTCHA-related text on the page

### 2. Detection Points

CAPTCHA detection occurs at multiple points:

1. **After opening a URL** (`OPEN_URL`)
2. **After navigating to Google** (`SEARCH_GOOGLE`)
3. **After search results load** (`SEARCH_GOOGLE`)
4. **Before reading page content** (`READ_PAGE`)
5. **Before fixing issues** (`FIX_ISSUE`)

### 3. Immediate Automation Pause

When a CAPTCHA is detected:

- ✅ Automation **immediately stops**
- ✅ No further automated actions are taken
- ✅ A detailed notification is generated for the user
- ✅ All steps are recorded in the JSON response
- ✅ The response includes `"error": "CAPTCHA_DETECTED"`

## Response Format

When a CAPTCHA is detected, the API returns the following JSON structure:

```json
{
    "success": false,
    "data": {
        "agent_id": "<agent_id>",
        "overall_success": false,
        "query": "<original query>",
        "steps": [
            {
                "step": "Detect CAPTCHA and pause",
                "result": {
                    "data": {
                        "title": "<page title if available>",
                        "url": "<url where CAPTCHA found>"
                    },
                    "error": "CAPTCHA_DETECTED",
                    "message": "A CAPTCHA was detected on the page at \"<url>\". Automated continuation is blocked by the verification.\n\nTo proceed:\n1. Open the following URL in your browser: <url>\n2. Complete the CAPTCHA manually\n3. Once the CAPTCHA is completed and you can access the page, reply with 'CAPTCHA_COMPLETED'\n4. The automation will then resume from the next step\n\nIMPORTANT SECURITY NOTES:\n- Do NOT share passwords, session tokens, API keys, or any private credentials\n- Do NOT provide screenshots that contain sensitive information\n- If a screenshot is helpful, only share the CAPTCHA challenge area (not login forms or sensitive data)\n- This is a security measure to protect websites from automated abuse",
                    "success": false
                },
                "success": false
            }
        ]
    }
}
```

## User Notification

The notification message includes:

1. **Clear explanation** that a CAPTCHA was detected
2. **The URL** where the CAPTCHA was found
3. **Step-by-step instructions** for the user:
   - Open the URL in their browser
   - Complete the CAPTCHA manually
   - Reply with `CAPTCHA_COMPLETED` when done
4. **Security warnings**:
   - Do NOT share passwords or credentials
   - Do NOT share screenshots with sensitive information
   - Only share CAPTCHA challenge area if needed

## Security Rules

The agent follows these strict security rules:

### ✅ What the Agent DOES:

- Detects CAPTCHAs automatically
- Pauses automation immediately
- Provides clear user instructions
- Records the detection in logs
- Returns structured error responses

### ❌ What the Agent NEVER DOES:

- **Never** attempts to solve CAPTCHAs programmatically
- **Never** provides instructions to bypass CAPTCHAs
- **Never** asks for credentials, session tokens, or API keys
- **Never** attempts to automate CAPTCHA completion
- **Never** retries automatically after CAPTCHA detection
- **Never** continues automation without user confirmation

## Workflow

### 1. Detection Phase

```
User Query → Agent Execution → Page Load → CAPTCHA Detection
```

### 2. Notification Phase

```
CAPTCHA Detected → Generate Notification → Record Step → Return Response
```

### 3. User Action Phase

```
User receives notification → Opens URL → Completes CAPTCHA → Confirms completion
```

### 4. Resumption Phase (Future)

```
User confirms CAPTCHA_COMPLETED → Validate confirmation → Resume automation
```

## Example Scenarios

### Scenario 1: CAPTCHA on Google Search

**Request:**
```json
{
    "query": "Search for Python tutorials",
    "agent_id": "agent_001"
}
```

**Response:**
```json
{
    "success": false,
    "data": {
        "agent_id": "agent_001",
        "overall_success": false,
        "query": "Search for Python tutorials",
        "steps": [
            {
                "step": "Reasoned about query: Search for Python tutorials",
                "success": true,
                "result": {...}
            },
            {
                "step": "Detect CAPTCHA and pause: Searched Google for: Python tutorials",
                "success": false,
                "result": {
                    "error": "CAPTCHA_DETECTED",
                    "message": "A CAPTCHA was detected on the page at \"https://www.google.com/search?q=Python+tutorials\"...",
                    "data": {
                        "title": "Google",
                        "url": "https://www.google.com/search?q=Python+tutorials"
                    }
                }
            }
        ]
    }
}
```

### Scenario 2: CAPTCHA on Target Website

**Request:**
```json
{
    "query": "Open https://example.com",
    "agent_id": "agent_002"
}
```

**Response:**
```json
{
    "success": false,
    "data": {
        "agent_id": "agent_002",
        "overall_success": false,
        "query": "Open https://example.com",
        "steps": [
            {
                "step": "Detect CAPTCHA and pause: Opened URL: https://example.com",
                "success": false,
                "result": {
                    "error": "CAPTCHA_DETECTED",
                    "message": "A CAPTCHA was detected on the page at \"https://example.com\"...",
                    "data": {
                        "title": "Example Domain",
                        "url": "https://example.com"
                    }
                }
            }
        ]
    }
}
```

## Implementation Details

### DETECT_CAPTCHA() Method

```python
async def DETECT_CAPTCHA(self) -> bool:
    """
    Detect if a CAPTCHA is present on the current page.
    Returns True if CAPTCHA is detected, False otherwise.
    """
    # Checks multiple indicators:
    # 1. CSS selectors for CAPTCHA elements
    # 2. Text content for CAPTCHA keywords
    # 3. Page content analysis
```

### NOTIFY_USER_FOR_CAPTCHA() Method

```python
def NOTIFY_USER_FOR_CAPTCHA(self, url: str, page_title: str = "") -> str:
    """
    Generate a user notification message for CAPTCHA detection.
    Returns a formatted message with instructions.
    """
```

### WAIT_FOR_USER_CONFIRMATION() Method

```python
async def WAIT_FOR_USER_CONFIRMATION(self) -> bool:
    """
    Wait for user confirmation that CAPTCHA is completed.
    Currently returns False to indicate pause.
    Future: Can be extended to poll for confirmation.
    """
```

## Testing CAPTCHA Detection

To test CAPTCHA detection, you can:

1. **Use a test endpoint** that returns a CAPTCHA
2. **Trigger rate limiting** on Google (may show CAPTCHA)
3. **Use Cloudflare-protected sites** (often show CAPTCHA)
4. **Test with reCAPTCHA demo pages**

## Future Enhancements

Potential future improvements:

1. **User Confirmation API**: Endpoint to receive `CAPTCHA_COMPLETED` confirmation
2. **Screenshot Capture**: Optional screenshot of CAPTCHA (without sensitive data)
3. **Retry Logic**: After user confirmation, retry the failed step
4. **CAPTCHA Type Detection**: Identify specific CAPTCHA type (reCAPTCHA, hCaptcha, etc.)
5. **Multiple CAPTCHA Handling**: Handle cases where multiple CAPTCHAs appear

## Compliance

This implementation ensures:

- ✅ **Security Compliance**: Never attempts to bypass security measures
- ✅ **Ethical Automation**: Respects website security policies
- ✅ **User Privacy**: Never requests sensitive credentials
- ✅ **Transparency**: Clear communication about CAPTCHA detection
- ✅ **Compliance**: Follows best practices for automated browsing

## Summary

The CAPTCHA detection system:

1. **Automatically detects** CAPTCHAs using multiple methods
2. **Immediately pauses** automation when detected
3. **Provides clear instructions** to users
4. **Never attempts** to solve or bypass CAPTCHAs
5. **Maintains security** and compliance standards
6. **Records all actions** in structured JSON format

This ensures that the browser agent operates ethically and respects website security measures while providing a smooth user experience when CAPTCHAs are encountered.

