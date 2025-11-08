import asyncio
import logging
import re
from typing import Optional, Dict, List
from pydantic import BaseModel
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

logger = logging.getLogger(__name__)

class TaskResult(BaseModel):
    """Result of a browser task execution."""
    success: bool
    message: str = ""
    data: dict = {}
    error: Optional[str] = None
    
    def dict(self):
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "error": self.error
        }

class ActionPlan(BaseModel):
    """Action plan from reasoning."""
    action: str  # OPEN_URL, SEARCH_GOOGLE, READ_PAGE, FIX_ISSUE
    target: str  # URL or search query
    reason: str
    expected_outcome: str

class BrowserAgent:
    """Advanced browser automation agent with reasoning capabilities using Playwright."""
    
    def __init__(self, task_query: str, llm_service=None, user_id: str = "default_user", agent_id: Optional[str] = None):
        """
        Initialize Browser Agent.
        
        Args:
            task_query: The task to execute in the browser
            llm_service: LLM service for reasoning (optional)
            user_id: User identifier
            agent_id: Agent identifier
        """
        self.task_query = task_query
        self.llm_service = llm_service
        self.user_id = user_id
        self.agent_id = agent_id
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.recorded_steps: List[Dict] = []
        self.captcha_detected = False
        self.captcha_url = None
    
    async def initialize_browser(self):
        """Initialize browser if not already initialized."""
        if self.playwright is None:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=False)
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            self.page = await self.context.new_page()
    
    async def DETECT_CAPTCHA(self) -> bool:
        """
        Detect if a CAPTCHA is present on the current page.
        
        Returns:
            True if CAPTCHA is detected, False otherwise
        """
        if not self.page:
            return False
        
        try:
            # Wait a moment for page to load
            await asyncio.sleep(1)
            
            # Check for common CAPTCHA indicators
            captcha_indicators = [
                # reCAPTCHA
                'iframe[src*="recaptcha"]',
                'div[class*="recaptcha"]',
                'div[id*="recaptcha"]',
                '.g-recaptcha',
                '[data-sitekey]',
                # hCaptcha
                'iframe[src*="hcaptcha"]',
                'div[id*="hcaptcha"]',
                '.h-captcha',
                # Cloudflare Turnstile
                'iframe[src*="challenges.cloudflare.com"]',
                'div[class*="cf-turnstile"]',
                # Generic CAPTCHA indicators
                'div[class*="captcha"]',
                'div[id*="captcha"]',
                'input[name*="captcha"]',
                # Text-based indicators in page content
                'text=verify you are human',
                'text=prove you are not a robot',
                'text=I\'m not a robot',
                'text=security check',
                'text=human verification'
            ]
            
            # Check for CAPTCHA elements
            for indicator in captcha_indicators:
                try:
                    if indicator.startswith('text='):
                        # Text-based search
                        text_query = indicator.replace('text=', '')
                        element = await self.page.query_selector(f'text={text_query}')
                        if element:
                            logger.warning(f"CAPTCHA detected via text indicator: {text_query}")
                            return True
                    else:
                        # CSS selector
                        element = await self.page.query_selector(indicator)
                        if element:
                            is_visible = await element.is_visible()
                            if is_visible:
                                logger.warning(f"CAPTCHA detected via selector: {indicator}")
                                return True
                except Exception as e:
                    # Continue checking other indicators
                    continue
            
            # Check page content for CAPTCHA keywords
            try:
                page_content = await self.page.content()
                page_text = await self.page.evaluate('() => document.body.innerText')
                
                captcha_keywords = [
                    'recaptcha',
                    'hcaptcha',
                    'captcha',
                    'verify you are human',
                    'prove you are not a robot',
                    'i\'m not a robot',
                    'security check',
                    'human verification',
                    'cloudflare',
                    'turnstile',
                    'challenge'
                ]
                
                page_content_lower = (page_content + page_text).lower()
                for keyword in captcha_keywords:
                    if keyword in page_content_lower:
                        # Additional check: make sure it's not just a mention
                        # Look for common CAPTCHA patterns
                        if any(pattern in page_content_lower for pattern in [
                            f'class="{keyword}',
                            f'id="{keyword}',
                            f'data-{keyword}',
                            f'src*={keyword}'
                        ]):
                            logger.warning(f"CAPTCHA detected via content keyword: {keyword}")
                            return True
            except Exception as e:
                logger.debug(f"Error checking page content for CAPTCHA: {e}")
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting CAPTCHA: {e}")
            return False
    
    def NOTIFY_USER_FOR_CAPTCHA(self, url: str, page_title: str = "") -> str:
        """
        Generate a user notification message when all fallbacks are blocked by CAPTCHAs.
        
        Args:
            url: URL(s) where CAPTCHA was detected
            page_title: Optional page title
            
        Returns:
            Notification message for the user
        """
        message = f"""Automated searches are blocked by CAPTCHAs across primary and fallback sources.

CAPTCHA Detected At:
{url}

The automation has tried multiple alternative search engines and sources, but all were blocked by CAPTCHA verification.

To proceed, you have the following options:

Option 1: Complete CAPTCHA Manually
- Open the URL(s) listed above in your browser
- Complete the CAPTCHA manually
- Once completed, reply with "CAPTCHA_COMPLETED" and the automation will resume

Option 2: Provide Alternative Source
- Provide an alternative URL or API endpoint that authorizes access
- Or suggest a permitted data source (RSS/API/allowed site)

Option 3: Use Authorized Access
- If you have API keys or OAuth credentials for authorized access, provide them
- Only short-lived session confirmations or OAuth via official flows are acceptable

IMPORTANT SECURITY NOTES:
- Do NOT share passwords, session tokens, or secret API keys
- Do NOT provide screenshots that contain sensitive information
- Only share the CAPTCHA challenge area if a screenshot is helpful (not login forms or sensitive data)
- This is a security measure to protect websites from automated abuse

The browser window(s) may remain open for you to complete CAPTCHAs manually if needed."""
        
        if page_title:
            message = f"Page: {page_title}\n\n" + message
        
        return message
    
    async def WAIT_FOR_CAPTCHA_COMPLETION(self, max_wait_seconds: int = 300, check_interval: int = 3) -> bool:
        """
        Wait for user to complete CAPTCHA by polling the page.
        Checks if we're past the CAPTCHA page and can access the target content.
        
        Args:
            max_wait_seconds: Maximum time to wait for CAPTCHA completion (default: 5 minutes)
            check_interval: How often to check for CAPTCHA completion in seconds (default: 3 seconds)
        
        Returns:
            True if CAPTCHA appears to be resolved, False if timeout
        """
        if not self.page:
            logger.warning("No page available to check CAPTCHA completion")
            return False
        
        logger.info(f"Waiting for user to complete CAPTCHA (max wait: {max_wait_seconds}s, check interval: {check_interval}s)")
        
        start_time = asyncio.get_event_loop().time()
        check_count = 0
        
        while True:
            elapsed_time = asyncio.get_event_loop().time() - start_time
            
            if elapsed_time >= max_wait_seconds:
                logger.warning(f"Timeout waiting for CAPTCHA completion after {elapsed_time:.1f} seconds")
                return False
            
            check_count += 1
            logger.debug(f"Checking CAPTCHA status (attempt {check_count}, elapsed: {elapsed_time:.1f}s)")
            
            try:
                # Wait a moment for page to update
                await asyncio.sleep(check_interval)
                
                # Get current URL
                current_url = self.page.url
                
                # Check if we're still on a CAPTCHA page
                is_captcha_page = await self.DETECT_CAPTCHA()
                
                # Also check if URL indicates CAPTCHA page
                captcha_url_indicators = ['/sorry/', 'captcha', 'challenge', 'verify']
                is_captcha_url = any(indicator in current_url.lower() for indicator in captcha_url_indicators)
                
                # If no CAPTCHA detected and not on CAPTCHA URL, assume it's resolved
                if not is_captcha_page and not is_captcha_url:
                    logger.info(f"CAPTCHA appears to be resolved! Current URL: {current_url}")
                    logger.info(f"Resolved after {elapsed_time:.1f} seconds ({check_count} checks)")
                    
                    # Additional check: wait a moment and verify page loaded successfully
                    await asyncio.sleep(2)
                    try:
                        page_title = await self.page.title()
                        logger.info(f"Page title after CAPTCHA: {page_title}")
                        
                        # Check one more time to be sure
                        final_check = await self.DETECT_CAPTCHA()
                        if not final_check:
                            logger.info("CAPTCHA confirmed resolved. Ready to continue.")
                            self.captcha_detected = False  # Reset flag
                            return True
                    except Exception as e:
                        logger.warning(f"Error verifying page after CAPTCHA: {e}")
                        # Still return True as we're past the CAPTCHA page
                        self.captcha_detected = False
                        return True
                
                # Still on CAPTCHA page, continue waiting
                if check_count % 10 == 0:  # Log every 10 checks
                    logger.info(f"Still waiting for CAPTCHA completion... (elapsed: {elapsed_time:.1f}s)")
                
            except Exception as e:
                logger.error(f"Error checking CAPTCHA status: {e}")
                # Continue waiting despite error
                await asyncio.sleep(check_interval)
    
    async def WAIT_FOR_USER_CONFIRMATION(self) -> bool:
        """
        Wait for user confirmation that CAPTCHA is completed.
        Uses polling to detect when CAPTCHA is resolved.
        
        Returns:
            True if CAPTCHA is resolved, False if timeout
        """
        return await self.WAIT_FOR_CAPTCHA_COMPLETION()
    
    async def REASON_AND_CHOOSE_FALLBACK(self, query: str) -> List[Dict]:
        """
        Use LLM to reason about the query and choose appropriate fallback strategies.
        
        Args:
            query: User query
            
        Returns:
            List of fallback strategies to try
        """
        if self.llm_service:
            try:
                from pydantic import BaseModel
                from typing import List as TypingList
                
                class FallbackStrategySchema(BaseModel):
                    type: str  # search_engine, site_search, cache
                    engine: str = ""  # bing, duckduckgo (for search_engine)
                    site: str = ""  # site domain (for site_search)
                    query: str = ""  # search query
                    description: str
                
                class FallbackListSchema(BaseModel):
                    fallbacks: TypingList[FallbackStrategySchema]
                
                system_instruction = """You are an AI assistant that suggests fallback search strategies when primary search is blocked.

IMPORTANT: DO NOT suggest Google as a fallback. Google is not allowed.

Given a user query, suggest appropriate fallback strategies including:
1. Alternative search engines (Bing only - NO GOOGLE) - DuckDuckGo is the default
2. Site-specific searches on relevant authoritative sources
3. Cached version searches
4. For news queries: suggest news sites (bbc.com, techcrunch.com, reuters.com, cnn.com, theverge.com)
5. For technical queries: suggest tech sites (medium.com, dev.to, stackoverflow.com, github.com)
6. For general queries: suggest relevant authoritative sites

Return a list of fallback strategies with:
- type: "search_engine" | "site_search" | "cache"
- engine: "bing" only (if type is search_engine) - DO NOT suggest Google
- site: domain name like "bbc.com" (if type is site_search)
- query: the search query to use
- description: human-readable description

Always prioritize:
1. Alternative search engines (Bing only - NO GOOGLE) - since DuckDuckGo is default
2. Then site-specific searches on relevant authoritative sources
3. Finally cached version searches

Return as JSON with a "fallbacks" array."""
                
                reasoning_prompt = f"""
                User Query: "{query}"
                
                Suggest appropriate fallback search strategies for this query.
                Consider the query topic and suggest relevant authoritative sites and alternative search engines.
                """
                
                try:
                    response = self.llm_service.generate_content_with_Structured_schema(
                        system_instruction=system_instruction,
                        query=reasoning_prompt,
                        response_schema=FallbackListSchema
                    )
                    
                    # Validate and convert to list of dicts
                    if hasattr(response, 'fallbacks') and isinstance(response.fallbacks, list):
                        fallbacks = []
                        for fb in response.fallbacks:
                            if isinstance(fb, dict):
                                fallback_dict = fb
                            elif hasattr(fb, 'dict'):
                                fallback_dict = fb.dict()
                            elif hasattr(fb, 'model_dump'):
                                fallback_dict = fb.model_dump()
                            else:
                                continue
                            
                            # Validate fallback
                            fb_type = fallback_dict.get("type", "")
                            if fb_type not in ["search_engine", "site_search", "cache"]:
                                logger.warning(f"Invalid fallback type: {fb_type}, skipping")
                                continue
                            
                            # Ensure required fields
                            if not fallback_dict.get("query") or not fallback_dict.get("query").strip():
                                fallback_dict["query"] = query
                            if not fallback_dict.get("description") or not fallback_dict.get("description").strip():
                                fallback_dict["description"] = f"Fallback: {fb_type}"
                            
                            # Validate engine for search_engine type
                            if fb_type == "search_engine":
                                engine = fallback_dict.get("engine", "").lower()
                                # DO NOT allow Google - only Bing
                                if engine == "google":
                                    logger.warning(f"Google is not allowed as fallback, skipping")
                                    continue
                                if engine not in ["bing"]:
                                    logger.warning(f"Invalid engine: {engine}, defaulting to bing")
                                    fallback_dict["engine"] = "bing"
                            
                            # Validate site for site_search type
                            if fb_type == "site_search":
                                if not fallback_dict.get("site") or not fallback_dict.get("site").strip():
                                    logger.warning(f"Site search missing site domain, skipping")
                                    continue
                            
                            fallbacks.append(fallback_dict)
                        
                        if fallbacks:
                            logger.info(f"LLM suggested {len(fallbacks)} fallback strategies")
                            return fallbacks
                        else:
                            logger.warning("LLM returned empty fallbacks list, using default")
                    else:
                        logger.warning("LLM response missing fallbacks, using default")
                except Exception as e:
                    logger.warning(f"Error with LLM fallback reasoning: {e}, using default fallbacks")
            except Exception as e:
                logger.error(f"LLM fallback reasoning failed: {e}, using default fallbacks")
        
        # Default fallback strategies (fallback logic)
        # Since DuckDuckGo is default, fallback to Bing only (NO GOOGLE)
        fallbacks = []
        query_lower = query.lower()
        
        # Try Bing as fallback (NO GOOGLE)
        fallbacks.append({
            "type": "search_engine",
            "engine": "bing",
            "query": query,
            "description": f"Search Bing for {query}"
        })
        
        # For news queries, try news sites
        if any(word in query_lower for word in ['news', 'latest', 'recent', 'update']):
            news_sites = ['bbc.com', 'techcrunch.com', 'theverge.com', 'reuters.com', 'cnn.com']
            for site in news_sites:
                fallbacks.append({
                    "type": "site_search",
                    "site": site,
                    "query": query,
                    "description": f"Search {site} for {query}"
                })
        
        # For technical queries, try tech blogs
        if any(word in query_lower for word in ['api', 'code', 'programming', 'developer', 'tech', 'software']):
            tech_sites = ['medium.com', 'dev.to', 'stackoverflow.com', 'github.com']
            for site in tech_sites:
                fallbacks.append({
                    "type": "site_search",
                    "site": site,
                    "query": query,
                    "description": f"Search {site} for {query}"
                })
        
        # Try cached version
        fallbacks.append({
            "type": "cache",
            "query": query,
            "description": f"Get cached version of results for {query}"
        })
        
        return fallbacks
    
    async def EXECUTE_FALLBACK_STRATEGY(self, fallback: Dict, original_query: str) -> TaskResult:
        """
        Execute a fallback strategy.
        
        Args:
            fallback: Fallback strategy dict
            original_query: Original user query
            
        Returns:
            TaskResult from the fallback attempt
        """
        try:
            fallback_type = fallback.get("type")
            
            if fallback_type == "search_engine":
                engine = fallback.get("engine")
                query = fallback.get("query", original_query)
                
                # DO NOT use Google - skip if Google is requested
                if engine == "google":
                    logger.warning("Google fallback requested but not allowed. Skipping.")
                    return TaskResult(
                        success=False,
                        message="Google is not allowed as fallback",
                        error="Google not allowed",
                        data={"query": query, "fallback": fallback}
                    )
                elif engine == "bing":
                    result = await self.SEARCH_BING(query)
                    # Results are already included in SEARCH_BING response
                    return result
                    
            elif fallback_type == "site_search":
                site = fallback.get("site")
                query = fallback.get("query", original_query)
                result = await self.SITE_SPECIFIC_SEARCH(site, query)
                # Results are already included in SITE_SPECIFIC_SEARCH response
                return result
                
            elif fallback_type == "cache":
                query = fallback.get("query", original_query)
                result = await self.USE_CACHE_OPERATOR(query)
                # Results are already included in USE_CACHE_OPERATOR response
                return result
                
            return TaskResult(
                success=False,
                message=f"Unknown fallback type: {fallback_type}",
                error="Unknown fallback type",
                data={"fallback": fallback}
            )
        except Exception as e:
            logger.error(f"Error executing fallback strategy: {e}")
            return TaskResult(
                success=False,
                message=f"Error executing fallback: {str(e)}",
                error=str(e),
                data={"fallback": fallback}
            )
    
    def REASON_AND_DECIDE(self, query: str) -> ActionPlan:
        """
        Use LLM-based reasoning to decide the best action for the query.
        
        Args:
            query: User query
            
        Returns:
            ActionPlan with recommended action
        """
        if self.llm_service:
            try:
                # Use LLM with structured schema for reliable parsing
                from pydantic import BaseModel
                
                class ActionPlanSchema(BaseModel):
                    action: str  # OPEN_URL, SEARCH_DUCKDUCKGO, SEARCH_GOOGLE, READ_PAGE, FIX_ISSUE
                    target: str  # URL or search query
                    reason: str
                    expected_outcome: str
                
                system_instruction = """You are an AI assistant that analyzes user queries and determines the best browser automation action.

IMPORTANT: DO NOT use Google. Only use DuckDuckGo for searches.

Analyze the user query and determine:
1. Does the query contain a URL? If yes, extract the full URL.
2. What is the user's intent? (search for information, open a website, read a page, fix an issue)
3. What action should be taken? Choose one of: OPEN_URL, SEARCH_DUCKDUCKGO, READ_PAGE, FIX_ISSUE
4. What are the search terms if it's a search query? (extract key terms, remove command words like "search", "find", "look for")
5. What is the expected outcome?

Rules:
- If URL is present: action = "OPEN_URL", target = the URL
- If search intent: action = "SEARCH_DUCKDUCKGO", target = cleaned search terms (remove "search for", "find", etc.)
- DEFAULT: Use DuckDuckGo as the ONLY search engine - DO NOT use Google
- DO NOT suggest SEARCH_GOOGLE - it is not allowed
- If information request without URL: action = "SEARCH_DUCKDUCKGO", target = the query terms
- Be smart about extracting search terms - remove filler words but keep the core meaning

Return your analysis as JSON with: action, target, reason, expected_outcome"""
                
                reasoning_prompt = f"""
                User Query: "{query}"
                
                Analyze this query and determine the best action to take.
                Extract URLs if present, identify search intent, and clean search terms appropriately.
                """
                
                try:
                    response = self.llm_service.generate_content_with_Structured_schema(
                        system_instruction=system_instruction,
                        query=reasoning_prompt,
                        response_schema=ActionPlanSchema
                    )
                    
                    # Validate the response
                    if hasattr(response, 'action') and hasattr(response, 'target'):
                        # Validate action is one of the allowed values (NO GOOGLE)
                        allowed_actions = ["OPEN_URL", "SEARCH_DUCKDUCKGO", "READ_PAGE", "FIX_ISSUE"]
                        if response.action not in allowed_actions:
                            logger.warning(f"Invalid action from LLM: {response.action}, defaulting to SEARCH_DUCKDUCKGO")
                            response.action = "SEARCH_DUCKDUCKGO"
                        # DO NOT allow SEARCH_GOOGLE - convert to SEARCH_DUCKDUCKGO
                        if response.action == "SEARCH_GOOGLE":
                            logger.warning("LLM suggested Google, but Google is not allowed. Converting to DuckDuckGo.")
                            response.action = "SEARCH_DUCKDUCKGO"
                        
                        # Ensure target is not empty
                        if not response.target or not response.target.strip():
                            logger.warning("Empty target from LLM, using original query")
                            response.target = query
                        
                        # Create ActionPlan from validated response
                        return ActionPlan(
                            action=response.action,
                            target=response.target.strip(),
                            reason=response.reason if hasattr(response, 'reason') else f"LLM determined {response.action}",
                            expected_outcome=response.expected_outcome if hasattr(response, 'expected_outcome') else "Complete the requested task"
                        )
                    else:
                        logger.warning("LLM response missing required fields, using fallback")
                except Exception as e:
                    logger.warning(f"Error with structured schema: {e}, trying fallback")
                    
            except Exception as e:
                logger.error(f"LLM reasoning failed: {e}, using fallback logic")
        
        # Fallback logic without LLM (simple regex-based)
        query_lower = query.lower()
        
        # Check for URL (basic pattern matching)
        url_pattern = r'https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9-]+\.[a-zA-Z]{2,}'
        urls = re.findall(url_pattern, query)
        if urls:
            url = urls[0]
            if not url.startswith('http'):
                url = 'https://' + url
            return ActionPlan(
                action="OPEN_URL",
                target=url,
                reason="URL detected in query (fallback logic)",
                expected_outcome="Navigate to the specified website"
            )
        
        # Default: search DuckDuckGo (fallback)
        return ActionPlan(
            action="SEARCH_DUCKDUCKGO",
            target=query,
            reason="No specific URL provided, using DuckDuckGo search (default search engine)",
            expected_outcome="Find relevant information"
        )
    
    async def OPEN_URL(self, url: str) -> TaskResult:
        """
        Open a URL in the browser.
        
        Args:
            url: URL to open
            
        Returns:
            TaskResult with execution details
        """
        try:
            await self.initialize_browser()
            
            # Ensure URL has protocol
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            logger.info(f"Opening URL: {url}")
            await self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await self.WAIT_FOR_PAGE_LOAD(timeout=30000)
            
            # Check for CAPTCHA immediately after page load
            captcha_found = await self.DETECT_CAPTCHA()
            if captcha_found:
                self.captcha_detected = True
                self.captcha_url = self.page.url
                title = await self.page.title()
                notification = self.NOTIFY_USER_FOR_CAPTCHA(self.page.url, title)
                
                logger.warning(f"CAPTCHA detected on {url}. Automation paused. Browser will remain open.")
                logger.info(f"Browser is open at: {self.page.url}")
                logger.info("User can complete CAPTCHA in the browser window. Browser will stay open.")
                
                return TaskResult(
                    success=False,
                    message=notification,
                    error="CAPTCHA_DETECTED",
                    data={
                        "title": title,
                        "url": self.page.url,
                        "captcha_detected": True,
                        "browser_open": True,
                        "message": "Browser remains open for you to complete the CAPTCHA manually."
                    }
                )
            
            title = await self.page.title()
            current_url = self.page.url
            
            return TaskResult(
                success=True,
                message=f"Successfully opened {url}",
                data={
                    "title": title,
                    "url": current_url
                }
            )
        except Exception as e:
            logger.error(f"Error opening URL {url}: {e}")
            return TaskResult(
                success=False,
                message=f"Failed to open {url}",
                error=str(e),
                data={"url": url}
            )
    
    async def NEW_TAB(self) -> Optional[Page]:
        """
        Open a new browser tab.
        
        Returns:
            New Page object, or None if failed
        """
        try:
            if not self.page:
                await self.initialize_browser()
            
            if self.context:
                new_page = await self.context.new_page()
                logger.info("Opened new tab")
                return new_page
            return None
        except Exception as e:
            logger.error(f"Error opening new tab: {e}")
            return None
    
    async def SEARCH_BING(self, query: str) -> TaskResult:
        """
        Perform a Bing search.
        
        Args:
            query: Search query
            
        Returns:
            TaskResult with search results
        """
        try:
            await self.initialize_browser()
            
            logger.info(f"Searching Bing for: {query}")
            
            # Navigate to Bing and wait for full load
            logger.info("Navigating to Bing...")
            await self.page.goto("https://www.bing.com", wait_until='domcontentloaded', timeout=30000)
            await self.WAIT_FOR_PAGE_LOAD(timeout=30000)
            
            # Check for CAPTCHA
            captcha_found = await self.DETECT_CAPTCHA()
            if captcha_found:
                self.captcha_detected = True
                self.captcha_url = self.page.url
                title = await self.page.title()
                return TaskResult(
                    success=False,
                    message=f"CAPTCHA detected on Bing",
                    error="CAPTCHA_DETECTED",
                    data={
                        "title": title,
                        "url": self.page.url,
                        "query": query,
                        "search_engine": "bing"
                    }
                )
            
            # Find search box - try multiple selectors with proper waiting
            logger.info("Waiting for Bing search box to be ready...")
            search_selectors = ['input[name="q"]', 'input[type="search"]', '#sb_form_q']
            search_box = None
            
            for selector in search_selectors:
                search_box = await self.WAIT_FOR_ELEMENT_READY(selector, timeout=5000, max_retries=3)
                if search_box:
                    logger.info(f"Found Bing search box using selector: {selector}")
                    break
            
            if not search_box:
                return TaskResult(
                    success=False,
                    message="Could not find Bing search box after multiple attempts",
                    error="Search box element not found",
                    data={"query": query, "search_engine": "bing"}
                )
            
            # Type search query - clear first, then type
            logger.info(f"Typing search query: {query}")
            await search_box.click()  # Focus on the element
            await asyncio.sleep(0.3)
            await search_box.fill('')  # Clear any existing text
            await asyncio.sleep(0.2)
            await search_box.type(query, delay=50)  # Type with delay for reliability
            await asyncio.sleep(0.5)
            
            # Submit search
            logger.info("Submitting search...")
            await search_box.press("Enter")
            
            # Wait for search results page to load
            await self.WAIT_FOR_PAGE_LOAD(timeout=30000)
            await asyncio.sleep(2)  # Additional wait for results to render
            
            # Check for CAPTCHA on results page
            captcha_found = await self.DETECT_CAPTCHA()
            if captcha_found:
                self.captcha_detected = True
                self.captcha_url = self.page.url
                title = await self.page.title()
                return TaskResult(
                    success=False,
                    message=f"CAPTCHA detected on Bing search results",
                    error="CAPTCHA_DETECTED",
                    data={
                        "title": title,
                        "url": self.page.url,
                        "query": query,
                        "search_engine": "bing"
                    }
                )
            
            title = await self.page.title()
            current_url = self.page.url
            
            # Extract search results using READ_TOP_RESULTS
            read_result = await self.READ_TOP_RESULTS(limit=5)
            results = read_result.data.get("results", []) if read_result.success else []
            
            return TaskResult(
                success=True,
                message=f"Successfully searched Bing for: {query}",
                data={
                    "title": title,
                    "url": current_url,
                    "query": query,
                    "results": results,
                    "results_count": len(results),
                    "search_engine": "bing"
                }
            )
        except Exception as e:
            logger.error(f"Error searching Bing: {e}")
            return TaskResult(
                success=False,
                message=f"Failed to search Bing for: {query}",
                error=str(e),
                data={"query": query, "search_engine": "bing"}
            )
    
    async def SEARCH_DUCKDUCKGO(self, query: str) -> TaskResult:
        """
        Perform a DuckDuckGo search.
        
        Args:
            query: Search query
            
        Returns:
            TaskResult with search results
        """
        try:
            await self.initialize_browser()
            
            logger.info(f"Searching DuckDuckGo for: {query}")
            
            # Navigate to DuckDuckGo and wait for full load
            logger.info("Navigating to DuckDuckGo (default search engine)...")
            await self.page.goto("https://www.duckduckgo.com", wait_until='domcontentloaded', timeout=30000)
            await self.WAIT_FOR_PAGE_LOAD(timeout=30000)
            
            # Check for CAPTCHA
            captcha_found = await self.DETECT_CAPTCHA()
            if captcha_found:
                self.captcha_detected = True
                self.captcha_url = self.page.url
                title = await self.page.title()
                return TaskResult(
                    success=False,
                    message=f"CAPTCHA detected on DuckDuckGo",
                    error="CAPTCHA_DETECTED",
                    data={
                        "title": title,
                        "url": self.page.url,
                        "query": query,
                        "search_engine": "duckduckgo"
                    }
                )
            
            # Find search box - wait for it to be visible, enabled, and interactive
            logger.info("Waiting for DuckDuckGo search box to be ready...")
            search_selectors = ['input[name="q"]', 'input[type="search"]', '#search_form_input_homepage']
            search_box = None
            
            for selector in search_selectors:
                search_box = await self.WAIT_FOR_ELEMENT_READY(selector, timeout=10000, max_retries=5)
                if search_box:
                    logger.info(f"Found DuckDuckGo search box using selector: {selector}")
                    break
            
            if not search_box:
                return TaskResult(
                    success=False,
                    message="Could not find DuckDuckGo search box after multiple attempts",
                    error="Search box element not found",
                    data={"query": query, "search_engine": "duckduckgo"}
                )
            
            # Type search query - clear first, then type
            logger.info(f"Typing search query: {query}")
            await search_box.click()  # Focus on the element
            await asyncio.sleep(0.3)
            await search_box.fill('')  # Clear any existing text
            await asyncio.sleep(0.2)
            await search_box.type(query, delay=50)  # Type with delay for reliability
            await asyncio.sleep(0.5)
            
            # Submit search
            logger.info("Submitting search...")
            await search_box.press("Enter")
            
            # Wait for search results page to load
            await self.WAIT_FOR_PAGE_LOAD(timeout=30000)
            await asyncio.sleep(2)  # Additional wait for results to render
            
            # Check for CAPTCHA on results page
            captcha_found = await self.DETECT_CAPTCHA()
            if captcha_found:
                self.captcha_detected = True
                self.captcha_url = self.page.url
                title = await self.page.title()
                return TaskResult(
                    success=False,
                    message=f"CAPTCHA detected on DuckDuckGo search results",
                    error="CAPTCHA_DETECTED",
                    data={
                        "title": title,
                        "url": self.page.url,
                        "query": query,
                        "search_engine": "duckduckgo"
                    }
                )
            
            title = await self.page.title()
            current_url = self.page.url
            
            # Extract search results using READ_TOP_RESULTS
            read_result = await self.READ_TOP_RESULTS(limit=5)
            results = read_result.data.get("results", []) if read_result.success else []
            
            return TaskResult(
                success=True,
                message=f"Successfully searched DuckDuckGo for: {query}",
                data={
                    "title": title,
                    "url": current_url,
                    "query": query,
                    "results": results,
                    "results_count": len(results),
                    "search_engine": "duckduckgo"
                }
            )
        except Exception as e:
            logger.error(f"Error searching DuckDuckGo: {e}")
            return TaskResult(
                success=False,
                message=f"Failed to search DuckDuckGo for: {query}",
                error=str(e),
                data={"query": query, "search_engine": "duckduckgo"}
            )
    
    async def SITE_SPECIFIC_SEARCH(self, site: str, query: str) -> TaskResult:
        """
        Perform a site-specific search using DuckDuckGo's site: operator.
        NO GOOGLE - only use DuckDuckGo or Bing.
        
        Args:
            site: Site domain (e.g., "bbc.com", "techcrunch.com")
            query: Search query
            
        Returns:
            TaskResult with search results
        """
        try:
            site_query = f"site:{site} {query}"
            logger.info(f"Performing site-specific search: {site_query}")
            
            # Try with DuckDuckGo first (NO GOOGLE)
            result = await self.SEARCH_DUCKDUCKGO(site_query)
            if result.success and result.error != "CAPTCHA_DETECTED":
                return result
            
            # If DuckDuckGo has CAPTCHA or fails, try Bing (NO GOOGLE)
            logger.info(f"DuckDuckGo blocked, trying Bing for site search: {site_query}")
            return await self.SEARCH_BING(site_query)
        except Exception as e:
            logger.error(f"Error in site-specific search: {e}")
            return TaskResult(
                success=False,
                message=f"Failed site-specific search for {site}",
                error=str(e),
                data={"site": site, "query": query}
            )
    
    async def USE_CACHE_OPERATOR(self, query: str) -> TaskResult:
        """
        Try to get cached version using cache: operator.
        
        Args:
            query: Original query
            
        Returns:
            TaskResult with cached results
        """
        try:
            cache_query = f"cache:{query}"
            logger.info(f"Trying cached version: {cache_query}")
            
            # Try with Google cache operator
            result = await self.SEARCH_GOOGLE(cache_query)
            if result.error != "CAPTCHA_DETECTED":
                return result
            
            # If blocked, try webcache
            webcache_query = f"webcache:{query}"
            logger.info(f"Trying webcache: {webcache_query}")
            return await self.SEARCH_BING(webcache_query)
        except Exception as e:
            logger.error(f"Error getting cached version: {e}")
            return TaskResult(
                success=False,
                message=f"Failed to get cached version",
                error=str(e),
                data={"query": query}
            )
    
    async def READ_TOP_RESULTS(self, limit: int = 5) -> TaskResult:
        """
        Read the top search results from the current page.
        Extracts detailed information including titles, URLs, and snippets.
        
        Args:
            limit: Number of results to read
            
        Returns:
            TaskResult with top results
        """
        try:
            if not self.page:
                return TaskResult(
                    success=False,
                    message="No page available to read results",
                    error="No page"
                )
            
            current_url = self.page.url
            title = await self.page.title()
            
            # Extract results based on current search engine
            results = []
            
            try:
                # Wait for results to load
                await asyncio.sleep(2)
                
                # Try multiple selectors for different search engines
                # Google
                google_selectors = [
                    'div[data-header-feature="0"] h3',
                    'div.g h3',
                    'div[data-sokoban-container] h3',
                    '.yuRUbf h3',
                    'h3.LC20lb'
                ]
                
                # Bing
                bing_selectors = [
                    'h2 a',
                    '.b_title a',
                    '.b_algo h2 a',
                    'li.b_algo h2 a'
                ]
                
                # DuckDuckGo
                ddg_selectors = [
                    'h2 a.result__a',
                    '.result__title a',
                    'a.result__a',
                    '.web-result h2 a'
                ]
                
                all_selectors = google_selectors + bing_selectors + ddg_selectors
                
                for selector in all_selectors:
                    try:
                        result_elements = await self.page.query_selector_all(selector)
                        if result_elements:
                            logger.info(f"Found {len(result_elements)} results using selector: {selector}")
                            for i, elem in enumerate(result_elements[:limit]):
                                try:
                                    # Get title
                                    title_text = await elem.inner_text()
                                    if not title_text or len(title_text.strip()) < 3:
                                        continue
                                    
                                    # Get link - try multiple methods
                                    link = None
                                    
                                    # Method 1: Check if element itself is a link
                                    try:
                                        if await elem.evaluate('(el) => el.tagName === "A"'):
                                            link = await elem.get_attribute('href')
                                    except:
                                        pass
                                    
                                    # Method 2: Find link in parent or child
                                    if not link:
                                        try:
                                            link_elem = await elem.query_selector('a')
                                            if link_elem:
                                                link = await link_elem.get_attribute('href')
                                        except:
                                            pass
                                    
                                    # Method 3: Find parent link using JavaScript
                                    if not link:
                                        try:
                                            link = await elem.evaluate("""(elem) => {
                                                const link = elem.closest('a');
                                                return link ? link.href : null;
                                            }""")
                                        except:
                                            pass
                                    
                                    # Method 4: Try finding nearby link
                                    if not link:
                                        try:
                                            parent_container = await elem.evaluate_handle('(elem) => elem.closest("div, li, article")')
                                            if parent_container:
                                                link_elem = await parent_container.query_selector('a[href]')
                                                if link_elem:
                                                    link = await link_elem.get_attribute('href')
                                        except:
                                            pass
                                    
                                    # Clean and validate URL
                                    if link:
                                        # Remove URL parameters for DuckDuckGo redirects
                                        if 'duckduckgo.com' in current_url and 'uddg=' in link:
                                            # Extract actual URL from DuckDuckGo redirect
                                            import urllib.parse
                                            try:
                                                parsed = urllib.parse.urlparse(link)
                                                params = urllib.parse.parse_qs(parsed.query)
                                                if 'uddg' in params:
                                                    link = params['uddg'][0]
                                            except:
                                                pass
                                        
                                        # Handle relative URLs
                                        if link.startswith('/'):
                                            if 'google.com' in current_url:
                                                link = f"https://www.google.com{link}"
                                            elif 'bing.com' in current_url:
                                                link = f"https://www.bing.com{link}"
                                        
                                        # Validate URL
                                        if not link.startswith('http') and not link.startswith('//'):
                                            # Skip invalid URLs
                                            continue
                                        
                                        # Normalize URL
                                        if link.startswith('//'):
                                            link = 'https:' + link
                                    
                                    # Get snippet/description if available
                                    snippet = ""
                                    try:
                                        # Try to find snippet near the result
                                        result_container = await elem.evaluate_handle('(elem) => elem.closest("div[class*="result"], div[class*="g"], li")')
                                        if result_container:
                                            snippet_elem = await result_container.query_selector('.VwiC3b, .b_caption p, .result__snippet, .s')
                                            if snippet_elem:
                                                snippet = await snippet_elem.inner_text()
                                                snippet = snippet[:200]  # Limit snippet length
                                    except:
                                        pass
                                    
                                    if title_text and link:
                                        results.append({
                                            "title": title_text.strip(),
                                            "url": link,
                                            "snippet": snippet.strip() if snippet else ""
                                        })
                                    
                                    # Break if we have enough results
                                    if len(results) >= limit:
                                        break
                                except Exception as e:
                                    logger.debug(f"Error extracting individual result: {e}")
                                    continue
                            
                            # If we found results, break
                            if results:
                                break
                    except Exception as e:
                        logger.debug(f"Error with selector {selector}: {e}")
                        continue
                
                # If still no results, try a more aggressive approach
                if not results:
                    logger.warning("Standard selectors failed, trying alternative extraction")
                    try:
                        # Get all links on the page
                        all_links = await self.page.query_selector_all('a[href]')
                        for link_elem in all_links[:limit * 3]:  # Check more links
                            try:
                                href = await link_elem.get_attribute('href')
                                if href and ('http' in href or href.startswith('/')):
                                    title_text = await link_elem.inner_text()
                                    if title_text and len(title_text.strip()) > 10:
                                        # Filter out navigation links
                                        if any(skip in href.lower() for skip in ['/search', '/images', '/maps', '/settings', '/preferences']):
                                            continue
                                        results.append({
                                            "title": title_text.strip()[:100],
                                            "url": href,
                                            "snippet": ""
                                        })
                                        if len(results) >= limit:
                                            break
                            except:
                                continue
                    except Exception as e:
                        logger.warning(f"Alternative extraction also failed: {e}")
                
            except Exception as e:
                logger.error(f"Error extracting results: {e}", exc_info=True)
            
            logger.info(f"Extracted {len(results)} results from {current_url}")
            
            return TaskResult(
                success=True,
                message=f"Read {len(results)} top results",
                data={
                    "title": title,
                    "url": current_url,
                    "results": results,
                    "count": len(results)
                }
            )
        except Exception as e:
            logger.error(f"Error reading top results: {e}", exc_info=True)
            return TaskResult(
                success=False,
                message="Failed to read top results",
                error=str(e)
            )
    
    async def SEARCH_GOOGLE(self, query: str) -> TaskResult:
        """
        Perform a Google search.
        
        Args:
            query: Search query
            
        Returns:
            TaskResult with search results
        """
        try:
            await self.initialize_browser()
            
            logger.info(f"Searching Google for: {query}")
            
            # Navigate to Google and wait for full load
            logger.info("Navigating to Google...")
            await self.page.goto("https://www.google.com", wait_until='domcontentloaded', timeout=30000)
            await self.WAIT_FOR_PAGE_LOAD(timeout=30000)
            
            # Check for CAPTCHA on Google homepage
            captcha_found = await self.DETECT_CAPTCHA()
            if captcha_found:
                self.captcha_detected = True
                self.captcha_url = self.page.url
                title = await self.page.title()
                notification = self.NOTIFY_USER_FOR_CAPTCHA(self.page.url, title)
                
                logger.warning(f"CAPTCHA detected on Google. Automation paused. Browser will remain open.")
                logger.info(f"Browser is open at: {self.page.url}")
                logger.info("User can complete CAPTCHA in the browser window.")
                
                return TaskResult(
                    success=False,
                    message=notification,
                    error="CAPTCHA_DETECTED",
                    data={
                        "title": title,
                        "url": self.page.url,
                        "query": query,
                        "captcha_detected": True,
                        "browser_open": True,
                        "message": "Browser remains open for you to complete the CAPTCHA manually."
                    }
                )
            
            # Find search box - wait for it to be visible, enabled, and interactive
            logger.info("Waiting for Google search box to be ready...")
            search_selectors = [
                'textarea[name="q"]',
                'input[name="q"]',
                'textarea[aria-label*="Search"]',
                'input[type="search"]'
            ]
            
            search_box = None
            for selector in search_selectors:
                search_box = await self.WAIT_FOR_ELEMENT_READY(selector, timeout=5000, max_retries=3)
                if search_box:
                    logger.info(f"Found Google search box using selector: {selector}")
                    break
            
            if not search_box:
                return TaskResult(
                    success=False,
                    message="Could not find Google search box after multiple attempts",
                    error="Search box element not found",
                    data={"query": query}
                )
            
            # Type search query - clear first, then type
            logger.info(f"Typing search query: {query}")
            await search_box.click()  # Focus on the element
            await asyncio.sleep(0.3)
            await search_box.fill('')  # Clear any existing text
            await asyncio.sleep(0.2)
            await search_box.type(query, delay=50)  # Type with delay for reliability
            await asyncio.sleep(0.5)
            
            # Submit search
            logger.info("Submitting search...")
            await search_box.press("Enter")
            
            # Wait for search results page to load
            await self.WAIT_FOR_PAGE_LOAD(timeout=30000)
            await asyncio.sleep(2)  # Additional wait for results to render
            
            # Check for CAPTCHA on search results page
            captcha_found = await self.DETECT_CAPTCHA()
            if captcha_found:
                self.captcha_detected = True
                self.captcha_url = self.page.url
                title = await self.page.title()
                notification = self.NOTIFY_USER_FOR_CAPTCHA(self.page.url, title)
                
                logger.warning(f"CAPTCHA detected on search results page. Automation paused. Browser will remain open.")
                logger.info(f"Browser is open at: {self.page.url}")
                logger.info("User can complete CAPTCHA in the browser window.")
                
                return TaskResult(
                    success=False,
                    message=notification,
                    error="CAPTCHA_DETECTED",
                    data={
                        "title": title,
                        "url": self.page.url,
                        "query": query,
                        "captcha_detected": True,
                        "browser_open": True,
                        "message": "Browser remains open for you to complete the CAPTCHA manually."
                    }
                )
            
            title = await self.page.title()
            current_url = self.page.url
            
            # Extract search results using READ_TOP_RESULTS
            read_result = await self.READ_TOP_RESULTS(limit=5)
            results = read_result.data.get("results", []) if read_result.success else []
            
            return TaskResult(
                success=True,
                message=f"Successfully searched for: {query}",
                data={
                    "title": title,
                    "url": current_url,
                    "query": query,
                    "results": results,
                    "results_count": len(results)
                }
            )
        except Exception as e:
            logger.error(f"Error searching Google: {e}")
            return TaskResult(
                success=False,
                message=f"Failed to search Google for: {query}",
                error=str(e),
                data={"query": query}
            )
    
    async def READ_PAGE(self, url: Optional[str] = None) -> TaskResult:
        """
        Read and analyze the current page with detailed content extraction.
        
        Args:
            url: Optional URL to read (if not provided, reads current page)
            
        Returns:
            TaskResult with detailed page analysis
        """
        try:
            await self.initialize_browser()
            
            if url:
                open_result = await self.OPEN_URL(url)
                # If CAPTCHA was detected during OPEN_URL, return that result
                if open_result.error == "CAPTCHA_DETECTED":
                    return open_result
            
            # Check for CAPTCHA before reading page
            captcha_found = await self.DETECT_CAPTCHA()
            if captcha_found:
                self.captcha_detected = True
                self.captcha_url = self.page.url
                title = await self.page.title()
                notification = self.NOTIFY_USER_FOR_CAPTCHA(self.page.url, title)
                
                logger.warning(f"CAPTCHA detected while reading page. Automation paused. Browser will remain open.")
                logger.info(f"Browser is open at: {self.page.url}")
                logger.info("User can complete CAPTCHA in the browser window.")
                
                return TaskResult(
                    success=False,
                    message=notification,
                    error="CAPTCHA_DETECTED",
                    data={
                        "title": title,
                        "url": self.page.url,
                        "captcha_detected": True,
                        "browser_open": True,
                        "message": "Browser remains open for you to complete the CAPTCHA manually."
                    }
                )
            
            current_url = self.page.url
            title = await self.page.title()
            
            # Extract detailed page content
            try:
                # Get main content with better extraction
                body_text = await self.page.evaluate("""() => {
                    // Try to get main content area
                    const main = document.querySelector('main, article, .content, .post, .article, [role="main"]');
                    if (main) {
                        return main.innerText;
                    }
                    return document.body.innerText;
                }""")
                
                # Get meta description
                meta_desc = await self.page.evaluate("""() => {
                    const meta = document.querySelector('meta[name="description"], meta[property="og:description"]');
                    return meta ? meta.content : "";
                }""")
                
                # Get headings (H1, H2, H3)
                headings = await self.page.evaluate("""() => {
                    const h1s = Array.from(document.querySelectorAll("h1")).map(h => h.innerText).filter(t => t.trim());
                    const h2s = Array.from(document.querySelectorAll("h2")).map(h => h.innerText).filter(t => t.trim());
                    const h3s = Array.from(document.querySelectorAll("h3")).map(h => h.innerText).filter(t => t.trim());
                    return {h1: h1s.slice(0, 5), h2: h2s.slice(0, 10), h3: h3s.slice(0, 10)};
                }""")
                
                # Get article content (for news sites)
                article_content = await self.page.evaluate("""() => {
                    const article = document.querySelector('article, .article-body, .post-content, .entry-content, [class*="article"], [class*="content"]');
                    if (article) {
                        // Get paragraphs
                        const paragraphs = Array.from(article.querySelectorAll('p')).map(p => p.innerText).filter(t => t.trim() && t.length > 20);
                        return paragraphs.slice(0, 10).join('\\n\\n');
                    }
                    return "";
                }""")
                
                # Get publication date if available
                pub_date = await self.page.evaluate("""() => {
                    const time = document.querySelector('time[datetime], time[pubdate], [class*="date"], [class*="published"]');
                    if (time) {
                        return time.getAttribute('datetime') || time.innerText || time.getAttribute('pubdate');
                    }
                    // Try meta tags
                    const metaDate = document.querySelector('meta[property="article:published_time"], meta[name="pubdate"]');
                    return metaDate ? metaDate.content : "";
                }""")
                
                # Get author if available
                author = await self.page.evaluate("""() => {
                    const author = document.querySelector('[rel="author"], .author, [class*="author"], [itemprop="author"]');
                    if (author) {
                        return author.innerText || author.getAttribute('content');
                    }
                    const metaAuthor = document.querySelector('meta[name="author"], meta[property="article:author"]');
                    return metaAuthor ? metaAuthor.content : "";
                }""")
                
                # Extract key points (first few paragraphs or bullet points)
                key_points = await self.page.evaluate("""() => {
                    const article = document.querySelector('article, .article-body, .post-content');
                    if (article) {
                        const points = Array.from(article.querySelectorAll('p, li')).map(el => el.innerText)
                            .filter(t => t.trim() && t.length > 30 && t.length < 500)
                            .slice(0, 5);
                        return points;
                    }
                    return [];
                }""")
                
            except Exception as e:
                logger.warning(f"Error extracting detailed page content: {e}")
                body_text = ""
                meta_desc = ""
                headings = {}
                article_content = ""
                pub_date = ""
                author = ""
                key_points = []
            
            # Analyze for errors or issues
            issues = []
            try:
                # Check for common error indicators
                error_indicators = ['error', '404', 'not found', 'page not found', 'access denied']
                if any(indicator in body_text.lower() for indicator in error_indicators):
                    issues.append("Possible error detected on page")
            except:
                pass
            
            # Extract summary using LLM if available
            summary = ""
            if self.llm_service and body_text:
                try:
                    summary_prompt = f"""Summarize the key information from this page content in 2-3 sentences:

Title: {title}
Content: {body_text[:1000]}

Provide a concise summary of the main points."""
                    summary = self.llm_service.generate_content(summary_prompt)
                    summary = summary.strip()[:300]  # Limit summary length
                except Exception as e:
                    logger.debug(f"Could not generate summary: {e}")
            
            return TaskResult(
                success=True,
                message=f"Successfully read page: {title}",
                data={
                    "title": title,
                    "url": current_url,
                    "content_preview": body_text[:1000] if body_text else "",
                    "article_content": article_content[:2000] if article_content else "",
                    "meta_description": meta_desc,
                    "headings": headings,
                    "publication_date": pub_date,
                    "author": author,
                    "key_points": key_points if isinstance(key_points, list) else [],
                    "summary": summary,
                    "content_length": len(body_text) if body_text else 0,
                    "issues": issues
                }
            )
        except Exception as e:
            logger.error(f"Error reading page: {e}", exc_info=True)
            return TaskResult(
                success=False,
                message="Failed to read page",
                error=str(e),
                data={"url": url or "current page"}
            )
    
    async def EXTRACT_DETAILED_RESULTS(self, results: List[Dict], max_results: int = 3) -> TaskResult:
        """
        Extract detailed information from top search results by visiting each page.
        
        Args:
            results: List of result dictionaries with title and url
            max_results: Maximum number of results to visit in detail
            
        Returns:
            TaskResult with detailed extraction from top results
        """
        try:
            if not results:
                return TaskResult(
                    success=False,
                    message="No results to extract",
                    error="No results provided",
                    data={"results": []}
                )
            
            detailed_results = []
            visited_urls = []
            
            # Visit top results and extract detailed information
            for i, result in enumerate(results[:max_results]):
                try:
                    url = result.get("url", "")
                    title = result.get("title", "")
                    
                    if not url or url in visited_urls:
                        continue
                    
                    # Normalize and validate URL
                    if url.startswith('//'):
                        url = 'https:' + url
                    elif url.startswith('/'):
                        # Relative URL - skip or try to construct absolute
                        logger.warning(f"Skipping relative URL: {url}")
                        continue
                    elif not url.startswith('http'):
                        logger.warning(f"Skipping invalid URL: {url}")
                        continue
                    
                    # Skip DuckDuckGo redirect URLs that aren't resolved
                    if 'duckduckgo.com' in url and '/l/?uddg=' not in url and '?q=' in url:
                        # This is a DuckDuckGo search page, not a result URL
                        logger.warning(f"Skipping DuckDuckGo search page: {url}")
                        continue
                    
                    logger.info(f"Extracting details from result {i+1}/{min(len(results), max_results)}: {title}")
                    logger.debug(f"URL: {url}")
                    
                    # Open URL in new tab to avoid navigation issues
                    detail_page = None
                    try:
                        if self.context:
                            detail_page = await self.context.new_page()
                            try:
                                await detail_page.goto(url, wait_until='domcontentloaded', timeout=20000)
                                await asyncio.sleep(2)  # Wait for page to load
                            except Exception as nav_error:
                                logger.warning(f"Navigation error for {url}: {nav_error}")
                                if detail_page:
                                    await detail_page.close()
                                detailed_results.append({
                                    "title": title,
                                    "url": url,
                                    "snippet": result.get("snippet", ""),
                                    "error": f"Navigation failed: {str(nav_error)}",
                                    "extracted": False
                                })
                                continue
                            
                            # Check for CAPTCHA
                            captcha_found = False
                            try:
                                # Quick CAPTCHA check
                                captcha_selectors = ['iframe[src*="recaptcha"]', 'iframe[src*="hcaptcha"]', '.g-recaptcha']
                                for selector in captcha_selectors:
                                    elem = await detail_page.query_selector(selector)
                                    if elem:
                                        captcha_found = True
                                        break
                            except:
                                pass
                            
                            if captcha_found:
                                logger.warning(f"CAPTCHA detected on {url}, skipping detailed extraction")
                                if detail_page:
                                    await detail_page.close()
                                detailed_results.append({
                                    "title": title,
                                    "url": url,
                                    "snippet": result.get("snippet", ""),
                                    "error": "CAPTCHA_DETECTED",
                                    "extracted": False
                                })
                                continue
                            
                            # Extract detailed content
                            page_data = await detail_page.evaluate("""() => {
                                const data = {};
                                
                                // Title
                                data.title = document.title;
                                
                                // Main content
                                const main = document.querySelector('main, article, .content, .post, .article, [role="main"]');
                                data.content = main ? main.innerText : document.body.innerText;
                                
                                // Article content
                                const article = document.querySelector('article, .article-body, .post-content, .entry-content');
                                if (article) {
                                    const paragraphs = Array.from(article.querySelectorAll('p')).map(p => p.innerText).filter(t => t.trim() && t.length > 20);
                                    data.article_paragraphs = paragraphs.slice(0, 10);
                                }
                                
                                // Meta description
                                const meta = document.querySelector('meta[name="description"], meta[property="og:description"]');
                                data.meta_description = meta ? meta.content : "";
                                
                                // Publication date
                                const time = document.querySelector('time[datetime], [class*="date"], [class*="published"]');
                                data.pub_date = time ? (time.getAttribute('datetime') || time.innerText) : "";
                                
                                // Author
                                const author = document.querySelector('[rel="author"], .author, [class*="author"]');
                                data.author = author ? author.innerText : "";
                                
                                // Headings
                                data.headings = {
                                    h1: Array.from(document.querySelectorAll("h1")).map(h => h.innerText).filter(t => t.trim()).slice(0, 3),
                                    h2: Array.from(document.querySelectorAll("h2")).map(h => h.innerText).filter(t => t.trim()).slice(0, 5)
                                };
                                
                                return data;
                            }""")
                            
                            if detail_page:
                                await detail_page.close()
                            
                            # Create summary using LLM if available
                            summary = ""
                            if self.llm_service and page_data.get("content"):
                                try:
                                    content_preview = page_data.get("content", "")[:1500]
                                    summary_prompt = f"""Summarize this news article in 2-3 sentences highlighting the key points:

Title: {page_data.get('title', title)}
Content: {content_preview}

Provide a concise summary."""
                                    summary = self.llm_service.generate_content(summary_prompt)
                                    summary = summary.strip()[:300]
                                except Exception as e:
                                    logger.debug(f"Could not generate summary for {url}: {e}")
                            
                            detailed_results.append({
                                "title": page_data.get("title", title),
                                "url": url,
                                "snippet": result.get("snippet", ""),
                                "meta_description": page_data.get("meta_description", ""),
                                "content_preview": page_data.get("content", "")[:500],
                                "article_paragraphs": page_data.get("article_paragraphs", []),
                                "publication_date": page_data.get("pub_date", ""),
                                "author": page_data.get("author", ""),
                                "headings": page_data.get("headings", {}),
                                "summary": summary,
                                "extracted": True
                            })
                            
                            visited_urls.append(url)
                            logger.info(f"Successfully extracted details from: {title}")
                            
                    except Exception as e:
                        logger.warning(f"Error extracting details from {url}: {e}")
                        if detail_page:
                            try:
                                await detail_page.close()
                            except:
                                pass
                        detailed_results.append({
                            "title": title,
                            "url": url,
                            "snippet": result.get("snippet", ""),
                            "error": str(e),
                            "extracted": False
                        })
                    
                    # Small delay between requests
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error processing result {i+1}: {e}")
                    continue
            
            return TaskResult(
                success=True,
                message=f"Extracted detailed information from {len(detailed_results)} results",
                data={
                    "detailed_results": detailed_results,
                    "count": len(detailed_results),
                    "successfully_extracted": sum(1 for r in detailed_results if r.get("extracted", False))
                }
            )
        except Exception as e:
            logger.error(f"Error extracting detailed results: {e}", exc_info=True)
            return TaskResult(
                success=False,
                message="Failed to extract detailed results",
                error=str(e),
                data={"results": results}
            )
    
    async def FIX_ISSUE(self, issue_description: str) -> TaskResult:
        """
        Attempt to fix an issue or provide a solution.
        
        Args:
            issue_description: Description of the issue
            
        Returns:
            TaskResult with fix attempt or solution
        """
        try:
            await self.initialize_browser()
            
            # Use LLM to generate fix suggestions if available
            if self.llm_service:
                fix_prompt = f"""
                Issue: {issue_description}
                Current page: {self.page.url if self.page else "Not on a page"}
                
                Provide a solution or fix for this issue. Consider:
                1. What is the root cause?
                2. What steps can be taken to fix it?
                3. Are there alternative approaches?
                
                Respond with a clear solution.
                """
                solution = self.llm_service.generate_content(fix_prompt)
                
                return TaskResult(
                    success=True,
                    message="Issue analysis and solution provided",
                    data={
                        "issue": issue_description,
                        "solution": solution,
                        "url": self.page.url if self.page else None
                    }
                )
            else:
                # Basic fix suggestions without LLM
                return TaskResult(
                    success=True,
                    message="Issue noted, manual intervention may be required",
                    data={
                        "issue": issue_description,
                        "suggestion": "Review the issue and apply appropriate fixes",
                        "url": self.page.url if self.page else None
                    }
                )
        except Exception as e:
            logger.error(f"Error fixing issue: {e}")
            return TaskResult(
                success=False,
                message="Failed to generate fix",
                error=str(e),
                data={"issue": issue_description}
            )
    
    def RECORD_STEP(self, step_description: str, result: TaskResult) -> Dict:
        """
        Record a step in the execution log.
        
        Args:
            step_description: Description of the step
            result: TaskResult from the step
            
        Returns:
            Recorded step dictionary
        """
        step_record = {
            "step": step_description,
            "success": result.success,
            "result": result.dict()
        }
        self.recorded_steps.append(step_record)
        return step_record
    
    async def run(self) -> TaskResult:
        """
        Execute the browser task with reasoning.
        Stops immediately if CAPTCHA is detected.
        
        Returns:
            TaskResult with execution details
        """
        try:
            # Step 1: Reason and decide on action
            plan = self.REASON_AND_DECIDE(self.task_query)
            self.RECORD_STEP(f"Reasoned about query: {self.task_query}", TaskResult(
                success=True,
                message=f"Decided to {plan.action}: {plan.target}",
                data={"plan": plan.dict()}
            ))
            
            # Step 2: Execute the planned action
            result = None
            if plan.action == "OPEN_URL":
                result = await self.OPEN_URL(plan.target)
                self.RECORD_STEP(f"Opened URL: {plan.target}", result)
                
                # Check if CAPTCHA was detected
                if result.error == "CAPTCHA_DETECTED":
                    logger.warning("CAPTCHA detected. Waiting for user to complete CAPTCHA...")
                    logger.info("Browser will remain open. Polling for CAPTCHA completion...")
                    
                    # Wait for user to complete CAPTCHA
                    captcha_resolved = await self.WAIT_FOR_CAPTCHA_COMPLETION(max_wait_seconds=300, check_interval=3)
                    
                    if captcha_resolved:
                        logger.info("CAPTCHA resolved! Continuing with page read...")
                        # Continue with reading the page
                        read_result = await self.READ_PAGE()
                        self.RECORD_STEP(f"Read page content from {plan.target} after CAPTCHA", read_result)
                        
                        # Check if CAPTCHA appeared again
                        if read_result.error == "CAPTCHA_DETECTED":
                            logger.warning("CAPTCHA detected again. Stopping.")
                            return read_result
                        
                        # Successfully read the page
                        return read_result
                    else:
                        logger.warning("CAPTCHA not resolved within timeout. Stopping automation.")
                        return result
                
                # After opening, read the page (only if no CAPTCHA)
                if not self.captcha_detected:
                    read_result = await self.READ_PAGE()
                    self.RECORD_STEP(f"Read page content from {plan.target}", read_result)
                    
                    # Check if CAPTCHA was detected during read
                    if read_result.error == "CAPTCHA_DETECTED":
                        logger.warning("CAPTCHA detected during page read. Waiting for user to complete CAPTCHA...")
                        
                        # Wait for CAPTCHA completion
                        captcha_resolved = await self.WAIT_FOR_CAPTCHA_COMPLETION(max_wait_seconds=300, check_interval=3)
                        
                        if captcha_resolved:
                            logger.info("CAPTCHA resolved! Continuing to read page...")
                            # Try reading again
                            read_result = await self.READ_PAGE()
                            if read_result.error != "CAPTCHA_DETECTED":
                                self.RECORD_STEP("Read page after CAPTCHA resolution", read_result)
                                return read_result
                        
                        logger.warning("CAPTCHA not resolved. Stopping automation.")
                        return read_result
                
            elif plan.action == "SEARCH_DUCKDUCKGO":
                # Step 1: Attempt primary search on DuckDuckGo (default search engine)
                result = await self.SEARCH_DUCKDUCKGO(plan.target)
                self.RECORD_STEP(f"Searched DuckDuckGo for: {plan.target}", result)
                
                # Step 2: Check if CAPTCHA was detected or search failed
                # NO GOOGLE FALLBACK - only use DuckDuckGo and other non-Google fallbacks
                if result.error == "CAPTCHA_DETECTED" or not result.success:
                    logger.warning("DuckDuckGo search failed or blocked. Trying alternative fallback strategies (excluding Google)...")
                    
                    # Get fallback strategies (NO GOOGLE)
                    fallbacks = await self.REASON_AND_CHOOSE_FALLBACK(plan.target)
                    logger.info(f"Trying {len(fallbacks)} fallback strategies (NO GOOGLE)...")
                    
                    # Try each fallback
                    fallback_success = False
                    old_page = None
                    new_tab = None
                    
                    for i, fallback in enumerate(fallbacks, 1):
                        logger.info(f"Fallback {i}/{len(fallbacks)}: {fallback.get('description')}")
                        
                        # Open new tab for fallback (if context allows)
                        try:
                            if self.context:
                                new_tab = await self.NEW_TAB()
                                if new_tab:
                                    # Switch to new tab
                                    old_page = self.page
                                    self.page = new_tab
                        except Exception as e:
                            logger.debug(f"Could not open new tab: {e}")
                            # Continue with current page if new tab fails
                        
                        # Execute fallback
                        fallback_result = await self.EXECUTE_FALLBACK_STRATEGY(fallback, plan.target)
                        self.RECORD_STEP(f"Fallback attempt {i}: {fallback.get('description')}", fallback_result)
                        
                        # Check if fallback succeeded
                        if fallback_result.success and fallback_result.error != "CAPTCHA_DETECTED":
                            logger.info(f"Fallback {i} succeeded! Extracting detailed information from results...")
                            
                            # Get results from fallback
                            results = fallback_result.data.get("results", [])
                            
                            if results:
                                # Extract detailed information from top results
                                detailed_extraction = await self.EXTRACT_DETAILED_RESULTS(results, max_results=3)
                                self.RECORD_STEP(f"Extract detailed information from fallback {i} results", detailed_extraction)
                                
                                if detailed_extraction.success:
                                    detailed_results = detailed_extraction.data.get("detailed_results", [])
                                    fallback_result.data["detailed_results"] = detailed_results
                                    fallback_result.data["extraction_summary"] = {
                                        "total_results": len(results),
                                        "detailed_extractions": len(detailed_results),
                                        "successfully_extracted": detailed_extraction.data.get("successfully_extracted", 0),
                                        "source": fallback.get('description', 'fallback')
                                    }
                                    
                                    # Create comprehensive summary using LLM if available
                                    if self.llm_service and detailed_results:
                                        try:
                                            summary_prompt = f"""Based on these search results about "{plan.target}", provide a comprehensive summary:

"""
                                            for i, dr in enumerate(detailed_results[:3], 1):
                                                if dr.get("extracted"):
                                                    summary_prompt += f"""
Result {i}:
Title: {dr.get('title', 'N/A')}
Summary: {dr.get('summary', dr.get('content_preview', 'N/A')[:200])}
URL: {dr.get('url', 'N/A')}

"""
                                            summary_prompt += """
Provide a comprehensive summary of the key information found, highlighting the main points and latest developments."""
                                            
                                            comprehensive_summary = self.llm_service.generate_content(summary_prompt)
                                            fallback_result.data["comprehensive_summary"] = comprehensive_summary.strip()
                                            logger.info("Generated comprehensive summary using LLM")
                                        except Exception as e:
                                            logger.warning(f"Could not generate comprehensive summary: {e}")
                            
                            fallback_success = True
                            
                            # Close new tab if we opened one
                            try:
                                if new_tab and self.page == new_tab and old_page:
                                    await new_tab.close()
                                    self.page = old_page
                            except:
                                pass
                            
                            # Return successful result with detailed extraction
                            return fallback_result
                        
                        # If fallback also hit CAPTCHA, continue to next fallback
                        if fallback_result.error == "CAPTCHA_DETECTED":
                            logger.warning(f"Fallback {i} also blocked by CAPTCHA. Trying next fallback...")
                            # Track all CAPTCHA URLs
                            if fallback_result.data.get("url"):
                                if not hasattr(self, 'captcha_urls'):
                                    self.captcha_urls = []
                                self.captcha_urls.append(fallback_result.data.get("url"))
                        
                        # Close new tab if we opened one before trying next fallback
                        try:
                            if new_tab and self.page == new_tab and old_page:
                                await new_tab.close()
                                self.page = old_page
                                new_tab = None
                        except:
                            pass
                    
                    # All fallbacks failed
                    if not fallback_success:
                        logger.warning("All fallback strategies failed or were blocked by CAPTCHAs")
                        
                        # Record all fallbacks blocked
                        all_blocked_result = TaskResult(
                            success=False,
                            message="All fallback strategies failed or were blocked by CAPTCHAs",
                            error="ALL_FALLBACKS_BLOCKED",
                            data={
                                "title": "Fallback Attempts Failed",
                                "url": self.captcha_url or "Multiple URLs",
                                "fallbacks_tried": len(fallbacks),
                                "original_query": plan.target
                            }
                        )
                        self.RECORD_STEP("ALL_FALLBACKS_BLOCKED", all_blocked_result)
                        
                        # Notify user
                        captcha_urls = []
                        if self.captcha_url:
                            captcha_urls.append(self.captcha_url)
                        if hasattr(self, 'captcha_urls'):
                            captcha_urls.extend(self.captcha_urls)
                        captcha_urls = list(set(captcha_urls))  # Remove duplicates
                        
                        notification = self.NOTIFY_USER_FOR_CAPTCHA(
                            "\n".join(captcha_urls) if captcha_urls else "Multiple search engines",
                            "All fallback searches blocked"
                        )
                        
                        return TaskResult(
                            success=False,
                            message=notification,
                            error="ALL_FALLBACKS_BLOCKED",
                            data={
                                "title": "All Fallbacks Blocked",
                                "url": captcha_urls[0] if captcha_urls else "Multiple URLs",
                                "fallbacks_tried": len(fallbacks),
                                "original_query": plan.target,
                                "captcha_urls": captcha_urls
                            }
                        )
                
                # Step 3: Process results and extract detailed information (only if no CAPTCHA)
                if not self.captcha_detected and result.success:
                    # Get results from the search
                    results = result.data.get("results", [])
                    
                    if results:
                        logger.info(f"Found {len(results)} search results. Extracting detailed information...")
                        
                        # Extract detailed information from top results
                        detailed_extraction = await self.EXTRACT_DETAILED_RESULTS(results, max_results=3)
                        self.RECORD_STEP("Extract detailed information from top results", detailed_extraction)
                        
                        if detailed_extraction.success:
                            detailed_results = detailed_extraction.data.get("detailed_results", [])
                            result.data["detailed_results"] = detailed_results
                            result.data["extraction_summary"] = {
                                "total_results": len(results),
                                "detailed_extractions": len(detailed_results),
                                "successfully_extracted": detailed_extraction.data.get("successfully_extracted", 0)
                            }
                            
                            # Create comprehensive summary using LLM if available
                            if self.llm_service and detailed_results:
                                try:
                                    summary_prompt = f"""Based on these search results about "{plan.target}", provide a comprehensive summary:

"""
                                    for i, dr in enumerate(detailed_results[:3], 1):
                                        if dr.get("extracted"):
                                            summary_prompt += f"""
Result {i}:
Title: {dr.get('title', 'N/A')}
Summary: {dr.get('summary', dr.get('content_preview', 'N/A')[:200])}
URL: {dr.get('url', 'N/A')}

"""
                                    summary_prompt += """
Provide a comprehensive summary of the key information found, highlighting the main points and latest developments."""
                                    
                                    comprehensive_summary = self.llm_service.generate_content(summary_prompt)
                                    result.data["comprehensive_summary"] = comprehensive_summary.strip()
                                    logger.info("Generated comprehensive summary using LLM")
                                except Exception as e:
                                    logger.warning(f"Could not generate comprehensive summary: {e}")
                            
                            logger.info(f"Successfully extracted detailed information from {len(detailed_results)} results")
                        else:
                            logger.warning("Detailed extraction failed, but basic results are available")
                            result.data["detailed_results"] = []
                            result.data["extraction_summary"] = {
                                "total_results": len(results),
                                "detailed_extractions": 0,
                                "error": detailed_extraction.error
                            }
                    else:
                        logger.warning("No search results found")
                        result.data["detailed_results"] = []
                        result.data["extraction_summary"] = {
                            "total_results": 0,
                            "detailed_extractions": 0
                        }
                    
                    return result
                
                # Return the original result if no fallbacks were needed
                return result
                
            elif plan.action == "READ_PAGE":
                result = await self.READ_PAGE(plan.target if plan.target else None)
                self.RECORD_STEP(f"Read page: {plan.target or 'current page'}", result)
                
                # Check if CAPTCHA was detected
                if result.error == "CAPTCHA_DETECTED":
                    logger.warning("CAPTCHA detected. Waiting for user to complete CAPTCHA...")
                    
                    # Wait for CAPTCHA completion
                    captcha_resolved = await self.WAIT_FOR_CAPTCHA_COMPLETION(max_wait_seconds=300, check_interval=3)
                    
                    if captcha_resolved:
                        logger.info("CAPTCHA resolved! Continuing to read page...")
                        # Try reading again
                        result = await self.READ_PAGE(plan.target if plan.target else None)
                        if result.error != "CAPTCHA_DETECTED":
                            self.RECORD_STEP(f"Read page after CAPTCHA resolution: {plan.target or 'current page'}", result)
                            return result
                    
                    logger.warning("CAPTCHA not resolved. Stopping automation.")
                    return result
                
            elif plan.action == "FIX_ISSUE":
                # Check for CAPTCHA before fixing
                if self.page:
                    captcha_found = await self.DETECT_CAPTCHA()
                    if captcha_found:
                        self.captcha_detected = True
                        self.captcha_url = self.page.url
                        title = await self.page.title()
                        notification = self.NOTIFY_USER_FOR_CAPTCHA(self.page.url, title)
                        
                        result = TaskResult(
                            success=False,
                            message=notification,
                            error="CAPTCHA_DETECTED",
                            data={
                                "title": title,
                                "url": self.page.url,
                                "captcha_detected": True
                            }
                        )
                        self.RECORD_STEP(f"CAPTCHA detected while fixing issue", result)
                        logger.warning("CAPTCHA detected. Browser will remain open for user to complete CAPTCHA.")
                        return result
                
                result = await self.FIX_ISSUE(plan.target)
                self.RECORD_STEP(f"Attempted to fix: {plan.target}", result)
            
            # Return the final result
            if result:
                return result
            else:
                return TaskResult(
                    success=False,
                    message="No action was executed",
                    error="Unknown action type"
                )
                
        except Exception as e:
            logger.error(f"Error executing browser task: {e}", exc_info=True)
            return TaskResult(
                success=False,
                message=f"Failed to execute task: {self.task_query}",
                error=str(e)
            )
    
    def get_recorded_steps(self) -> List[Dict]:
        """Get all recorded steps."""
        return self.recorded_steps
    
    async def cleanup(self, force_close: bool = False):
        """
        Clean up browser resources.
        
        Args:
            force_close: If True, closes browser immediately. 
                        If False and CAPTCHA detected, keeps browser open for user to complete CAPTCHA.
        """
        try:
            # If CAPTCHA is detected and force_close is False, keep browser open
            if self.captcha_detected and not force_close:
                logger.info(f"CAPTCHA detected. Keeping browser open at {self.captcha_url} for user to complete CAPTCHA.")
                logger.info("Browser will remain open. User can complete CAPTCHA manually.")
                # Don't close the browser - let user see and complete CAPTCHA
                return
            
            # Normal cleanup - close everything
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("Browser resources cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def cleanup_after_captcha(self, delay_seconds: int = 300):
        """
        Cleanup browser after CAPTCHA completion or timeout.
        Keeps browser open for specified duration to allow user to complete CAPTCHA.
        
        Args:
            delay_seconds: Number of seconds to keep browser open (default: 5 minutes)
        """
        try:
            if self.captcha_detected:
                logger.info(f"Waiting {delay_seconds} seconds for user to complete CAPTCHA before cleanup...")
                await asyncio.sleep(delay_seconds)
                logger.info("Cleaning up browser after CAPTCHA wait period")
                await self.cleanup(force_close=True)
        except Exception as e:
            logger.error(f"Error during CAPTCHA cleanup: {e}")
