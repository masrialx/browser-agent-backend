# Website Domain Detection Fix

## Issue

The browser agent was searching Google or other search engines when the user explicitly mentioned a website domain (e.g., "wikipedia", "find about X on wikipedia"). The agent should **navigate directly to the website** when a domain is mentioned, not search for it.

## Root Cause

The `REASON_AND_DECIDE()` method was not properly detecting website domains in user queries. It was treating queries like "find about X on wikipedia" as search queries instead of recognizing "wikipedia" as a target website.

## Solution

### 1. Enhanced LLM System Instruction

**Updated the system instruction to:**
- Explicitly detect website domains (wikipedia, reddit, github, etc.)
- Understand that mentioning a website means "navigate to that website"
- Only use search engines when NO specific website is mentioned
- Handle queries like "on wikipedia", "from wikipedia", "wikipedia page", etc.

**Key Rules Added:**
- If website/domain mentioned: ALWAYS use OPEN_URL
- If query says "on wikipedia", "from wikipedia", etc., use OPEN_URL
- DO NOT search Google when a specific website is mentioned
- Only use SEARCH_GOOGLE when NO specific website is mentioned

### 2. Enhanced Fallback Logic

**Added website domain detection in fallback logic:**
- Common website domains dictionary (wikipedia, reddit, github, stackoverflow, etc.)
- Detection of navigation keywords: "on ", "from ", "visit", "open", "go to", "navigate to", "check", "read", "find on", "search on"
- Automatic URL construction from domain names

**Supported Websites:**
- wikipedia → https://www.wikipedia.org
- reddit → https://www.reddit.com
- github → https://www.github.com
- stackoverflow → https://www.stackoverflow.com
- youtube, twitter, facebook, linkedin, instagram
- medium, dev.to
- techcrunch, bbc, cnn, reuters, theverge, arstechnica

### 3. Query Examples

**Before (Incorrect Behavior):**
- Query: "find about Ethiopian and sumz on wikipedia"
- Action: SEARCH_GOOGLE("find about Ethiopian and sumz on wikipedia")
- Result: Searches Google instead of navigating to Wikipedia

**After (Correct Behavior):**
- Query: "find about Ethiopian and sumz on wikipedia"
- Action: OPEN_URL("https://www.wikipedia.org")
- Result: Navigates directly to Wikipedia

**Other Examples:**
- "visit wikipedia" → OPEN_URL("https://www.wikipedia.org")
- "open reddit" → OPEN_URL("https://www.reddit.com")
- "go to github" → OPEN_URL("https://www.github.com")
- "check stackoverflow" → OPEN_URL("https://www.stackoverflow.com")
- "read on medium" → OPEN_URL("https://www.medium.com")
- "find X on wikipedia" → OPEN_URL("https://www.wikipedia.org")
- "search for X on reddit" → OPEN_URL("https://www.reddit.com")

## Implementation Details

### LLM System Instruction

```python
system_instruction = """...
CRITICAL RULES:
- If the query mentions a website domain (wikipedia, reddit, github, etc.), ALWAYS use OPEN_URL
- If the query says "on wikipedia", "from wikipedia", "wikipedia page", etc., use OPEN_URL
- DO NOT search Google when a specific website is mentioned - navigate directly to that website
- Only use SEARCH_GOOGLE when NO specific website is mentioned
..."""
```

### Fallback Domain Detection

```python
website_domains = {
    'wikipedia': 'https://www.wikipedia.org',
    'reddit': 'https://www.reddit.com',
    'github': 'https://www.github.com',
    # ... more websites
}

# Check if query mentions a website domain
for domain, url in website_domains.items():
    if domain in query_lower:
        nav_keywords = ['on ', 'from ', 'visit', 'open', 'go to', ...]
        if any(keyword + domain in query_lower for keyword in nav_keywords):
            return ActionPlan(action="OPEN_URL", target=url, ...)
```

## Testing

### Test Cases

1. **"find about Ethiopian and sumz on wikipedia"**
   - Expected: OPEN_URL("https://www.wikipedia.org")
   - Actual: ✅ Navigates to Wikipedia

2. **"visit reddit"**
   - Expected: OPEN_URL("https://www.reddit.com")
   - Actual: ✅ Navigates to Reddit

3. **"open github"**
   - Expected: OPEN_URL("https://www.github.com")
   - Actual: ✅ Navigates to GitHub

4. **"find latest news"** (no website mentioned)
   - Expected: SEARCH_GOOGLE("latest news")
   - Actual: ✅ Searches Google

5. **"search for python tutorials"** (no website mentioned)
   - Expected: SEARCH_GOOGLE("python tutorials")
   - Actual: ✅ Searches Google

## Benefits

1. **Direct Navigation**: Users can navigate directly to websites by mentioning them
2. **No Unnecessary Searches**: Avoids searching Google when a website is specified
3. **Better User Experience**: Faster access to specific websites
4. **Intelligent Detection**: LLM + fallback logic ensures reliable detection
5. **Extensible**: Easy to add more website domains

## Summary

The browser agent now:
- ✅ Detects website domains in user queries
- ✅ Navigates directly to websites when mentioned
- ✅ Only uses search engines when no website is specified
- ✅ Handles various query patterns ("on wikipedia", "visit reddit", etc.)
- ✅ Provides fallback detection for common websites
- ✅ Avoids unnecessary searches and CAPTCHAs

This ensures the agent follows user intent correctly and navigates directly to websites when specified, rather than searching for them.

