# LLM-Based Reasoning Implementation

## Overview

The browser agent now uses **LLM-based reasoning** with **structured schema validation** instead of hardcoded keyword matching. This provides more intelligent and flexible decision-making.

## Changes Made

### 1. REASON_AND_DECIDE() - LLM-Based Action Planning

**Before (Hardcoded):**
```python
# Hardcoded keyword matching
search_keywords = ['search', 'find', 'look for', 'what is', 'how to', 'where is']
if any(keyword in query_lower for keyword in search_keywords):
    # Extract search terms by removing keywords
    search_terms = query
    for keyword in search_keywords:
        search_terms = re.sub(keyword, '', search_terms, flags=re.IGNORECASE).strip()
```

**After (LLM-Based):**
```python
# LLM with structured schema validation
class ActionPlanSchema(BaseModel):
    action: str  # OPEN_URL, SEARCH_GOOGLE, READ_PAGE, FIX_ISSUE
    target: str  # URL or search query
    reason: str
    expected_outcome: str

response = self.llm_service.generate_content_with_Structured_schema(
    system_instruction=system_instruction,
    query=reasoning_prompt,
    response_schema=ActionPlanSchema
)

# Validation
- Validates action is one of allowed values
- Ensures target is not empty
- Provides fallback if LLM fails
```

### 2. REASON_AND_CHOOSE_FALLBACK() - LLM-Based Fallback Selection

**Before (Hardcoded):**
```python
# Hardcoded site selection based on keywords
if any(word in query_lower for word in ['news', 'latest', 'recent', 'update']):
    news_sites = ['bbc.com', 'techcrunch.com', ...]
    for site in news_sites:
        fallbacks.append({...})
```

**After (LLM-Based):**
```python
# LLM suggests relevant fallback strategies
class FallbackStrategySchema(BaseModel):
    type: str  # search_engine, site_search, cache
    engine: str = ""
    site: str = ""
    query: str = ""
    description: str

class FallbackListSchema(BaseModel):
    fallbacks: List[FallbackStrategySchema]

response = self.llm_service.generate_content_with_Structured_schema(
    system_instruction=system_instruction,
    query=reasoning_prompt,
    response_schema=FallbackListSchema
)

# Validation
- Validates fallback types
- Validates engines (bing, duckduckgo)
- Ensures required fields are present
- Provides intelligent site suggestions
```

## Benefits

### 1. Intelligent Query Understanding

**LLM Advantages:**
- ✅ Understands context and intent beyond keywords
- ✅ Handles variations in phrasing
- ✅ Extracts search terms intelligently
- ✅ Removes filler words while preserving meaning
- ✅ Understands nuanced queries

**Example:**
- Query: "What's the latest on OpenAI?"
- Hardcoded: Might miss "What's" and "latest"
- LLM: Correctly identifies search intent, extracts "OpenAI latest news"

### 2. Smart Fallback Selection

**LLM Advantages:**
- ✅ Suggests relevant sites based on query topic
- ✅ Not limited to hardcoded keyword matching
- ✅ Adapts to different query types
- ✅ Suggests authoritative sources intelligently

**Example:**
- Query: "Latest AI developments"
- Hardcoded: Only checks for "news", "latest" keywords
- LLM: Suggests tech news sites, AI-specific blogs, research sites

### 3. Validation and Safety

**Validation Features:**
- ✅ Validates action types (OPEN_URL, SEARCH_GOOGLE, etc.)
- ✅ Ensures target is not empty
- ✅ Validates fallback types
- ✅ Validates search engines
- ✅ Provides fallback logic if LLM fails

### 4. Structured Output

**Structured Schema:**
- ✅ Uses Pydantic BaseModel for type safety
- ✅ Gemini 2.0 Flash structured output
- ✅ Automatic JSON parsing and validation
- ✅ Consistent response format

## Implementation Details

### Action Planning

```python
system_instruction = """You are an AI assistant that analyzes user queries...

Rules:
- If URL is present: action = "OPEN_URL", target = the URL
- If search intent: action = "SEARCH_GOOGLE", target = cleaned search terms
- Remove command words like "search", "find", "look for"
- Be smart about extracting search terms
"""

# Validation
allowed_actions = ["OPEN_URL", "SEARCH_GOOGLE", "READ_PAGE", "FIX_ISSUE"]
if response.action not in allowed_actions:
    response.action = "SEARCH_GOOGLE"  # Default

if not response.target or not response.target.strip():
    response.target = query  # Fallback to original
```

### Fallback Selection

```python
system_instruction = """Suggest fallback search strategies...

Always prioritize:
1. Alternative search engines (Bing, DuckDuckGo) first
2. Then site-specific searches on relevant authoritative sources
3. Finally cached version searches
"""

# Validation
if fb_type not in ["search_engine", "site_search", "cache"]:
    continue  # Skip invalid

if fb_type == "search_engine":
    if engine not in ["bing", "duckduckgo"]:
        engine = "bing"  # Default
```

## Fallback Logic

Both methods have **fallback logic** if LLM fails:

1. **REASON_AND_DECIDE**: Falls back to regex-based URL detection and default search
2. **REASON_AND_CHOOSE_FALLBACK**: Falls back to hardcoded fallback strategies

This ensures the system continues to work even if:
- LLM service is unavailable
- LLM returns invalid response
- Network issues
- API errors

## Examples

### Example 1: Search Query

**Input:**
```json
{"query": "Find latest news about OpenAI", "agent_id": "test_001"}
```

**LLM Analysis:**
- Action: `SEARCH_GOOGLE`
- Target: `latest news OpenAI` (removed "Find")
- Reason: "Search intent detected for latest news about OpenAI"
- Expected Outcome: "Find recent news articles about OpenAI"

### Example 2: URL Query

**Input:**
```json
{"query": "Open https://github.com", "agent_id": "test_002"}
```

**LLM Analysis:**
- Action: `OPEN_URL`
- Target: `https://github.com`
- Reason: "URL detected in query"
- Expected Outcome: "Navigate to GitHub website"

### Example 3: Fallback Selection

**Input Query:** "Latest AI developments"

**LLM Fallback Suggestions:**
1. Search Bing for "Latest AI developments"
2. Search DuckDuckGo for "Latest AI developments"
3. Search techcrunch.com for "Latest AI developments"
4. Search bbc.com for "Latest AI developments"
5. Search medium.com for "Latest AI developments"
6. Get cached version of results

## Testing

The LLM-based reasoning is tested through:

1. **Structured Schema Validation**: Ensures responses match expected format
2. **Action Validation**: Validates action is one of allowed values
3. **Target Validation**: Ensures target is not empty
4. **Fallback Logic**: Tests fallback when LLM fails
5. **Error Handling**: Tests error cases and recovery

## Summary

The browser agent now uses **LLM-based reasoning** with:

- ✅ **Intelligent query analysis** using Gemini 2.0 Flash
- ✅ **Structured schema validation** for reliable parsing
- ✅ **Smart fallback selection** based on query context
- ✅ **Validation and safety** checks
- ✅ **Fallback logic** if LLM fails
- ✅ **No hardcoded keyword matching** - all intelligent reasoning

This provides a more flexible, intelligent, and maintainable system that adapts to different query types and contexts.

