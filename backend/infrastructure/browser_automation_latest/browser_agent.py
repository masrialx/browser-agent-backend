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

CRITICAL RULE: Always use DuckDuckGo as the ONLY search engine for fallbacks. Never suggest Google, Bing, or blog search engines.

Given a user query, suggest appropriate fallback strategies:
1. Retry DuckDuckGo search (primary fallback)
2. Site-specific searches on relevant authoritative sources (only if website is explicitly mentioned)
3. Cached version searches (if available)

Return a list of fallback strategies with:
- type: "search_engine" | "site_search" | "cache"
- engine: "duckduckgo" ONLY (if type is search_engine) - NEVER "bing" or "google"
- site: domain name like "bbc.com" (if type is site_search and site is mentioned in query)
- query: the search query to use
- description: human-readable description

Fallback priority:
1. Retry DuckDuckGo search first
2. Only suggest site-specific searches if the website was explicitly mentioned in the original query
3. Do NOT suggest Google, Bing, or blog searches

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
                            
                            # Validate engine for search_engine type - ONLY DuckDuckGo allowed
                            if fb_type == "search_engine":
                                engine = fallback_dict.get("engine", "").lower()
                                if engine not in ["duckduckgo"]:
                                    logger.warning(f"Invalid engine: {engine}, defaulting to duckduckgo (DuckDuckGo is the only allowed search engine)")
                                    fallback_dict["engine"] = "duckduckgo"
                            
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
        
        # Default fallback strategies (DuckDuckGo only)
        fallbacks = []
        query_lower = query.lower()
        
        # Retry DuckDuckGo search (primary fallback)
        fallbacks.append({
            "type": "search_engine",
            "engine": "duckduckgo",
            "query": query,
            "description": f"Retry DuckDuckGo search for {query}"
        })
        
        # Only add site-specific searches if the site was explicitly mentioned in the query
        # For news queries, only if news sites are mentioned
        mentioned_sites = []
        news_sites = ['bbc', 'techcrunch', 'theverge', 'reuters', 'cnn']
        for site in news_sites:
            if site in query_lower:
                mentioned_sites.append(f"{site}.com")
        
        # For technical queries, only if tech sites are mentioned
        tech_sites_keywords = {
            'medium': 'medium.com',
            'dev.to': 'dev.to',
            'stackoverflow': 'stackoverflow.com',
            'github': 'github.com'
        }
        for keyword, site in tech_sites_keywords.items():
            if keyword in query_lower:
                mentioned_sites.append(site)
        
        # Add site-specific searches only for mentioned sites
        for site in mentioned_sites:
            fallbacks.append({
                "type": "site_search",
                "site": site,
                "query": query,
                "description": f"Search {site} for {query}"
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
                
                if engine == "bing":
                    result = await self.SEARCH_BING(query)
                    if result.success:
                        read_result = await self.READ_TOP_RESULTS(limit=5)
                        if read_result.success:
                            result.data["top_results"] = read_result.data.get("results", [])
                            # Extract detailed content from top 2 results
                            detailed_results = []
                            for i, res in enumerate(read_result.data.get("results", [])[:2]):
                                if res.get("url"):
                                    detail_result = await self.EXTRACT_DETAILED_CONTENT(res["url"])
                                    if detail_result.success:
                                        detailed_results.append(detail_result.data)
                            result.data["detailed_results"] = detailed_results
                    return result
                elif engine == "duckduckgo":
                    result = await self.SEARCH_DUCKDUCKGO(query)
                    if result.success:
                        read_result = await self.READ_TOP_RESULTS(limit=5)
                        if read_result.success:
                            result.data["top_results"] = read_result.data.get("results", [])
                            # Extract detailed content from top 2 results
                            detailed_results = []
                            for i, res in enumerate(read_result.data.get("results", [])[:2]):
                                if res.get("url") and res["url"].startswith("http"):
                                    detail_result = await self.EXTRACT_DETAILED_CONTENT(res["url"])
                                    if detail_result.success:
                                        detailed_results.append(detail_result.data)
                            result.data["detailed_results"] = detailed_results
                    return result
                    
            elif fallback_type == "site_search":
                site = fallback.get("site")
                query = fallback.get("query", original_query)
                result = await self.SITE_SPECIFIC_SEARCH(site, query)
                if result.success:
                    read_result = await self.READ_TOP_RESULTS(limit=5)
                    if read_result.success:
                        result.data["top_results"] = read_result.data.get("results", [])
                        # Extract detailed content from top 2 results
                        detailed_results = []
                        for i, res in enumerate(read_result.data.get("results", [])[:2]):
                            if res.get("url") and res["url"].startswith("http"):
                                detail_result = await self.EXTRACT_DETAILED_CONTENT(res["url"])
                                if detail_result.success:
                                    detailed_results.append(detail_result.data)
                        result.data["detailed_results"] = detailed_results
                return result
                
            elif fallback_type == "cache":
                query = fallback.get("query", original_query)
                result = await self.USE_CACHE_OPERATOR(query)
                if result.success:
                    read_result = await self.READ_TOP_RESULTS(limit=5)
                    if read_result.success:
                        result.data["top_results"] = read_result.data.get("results", [])
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
    
    def _correct_website_typos(self, query: str) -> str:
        """
        Correct common typos in website names.
        
        Args:
            query: User query
            
        Returns:
            Query with corrected website names
        """
        typo_corrections = {
            # Wikipedia typos
            'wikipida': 'wikipedia',
            'wikipeda': 'wikipedia',
            'wikipidia': 'wikipedia',
            'wikepedia': 'wikipedia',
            'wikpedia': 'wikipedia',
            'wkipedia': 'wikipedia',
            # Command word typos
            'vist': 'visit',
            'visti': 'visit',
            'vistit': 'visit',
            # Other website typos
            'linkedn': 'linkedin',
            'linkdin': 'linkedin',
            'youtue': 'youtube',
            'youtub': 'youtube',
            'facebok': 'facebook',
            'faceboook': 'facebook',
            'redit': 'reddit',
            'redditt': 'reddit',
            'twiter': 'twitter',
            'twittr': 'twitter',
            'instgram': 'instagram',
            'instagrm': 'instagram',
            'githu': 'github',
            'githb': 'github',
            'stackoverflw': 'stackoverflow',
            'stackoverfow': 'stackoverflow',
        }
        
        corrected_query = query.lower()
        for typo, correct in typo_corrections.items():
            if typo in corrected_query:
                corrected_query = corrected_query.replace(typo, correct)
                logger.info(f"Corrected typo '{typo}' to '{correct}' in query")
        
        # Preserve original case for non-typo parts
        words = query.split()
        corrected_words = corrected_query.split()
        if len(words) == len(corrected_words):
            result = []
            for orig, corr in zip(words, corrected_words):
                if orig.lower() != corr:
                    result.append(corr)
                else:
                    result.append(orig)
            return ' '.join(result)
        
        return corrected_query
    
    async def _extract_wikipedia_search_results(self, search_terms: str) -> List[Dict]:
        """
        Extract Wikipedia search results and get detailed content from Wikipedia articles.
        
        Args:
            search_terms: Search terms used
            
        Returns:
            List of detailed results from Wikipedia articles
        """
        detailed_results = []
        try:
            # Wait for search results to load
            await asyncio.sleep(2)
            
            # Extract Wikipedia search result links
            result_links = []
            try:
                # Wikipedia search results are in <ul class="mw-search-results"> with <li> items containing <a> tags
                result_items = await self.page.query_selector_all('.mw-search-results li, .searchresults li, .search-result')
                
                for item in result_items[:5]:  # Get top 5 results
                    try:
                        # Find the main article link
                        link_elem = await item.query_selector('a[href*="/wiki/"]')
                        if link_elem:
                            href = await link_elem.get_attribute('href')
                            title = await link_elem.inner_text()
                            title = title.strip()
                            
                            # Construct full URL if relative
                            if href and href.startswith('/wiki/'):
                                href = 'https://en.wikipedia.org' + href
                            
                            if href and title and 'Special:' not in href:
                                result_links.append({
                                    "title": title,
                                    "url": href
                                })
                    except Exception as e:
                        logger.debug(f"Error extracting Wikipedia result link: {e}")
                        continue
                
                # If no results found with the above selector, try alternative
                if not result_links:
                    # Try finding links in search results
                    all_links = await self.page.query_selector_all('a[href*="/wiki/"]')
                    for link in all_links[:10]:
                        try:
                            href = await link.get_attribute('href')
                            title = await link.inner_text()
                            title = title.strip()
                            
                            # Skip navigation and special pages
                            if href and ('Special:' in href or 'Category:' in href or 'Help:' in href or 'Template:' in href):
                                continue
                            
                            # Construct full URL if relative
                            if href and href.startswith('/wiki/'):
                                href = 'https://en.wikipedia.org' + href
                            
                            if href and title and href not in [r["url"] for r in result_links]:
                                result_links.append({
                                    "title": title,
                                    "url": href
                                })
                                if len(result_links) >= 5:
                                    break
                        except:
                            continue
            except Exception as e:
                logger.warning(f"Error extracting Wikipedia search result links: {e}")
            
            # Extract detailed content from each Wikipedia article
            logger.info(f"Found {len(result_links)} Wikipedia articles. Extracting detailed content...")
            for i, result_link in enumerate(result_links[:3]):  # Extract from top 3 articles
                try:
                    logger.info(f"Extracting content from article {i+1}/{min(3, len(result_links))}: {result_link['title']}")
                    
                    # Navigate to the Wikipedia article
                    article_url = result_link['url']
                    await self.page.goto(article_url, wait_until='domcontentloaded', timeout=30000)
                    await asyncio.sleep(2)  # Wait for page to load
                    
                    # Check for CAPTCHA
                    captcha_found = await self.DETECT_CAPTCHA()
                    if captcha_found:
                        logger.warning(f"CAPTCHA detected on {article_url}, skipping")
                        continue
                    
                    # Extract detailed content using EXTRACT_DETAILED_CONTENT
                    detail_result = await self.EXTRACT_DETAILED_CONTENT(article_url, max_content_length=3000)
                    
                    if detail_result.success:
                        # Enhance the result with Wikipedia-specific information
                        article_data = detail_result.data.copy()
                        
                        # Try to extract Wikipedia infobox data
                        try:
                            infobox = await self.page.evaluate("""() => {
                                const infobox = document.querySelector('.infobox, .infobox_v2');
                                if (!infobox) return null;
                                const rows = Array.from(infobox.querySelectorAll('tr'));
                                const data = {};
                                rows.forEach(row => {
                                    const header = row.querySelector('th');
                                    const value = row.querySelector('td');
                                    if (header && value) {
                                        data[header.innerText.trim()] = value.innerText.trim();
                                    }
                                });
                                return data;
                            }""")
                            if infobox:
                                article_data["infobox"] = infobox
                        except:
                            pass
                        
                        # Try to extract Wikipedia table of contents
                        try:
                            toc = await self.page.evaluate("""() => {
                                const toc = document.querySelector('#toc');
                                if (!toc) return [];
                                const links = Array.from(toc.querySelectorAll('a'));
                                return links.map(link => link.innerText.trim()).filter(t => t);
                            }""")
                            if toc:
                                article_data["table_of_contents"] = toc
                        except:
                            pass
                        
                        detailed_results.append(article_data)
                        logger.info(f"Successfully extracted content from: {result_link['title']}")
                    else:
                        logger.warning(f"Failed to extract content from {result_link['title']}: {detail_result.message}")
                except Exception as e:
                    logger.error(f"Error extracting content from Wikipedia article {i+1}: {e}")
                    continue
            
            # Navigate back to search results page if we have results
            if detailed_results and result_links:
                try:
                    # Go back to search results
                    await self.page.go_back()
                    await asyncio.sleep(1)
                except:
                    pass
            
            return detailed_results
        except Exception as e:
            logger.error(f"Error extracting Wikipedia search results: {e}")
            return detailed_results
    
    def REASON_AND_DECIDE(self, query: str) -> ActionPlan:
        """
        Use LLM-based reasoning to decide the best action for the query.
        
        Args:
            query: User query
            
        Returns:
            ActionPlan with recommended action
        """
        # First, correct any typos in website names
        corrected_query = self._correct_website_typos(query)
        if corrected_query.lower() != query.lower():
            logger.info(f"Original query: '{query}', Corrected query: '{corrected_query}'")
            query = corrected_query
        
        if self.llm_service:
            try:
                # Use LLM with structured schema for reliable parsing
                from pydantic import BaseModel
                
                class ActionPlanSchema(BaseModel):
                    action: str  # OPEN_URL, SEARCH_DUCKDUCKGO, READ_PAGE, FIX_ISSUE
                    target: str  # URL or search query
                    reason: str
                    expected_outcome: str
                
                system_instruction = """You are an AI assistant that analyzes user queries and determines the best browser automation action.

CRITICAL RULES:
1. DEFAULT SEARCH ENGINE: Always use DuckDuckGo (SEARCH_DUCKDUCKGO) as the default search engine. NEVER use Google or Bing unless explicitly requested.
2. DIRECT SITE VISIT: If the query mentions a website by name or domain, ALWAYS use OPEN_URL to navigate directly to that website. DO NOT search for it.
3. SEARCH INTENT: Only use search engines when NO specific website is mentioned.

Analyze the user query and determine:
1. Does the query contain a website domain name or URL? (e.g., "wikipedia", "linkedin", "youtube", "github.com", "open facebook", "visit reddit")
   - If a website is mentioned: use OPEN_URL to navigate DIRECTLY to that website
   - Common websites: wikipedia, linkedin, facebook, youtube, github, reddit, twitter, instagram, stackoverflow, etc.
2. What is the user's intent? 
   - If website/domain mentioned: user wants to OPEN_URL to that website (e.g., "go to LinkedIn" -> OPEN_URL("https://www.linkedin.com"))
   - If website mentioned WITH search query (e.g., "find X on wikipedia"): OPEN_URL to website first, then search within that website
   - If NO website mentioned: user wants to SEARCH_DUCKDUCKGO for information (NOT Google or Bing)
3. What action should be taken? Choose one of: OPEN_URL, SEARCH_DUCKDUCKGO, READ_PAGE, FIX_ISSUE
4. If OPEN_URL: construct the full URL from the domain name
   - Examples: "linkedin" -> "https://www.linkedin.com", "youtube" -> "https://www.youtube.com"
5. If SEARCH_DUCKDUCKGO: extract search terms (remove command words like "search", "find", "look for")

EXAMPLES:
- "Go to LinkedIn" -> OPEN_URL("https://www.linkedin.com")
- "Visit Facebook" -> OPEN_URL("https://www.facebook.com")
- "Open YouTube" -> OPEN_URL("https://www.youtube.com")
- "Go to github.com" -> OPEN_URL("https://www.github.com")
- "visit wikipedia and find about X" -> OPEN_URL("https://www.wikipedia.org") (then search within Wikipedia)
- "vist wikipida and find about X" -> OPEN_URL("https://www.wikipedia.org") (typos are automatically corrected)
- "find about Ethiopian and sumz on wikipedia" -> OPEN_URL("https://www.wikipedia.org")
- "search latest news about AI" (no website) -> SEARCH_DUCKDUCKGO("latest news about AI")
- "find latest OpenAI updates" (no website) -> SEARCH_DUCKDUCKGO("latest OpenAI updates")

Website domain mapping:
- linkedin / linkedin.com -> https://www.linkedin.com
- facebook / facebook.com -> https://www.facebook.com
- youtube / youtube.com -> https://www.youtube.com
- github / github.com -> https://www.github.com
- wikipedia / wikipedia.org -> https://www.wikipedia.org
- reddit / reddit.com -> https://www.reddit.com
- twitter / twitter.com -> https://www.twitter.com
- instagram / instagram.com -> https://www.instagram.com
- stackoverflow / stackoverflow.com -> https://www.stackoverflow.com

Return your analysis as JSON with: action, target (URL or search query), reason, expected_outcome"""
                
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
                        # Validate action is one of the allowed values
                        allowed_actions = ["OPEN_URL", "SEARCH_GOOGLE", "SEARCH_DUCKDUCKGO", "READ_PAGE", "FIX_ISSUE"]
                        if response.action not in allowed_actions:
                            logger.warning(f"Invalid action from LLM: {response.action}, defaulting to SEARCH_DUCKDUCKGO")
                            response.action = "SEARCH_DUCKDUCKGO"
                        
                        # Map SEARCH_GOOGLE to SEARCH_DUCKDUCKGO (DuckDuckGo is default)
                        if response.action == "SEARCH_GOOGLE":
                            logger.info("Mapping SEARCH_GOOGLE to SEARCH_DUCKDUCKGO (DuckDuckGo is default search engine)")
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
        
        # Fallback logic without LLM (enhanced domain detection with typo tolerance)
        query_lower = query.lower()
        
        # Common website domains to detect (with common typos)
        website_domains = {
            'linkedin': 'https://www.linkedin.com',
            'linkdin': 'https://www.linkedin.com',
            'linkedn': 'https://www.linkedin.com',
            'facebook': 'https://www.facebook.com',
            'facebok': 'https://www.facebook.com',
            'youtube': 'https://www.youtube.com',
            'youtue': 'https://www.youtube.com',
            'youtub': 'https://www.youtube.com',
            'github': 'https://www.github.com',
            'githu': 'https://www.github.com',
            'githb': 'https://www.github.com',
            'wikipedia': 'https://www.wikipedia.org',
            'wikipida': 'https://www.wikipedia.org',
            'wikipeda': 'https://www.wikipedia.org',
            'wikipidia': 'https://www.wikipedia.org',
            'wikepedia': 'https://www.wikipedia.org',
            'wikpedia': 'https://www.wikipedia.org',
            'wkipedia': 'https://www.wikipedia.org',
            'reddit': 'https://www.reddit.com',
            'redit': 'https://www.reddit.com',
            'redditt': 'https://www.reddit.com',
            'twitter': 'https://www.twitter.com',
            'twiter': 'https://www.twitter.com',
            'twittr': 'https://www.twitter.com',
            'instagram': 'https://www.instagram.com',
            'instgram': 'https://www.instagram.com',
            'instagrm': 'https://www.instagram.com',
            'stackoverflow': 'https://www.stackoverflow.com',
            'stackoverflw': 'https://www.stackoverflow.com',
            'stackoverfow': 'https://www.stackoverflow.com',
            'medium': 'https://www.medium.com',
            'dev.to': 'https://www.dev.to',
            'techcrunch': 'https://www.techcrunch.com',
            'bbc': 'https://www.bbc.com',
            'cnn': 'https://www.cnn.com',
            'reuters': 'https://www.reuters.com',
            'theverge': 'https://www.theverge.com',
            'arstechnica': 'https://www.arstechnica.com',
        }
        
        # Check if query mentions a website domain (with typo tolerance)
        for domain, url in website_domains.items():
            if domain in query_lower:
                # Check for context words that indicate navigation intent
                nav_keywords = ['on ', 'from ', 'visit', 'open', 'go to', 'navigate to', 'check', 'read', 'find on', 'search on', 'go', 'visit', 'vist']
                # Also check if domain appears as a word (handles "visit wikipedia", "wikipedia page", etc.)
                if any(keyword + domain in query_lower or domain + ' ' in query_lower or ' ' + domain in query_lower for keyword in nav_keywords) or domain in query_lower.split():
                    logger.info(f"Website domain '{domain}' detected in query. Navigating directly to {url}")
                    return ActionPlan(
                        action="OPEN_URL",
                        target=url,
                        reason=f"Website domain '{domain}' detected in query - navigating directly to website",
                        expected_outcome=f"Navigate to {domain} website"
                    )
        
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
        
        # Default: search DuckDuckGo (NOT Google)
        return ActionPlan(
            action="SEARCH_DUCKDUCKGO",
            target=query,
            reason="No specific URL or website domain provided, using DuckDuckGo search (default search engine)",
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
            await asyncio.sleep(3)  # Wait for page to fully load (increased delay for stability)
            # Wait for network to be idle to ensure page is fully loaded
            try:
                await self.page.wait_for_load_state('networkidle', timeout=10000)
            except:
                pass
            await asyncio.sleep(1)  # Additional delay for stability
            
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
            
            # Navigate to Bing
            await self.page.goto("https://www.bing.com", wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(1)
            
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
            
            # Find search box
            search_selectors = ['input[name="q"]', 'input[type="search"]', '#sb_form_q']
            search_box = None
            for selector in search_selectors:
                try:
                    search_box = await self.page.query_selector(selector)
                    if search_box:
                        break
                except:
                    continue
            
            if not search_box:
                return TaskResult(
                    success=False,
                    message="Could not find Bing search box",
                    error="Search box element not found",
                    data={"query": query, "search_engine": "bing"}
                )
            
            # Type search query
            await search_box.fill(query)
            await asyncio.sleep(0.5)
            await search_box.press("Enter")
            await self.page.wait_for_load_state('networkidle', timeout=10000)
            await asyncio.sleep(2)
            
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
            
            # Extract search results
            results = []
            try:
                result_elements = await self.page.query_selector_all('h2 a, .b_title a')
                for i, elem in enumerate(result_elements[:5]):
                    try:
                        text = await elem.inner_text()
                        link = await elem.get_attribute('href')
                        results.append({"title": text, "url": link})
                    except:
                        continue
            except:
                pass
            
            return TaskResult(
                success=True,
                message=f"Successfully searched Bing for: {query}",
                data={
                    "title": title,
                    "url": current_url,
                    "query": query,
                    "results": results,
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
            
            # Navigate to DuckDuckGo
            await self.page.goto("https://www.duckduckgo.com", wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(1)
            
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
            
            # Find search box
            search_selectors = ['input[name="q"]', 'input[type="search"]', '#search_form_input_homepage']
            search_box = None
            for selector in search_selectors:
                try:
                    search_box = await self.page.query_selector(selector)
                    if search_box:
                        break
                except:
                    continue
            
            if not search_box:
                return TaskResult(
                    success=False,
                    message="Could not find DuckDuckGo search box",
                    error="Search box element not found",
                    data={"query": query, "search_engine": "duckduckgo"}
                )
            
            # Type search query
            await search_box.fill(query)
            await asyncio.sleep(0.5)
            await search_box.press("Enter")
            # Wait for navigation to start
            await asyncio.sleep(1)
            # Wait for page load (use domcontentloaded instead of networkidle for better reliability)
            try:
                await self.page.wait_for_load_state('domcontentloaded', timeout=15000)
            except Exception as e:
                logger.warning(f"Timeout waiting for domcontentloaded: {e}")
            await asyncio.sleep(2)  # Additional wait for content to render
            
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
            
            # Extract search results with snippets
            results = []
            try:
                # DuckDuckGo uses article[data-testid="result"]
                result_elements = await self.page.query_selector_all('article[data-testid="result"], .result, .web-result')
                for i, elem in enumerate(result_elements[:5]):
                    try:
                        # Get title and link
                        title_elem = await elem.query_selector('h2 a[data-testid="result-title-a"], h2 a, a[data-testid="result-title-a"]')
                        if title_elem:
                            text = await title_elem.inner_text()
                            text = text.strip()
                            link = await title_elem.get_attribute('href')
                            
                            # Handle DuckDuckGo redirect URLs (/l/?kh=-1&uddg=...)
                            if link and link.startswith('/l/'):
                                # Extract the actual URL from the redirect
                                try:
                                    # Get the data-uddg attribute or extract from href
                                    if 'uddg=' in link:
                                        actual_url = link.split('uddg=')[1].split('&')[0]
                                        link = actual_url
                                except:
                                    pass
                            
                            # Handle relative URLs
                            if link and not link.startswith('http'):
                                if link.startswith('/'):
                                    base_url = "https://" + current_url.split('/')[2] if len(current_url.split('/')) > 2 else "https://duckduckgo.com"
                                    link = base_url + link
                                else:
                                    link = "https://" + link
                            
                            # Get snippet
                            snippet = ""
                            try:
                                snippet_elem = await elem.query_selector('span[data-testid="result-snippet"], .result__snippet, .snippet')
                                if snippet_elem:
                                    snippet = await snippet_elem.inner_text()
                                    snippet = snippet.strip()[:200]
                            except:
                                pass
                            
                            if text and link:
                                results.append({
                                    "title": text,
                                    "url": link,
                                    "snippet": snippet,
                                    "rank": i + 1
                                })
                    except Exception as e:
                        logger.debug(f"Error extracting DuckDuckGo result {i}: {e}")
                        continue
            except Exception as e:
                logger.warning(f"Error extracting DuckDuckGo results: {e}")
                pass
            
            return TaskResult(
                success=True,
                message=f"Successfully searched DuckDuckGo for: {query}",
                data={
                    "title": title,
                    "url": current_url,
                    "query": query,
                    "results": results,
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
        Perform a site-specific search using Google's site: operator.
        
        Args:
            site: Site domain (e.g., "bbc.com", "techcrunch.com")
            query: Search query
            
        Returns:
            TaskResult with search results
        """
        try:
            site_query = f"site:{site} {query}"
            logger.info(f"Performing site-specific search: {site_query}")
            
            # Try with Google first, but if CAPTCHA, try Bing
            result = await self.SEARCH_GOOGLE(site_query)
            if result.error != "CAPTCHA_DETECTED":
                return result
            
            # If Google has CAPTCHA, try Bing
            logger.info(f"Google blocked, trying Bing for site search: {site_query}")
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
        Try to get cached version using DuckDuckGo cache.
        
        Args:
            query: Original query
            
        Returns:
            TaskResult with cached results
        """
        try:
            # DuckDuckGo doesn't have a cache operator, so we'll just retry the search
            logger.info(f"Cache operator not available for DuckDuckGo. Retrying search: {query}")
            return await self.SEARCH_DUCKDUCKGO(query)
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
        Read the top search results from the current page and extract detailed information.
        
        Args:
            limit: Number of results to read
            
        Returns:
            TaskResult with top results and detailed content
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
            
            # Try to extract results (works for Google, Bing, DuckDuckGo)
            try:
                # DuckDuckGo style
                result_elements = await self.page.query_selector_all('article[data-testid="result"], .result, .web-result, h2 a[data-testid="result-title-a"]')
                if not result_elements:
                    # Google style
                    result_elements = await self.page.query_selector_all('div[data-header-feature="0"] h3, div.g h3, div.g a h3')
                if not result_elements:
                    # Bing style
                    result_elements = await self.page.query_selector_all('h2 a, .b_title a, .b_algo')
                
                for i, elem in enumerate(result_elements[:limit]):
                    try:
                        # Get title
                        title_elem = elem if elem.tag_name in ['H2', 'H3', 'A'] else await elem.query_selector('h2, h3, a')
                        if not title_elem:
                            title_elem = elem
                        
                        text = await title_elem.inner_text()
                        text = text.strip()
                        
                        # Get link
                        link_elem = await elem.query_selector('a') if elem.tag_name != 'A' else elem
                        if not link_elem and title_elem.tag_name == 'A':
                            link_elem = title_elem
                        
                        if link_elem:
                            link = await link_elem.get_attribute('href')
                            # Handle relative URLs
                            if link and not link.startswith('http'):
                                if link.startswith('/'):
                                    # Try to construct full URL
                                    base_url = current_url.split('/')[0] + '//' + current_url.split('/')[2]
                                    link = base_url + link
                                else:
                                    link = current_url + '/' + link
                        else:
                            link = None
                        
                        # Get snippet/description if available
                        snippet = ""
                        try:
                            # Try to find snippet/description
                            snippet_elem = await elem.query_selector('.result__snippet, .b_caption p, .VwiC3b, span[data-testid="result-snippet"]')
                            if snippet_elem:
                                snippet = await snippet_elem.inner_text()
                                snippet = snippet.strip()[:200]  # Limit snippet length
                        except:
                            pass
                        
                        if text and link:
                            results.append({
                                "title": text,
                                "url": link,
                                "snippet": snippet,
                                "rank": i + 1
                            })
                    except Exception as e:
                        logger.debug(f"Error extracting result {i}: {e}")
                        continue
            except Exception as e:
                logger.warning(f"Error extracting results: {e}")
            
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
            logger.error(f"Error reading top results: {e}")
            return TaskResult(
                success=False,
                message="Failed to read top results",
                error=str(e)
            )
    
    async def EXTRACT_DETAILED_CONTENT(self, url: str, max_content_length: int = 2000) -> TaskResult:
        """
        Extract detailed content from a specific URL.
        
        Args:
            url: URL to extract content from
            max_content_length: Maximum content length to extract
            
        Returns:
            TaskResult with detailed content
        """
        try:
            if not self.page:
                await self.initialize_browser()
            
            logger.info(f"Extracting detailed content from: {url}")
            
            # Navigate to the URL
            await self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(3)  # Wait for page to load (increased delay for stability)
            # Wait for network to be idle to ensure page is fully loaded
            try:
                await self.page.wait_for_load_state('networkidle', timeout=10000)
            except:
                pass
            await asyncio.sleep(1)  # Additional delay for stability
            
            # Check for CAPTCHA
            captcha_found = await self.DETECT_CAPTCHA()
            if captcha_found:
                return TaskResult(
                    success=False,
                    message=f"CAPTCHA detected on {url}",
                    error="CAPTCHA_DETECTED",
                    data={"url": url}
                )
            
            title = await self.page.title()
            current_url = self.page.url
            
            # Extract detailed content
            try:
                # Get main content
                body_text = await self.page.evaluate('() => document.body.innerText')
                
                # Get article content (try common article selectors)
                article_content = ""
                article_selectors = [
                    'article',
                    '[role="article"]',
                    '.article-content',
                    '.post-content',
                    '.entry-content',
                    'main article',
                    '.content',
                    '#content'
                ]
                
                for selector in article_selectors:
                    try:
                        article_elem = await self.page.query_selector(selector)
                        if article_elem:
                            article_content = await article_elem.inner_text()
                            if len(article_content) > 100:  # Only use if substantial content
                                break
                    except:
                        continue
                
                # Use article content if available, otherwise use body text
                main_content = article_content if article_content else body_text
                
                # Limit content length
                if len(main_content) > max_content_length:
                    main_content = main_content[:max_content_length] + "..."
                
                # Get meta description
                meta_desc = await self.page.evaluate("""() => {
                    const meta = document.querySelector('meta[name="description"]');
                    return meta ? meta.content : "";
                }""")
                
                # Get headings
                headings = await self.page.evaluate("""() => {
                    const h1s = Array.from(document.querySelectorAll("h1")).map(h => h.innerText).filter(t => t.trim());
                    const h2s = Array.from(document.querySelectorAll("h2")).map(h => h.innerText).filter(t => t.trim());
                    const h3s = Array.from(document.querySelectorAll("h3")).map(h => h.innerText).filter(t => t.trim());
                    return {h1: h1s, h2: h2s, h3: h3s};
                }""")
                
                # Get publication date if available
                pub_date = ""
                date_selectors = [
                    'time[datetime]',
                    '[class*="date"]',
                    '[class*="published"]',
                    'time'
                ]
                for selector in date_selectors:
                    try:
                        date_elem = await self.page.query_selector(selector)
                        if date_elem:
                            pub_date = await date_elem.get_attribute('datetime') or await date_elem.inner_text()
                            if pub_date:
                                break
                    except:
                        continue
                
                # Get author if available
                author = ""
                author_selectors = [
                    '[rel="author"]',
                    '[class*="author"]',
                    '.byline',
                    '[itemprop="author"]'
                ]
                for selector in author_selectors:
                    try:
                        author_elem = await self.page.query_selector(selector)
                        if author_elem:
                            author = await author_elem.inner_text()
                            if author:
                                break
                    except:
                        continue
                
                # Extract key information using LLM if available
                key_points = []
                if self.llm_service and main_content:
                    try:
                        summary_prompt = f"""Extract the key points and main information from this article content:

Title: {title}
Content: {main_content[:1500]}

Provide 3-5 key points or important facts from this content. Return as a JSON array of strings."""
                        
                        summary = self.llm_service.generate_content(summary_prompt)
                        # Try to extract array from response
                        import json
                        json_match = re.search(r'\[.*?\]', summary, re.DOTALL)
                        if json_match:
                            key_points = json.loads(json_match.group())
                        else:
                            # Fallback: split by lines or sentences
                            key_points = [s.strip() for s in summary.split('\n') if s.strip()][:5]
                    except Exception as e:
                        logger.debug(f"Error extracting key points: {e}")
                
                return TaskResult(
                    success=True,
                    message=f"Successfully extracted content from {title}",
                    data={
                        "title": title,
                        "url": current_url,
                        "content": main_content,
                        "content_preview": main_content[:500] if main_content else "",
                        "meta_description": meta_desc,
                        "headings": headings,
                        "publication_date": pub_date,
                        "author": author,
                        "key_points": key_points,
                        "content_length": len(main_content)
                    }
                )
            except Exception as e:
                logger.error(f"Error extracting detailed content: {e}")
                return TaskResult(
                    success=False,
                    message=f"Failed to extract content from {url}",
                    error=str(e),
                    data={"url": url}
                )
        except Exception as e:
            logger.error(f"Error navigating to URL {url}: {e}")
            return TaskResult(
                success=False,
                message=f"Failed to navigate to {url}",
                error=str(e),
                data={"url": url}
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
            
            # Navigate to Google
            await self.page.goto("https://www.google.com", wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(1)
            
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
            
            # Find search box - try multiple selectors
            search_selectors = [
                'textarea[name="q"]',
                'input[name="q"]',
                'textarea[aria-label*="Search"]',
                'input[type="search"]'
            ]
            
            search_box = None
            for selector in search_selectors:
                try:
                    search_box = await self.page.query_selector(selector)
                    if search_box:
                        break
                except:
                    continue
            
            if not search_box:
                return TaskResult(
                    success=False,
                    message="Could not find Google search box",
                    error="Search box element not found",
                    data={"query": query}
                )
            
            # Type search query
            await search_box.fill(query)
            await asyncio.sleep(0.5)
            
            # Submit search
            await search_box.press("Enter")
            await self.page.wait_for_load_state('networkidle', timeout=10000)
            await asyncio.sleep(2)
            
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
            
            # Try to extract first few search results
            results = []
            try:
                result_elements = await self.page.query_selector_all('div[data-header-feature="0"] h3, div.g h3')
                for i, elem in enumerate(result_elements[:5]):
                    try:
                        text = await elem.inner_text()
                        link_elem = await elem.query_selector('a')
                        link = await link_elem.get_attribute('href') if link_elem else None
                        results.append({"title": text, "url": link})
                    except:
                        continue
            except:
                pass
            
            return TaskResult(
                success=True,
                message=f"Successfully searched for: {query}",
                data={
                    "title": title,
                    "url": current_url,
                    "query": query,
                    "results": results
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
        Read and analyze the current page.
        
        Args:
            url: Optional URL to read (if not provided, reads current page)
            
        Returns:
            TaskResult with page analysis
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
            
            # Extract page content
            try:
                # Check if this is a Wikipedia page and extract more detailed content
                is_wikipedia = 'wikipedia.org' in current_url
                
                if is_wikipedia:
                    # Extract Wikipedia-specific content
                    wikipedia_content = await self.page.evaluate("""() => {
                        // Get main article content
                        const content = document.querySelector('#content, #mw-content-text, .mw-parser-output');
                        if (content) {
                            // Remove unwanted elements (nav, references, etc.)
                            const unwanted = content.querySelectorAll('.navbox, .reference, .mw-references-wrap, .mw-jump-link, .mw-editsection, .infobox');
                            unwanted.forEach(el => el.remove());
                            return content.innerText;
                        }
                        return document.body.innerText;
                    }""")
                    body_text = wikipedia_content if wikipedia_content else await self.page.evaluate('() => document.body.innerText')
                    
                    # Extract Wikipedia infobox
                    infobox_data = None
                    try:
                        infobox_data = await self.page.evaluate("""() => {
                            const infobox = document.querySelector('.infobox, .infobox_v2');
                            if (!infobox) return null;
                            const rows = Array.from(infobox.querySelectorAll('tr'));
                            const data = {};
                            rows.forEach(row => {
                                const header = row.querySelector('th');
                                const value = row.querySelector('td');
                                if (header && value) {
                                    const key = header.innerText.trim();
                                    const val = value.innerText.trim();
                                    if (key && val) {
                                        data[key] = val;
                                    }
                                }
                            });
                            return Object.keys(data).length > 0 ? data : null;
                        }""")
                    except:
                        pass
                else:
                    # Get main content for non-Wikipedia pages
                    body_text = await self.page.evaluate('() => document.body.innerText')
                    infobox_data = None
                
                # Get meta description
                meta_desc = await self.page.evaluate("""() => {
                    const meta = document.querySelector('meta[name="description"]');
                    return meta ? meta.content : "";
                }""")
                
                # Get headings (more comprehensive)
                headings = await self.page.evaluate("""() => {
                    const h1s = Array.from(document.querySelectorAll("h1")).map(h => h.innerText.trim()).filter(t => t);
                    const h2s = Array.from(document.querySelectorAll("h2")).map(h => h.innerText.trim()).filter(t => t);
                    const h3s = Array.from(document.querySelectorAll("h3")).map(h => h.innerText.trim()).filter(t => t);
                    return {h1: h1s, h2: h2s, h3: h3s};
                }""")
                
                # Extract key paragraphs from Wikipedia
                key_paragraphs = []
                if is_wikipedia:
                    try:
                        key_paragraphs = await self.page.evaluate("""() => {
                            const content = document.querySelector('#mw-content-text, .mw-parser-output');
                            if (!content) return [];
                            const paragraphs = Array.from(content.querySelectorAll('p'));
                            return paragraphs
                                .map(p => p.innerText.trim())
                                .filter(p => p.length > 50 && p.length < 500)
                                .slice(0, 5);
                        }""")
                    except:
                        pass
            except Exception as e:
                logger.warning(f"Error extracting page content: {e}")
                body_text = ""
                meta_desc = ""
                headings = {}
                infobox_data = None
                key_paragraphs = []
            
            # Analyze for errors or issues
            issues = []
            try:
                # Check for common error indicators
                error_indicators = ['error', '404', 'not found', 'page not found', 'access denied']
                if any(indicator in body_text.lower() for indicator in error_indicators):
                    issues.append("Possible error detected on page")
            except:
                pass
            
            # Build data dictionary
            data = {
                "title": title,
                "url": current_url,
                "content": body_text[:3000] if body_text else "",  # Increased content length
                "content_preview": body_text[:500] if body_text else "",
                "meta_description": meta_desc,
                "headings": headings,
                "issues": issues
            }
            
            # Add Wikipedia-specific data
            if 'wikipedia.org' in current_url:
                if infobox_data:
                    data["infobox"] = infobox_data
                if key_paragraphs:
                    data["key_paragraphs"] = key_paragraphs
                data["content_length"] = len(body_text) if body_text else 0
            
            return TaskResult(
                success=True,
                message=f"Successfully read page: {title}",
                data=data
            )
        except Exception as e:
            logger.error(f"Error reading page: {e}")
            return TaskResult(
                success=False,
                message="Failed to read page",
                error=str(e),
                data={"url": url or "current page"}
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
                if not self.captcha_detected and result.success:
                    # Check if we need to search within the website
                    # If the original query contains search terms (e.g., "find X on wikipedia"), 
                    # we should search within the opened website
                    # Correct typos in original query for website detection
                    original_query = self._correct_website_typos(self.task_query)
                    original_query_lower = original_query.lower()
                    website_domains = ['wikipedia', 'wikipida', 'wikipeda', 'wikipidia', 'wikepedia', 'wikpedia', 'wkipedia', 
                                      'reddit', 'redit', 'redditt', 
                                      'github', 'githu', 'githb', 
                                      'stackoverflow', 'stackoverflw', 'stackoverfow', 
                                      'youtube', 'youtue', 'youtub', 
                                      'twitter', 'twiter', 'twittr', 
                                      'facebook', 'facebok', 'faceboook']
                    
                    # Check if query has both website and search terms
                    has_website = any(domain in original_query_lower for domain in website_domains)
                    has_search_terms = any(word in original_query_lower for word in ['find', 'search', 'look for', 'about', 'information'])
                    
                    if has_website and has_search_terms:
                        # Extract search terms from original query (remove website and command words)
                        search_terms = original_query  # Use corrected query (typos already fixed)
                        
                        # Remove website mentions (including typos)
                        website_patterns = website_domains + ['wikipedia', 'wikipida', 'wikipeda', 'wikipidia', 'wikepedia', 'wikpedia', 'wkipedia']
                        for domain in website_patterns:
                            search_terms = re.sub(f'\\b{domain}\\b', '', search_terms, flags=re.IGNORECASE)
                        
                        # Remove command words (including typos and filler words)
                        command_words = ['find', 'search', 'look for', 'on', 'from', 'visit', 'vist', 'visti', 'vistit', 
                                       'open', 'go to', 'navigate to', 'check', 'read', 'about', 'it', 'and', 'the', 'a', 'an']
                        for word in command_words:
                            # Remove word with word boundaries to avoid partial matches
                            search_terms = re.sub(r'\b' + re.escape(word) + r'\b', '', search_terms, flags=re.IGNORECASE)
                        
                        # Remove extra spaces and clean up
                        search_terms = re.sub(r'\s+', ' ', search_terms).strip()
                        # Remove leading/trailing "and" and other connectors
                        search_terms = re.sub(r'^\s*(and|or|but)\s+|\s+(and|or|but)\s*$', '', search_terms, flags=re.IGNORECASE).strip()
                        
                        # Final cleanup - remove any remaining single-letter words and extra connectors
                        words = search_terms.split()
                        filtered_words = [w for w in words if len(w) > 1 and w.lower() not in ['and', 'or', 'but', 'the', 'a', 'an', 'it', 'is', 'are', 'was', 'were']]
                        search_terms = ' '.join(filtered_words).strip()
                        
                        logger.info(f"Extracted search terms: '{search_terms}' from original query: '{self.task_query}'")
                        
                        if search_terms and len(search_terms) > 3:
                            logger.info(f"Searching within website for: {search_terms}")
                            # Try to find and use the website's search box
                            try:
                                # Common search box selectors
                                search_selectors = [
                                    'input[type="search"]',
                                    'input[name="search"]',
                                    'input[id*="search"]',
                                    'input[placeholder*="Search"]',
                                    'input[aria-label*="Search"]',
                                    '#searchInput',  # Wikipedia
                                    '#search',  # Common
                                    '.search-input',  # Common
                                ]
                                
                                search_box = None
                                for selector in search_selectors:
                                    try:
                                        search_box = await self.page.query_selector(selector)
                                        if search_box:
                                            logger.info(f"Found search box with selector: {selector}")
                                            break
                                    except:
                                        continue
                                
                                if search_box:
                                    # Type search terms and submit
                                    await search_box.fill(search_terms)
                                    await asyncio.sleep(0.5)
                                    await search_box.press("Enter")
                                    # Wait for navigation to start
                                    await asyncio.sleep(1)
                                    # Wait for page load (use domcontentloaded for better reliability)
                                    try:
                                        await self.page.wait_for_load_state('domcontentloaded', timeout=15000)
                                    except Exception as e:
                                        logger.warning(f"Timeout waiting for domcontentloaded: {e}")
                                    await asyncio.sleep(2)  # Additional wait for content to render
                                    
                                    # Check for CAPTCHA after search
                                    captcha_found = await self.DETECT_CAPTCHA()
                                    if captcha_found:
                                        self.captcha_detected = True
                                        self.captcha_url = self.page.url
                                        title = await self.page.title()
                                        return TaskResult(
                                            success=False,
                                            message=f"CAPTCHA detected after searching within website",
                                            error="CAPTCHA_DETECTED",
                                            data={"title": title, "url": self.page.url}
                                        )
                                    
                                    # Read the search results page
                                    read_result = await self.READ_PAGE()
                                    if read_result.success:
                                        self.RECORD_STEP(f"Searched within website for: {search_terms}", read_result)
                                        
                                        # Extract detailed content from Wikipedia search results
                                        if 'wikipedia' in original_query_lower:
                                            logger.info("Extracting detailed content from Wikipedia search results...")
                                            detailed_results = await self._extract_wikipedia_search_results(search_terms)
                                            if detailed_results:
                                                read_result.data["detailed_results"] = detailed_results
                                                read_result.data["extraction_summary"] = {
                                                    "total_results": len(detailed_results),
                                                    "search_terms": search_terms,
                                                    "source": "wikipedia"
                                                }
                                                # Update the message to include extraction summary
                                                read_result.message = f"Successfully searched Wikipedia for '{search_terms}' and extracted detailed content from {len(detailed_results)} articles"
                                        
                                        return read_result
                                else:
                                    logger.info("Search box not found. Reading the opened page instead.")
                            except Exception as e:
                                logger.warning(f"Error searching within website: {e}. Reading the opened page instead.")
                    
                    # Read the page (if no search was performed or search failed)
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
                    
                    # Successfully read the page
                    return read_result
                else:
                    return result
                
            elif plan.action == "SEARCH_DUCKDUCKGO" or plan.action == "SEARCH_GOOGLE":
                # Map SEARCH_GOOGLE to SEARCH_DUCKDUCKGO
                if plan.action == "SEARCH_GOOGLE":
                    logger.info("Mapping SEARCH_GOOGLE to SEARCH_DUCKDUCKGO (DuckDuckGo is default search engine)")
                    plan.action = "SEARCH_DUCKDUCKGO"
                
                # Step 1: Attempt primary search on DuckDuckGo
                result = await self.SEARCH_DUCKDUCKGO(plan.target)
                self.RECORD_STEP(f"Searched DuckDuckGo for: {plan.target}", result)
                
                # Step 2: Check if CAPTCHA was detected
                if result.error == "CAPTCHA_DETECTED":
                    logger.warning("CAPTCHA detected on DuckDuckGo. Trying fallback strategies...")
                    
                    # Get fallback strategies
                    fallbacks = await self.REASON_AND_CHOOSE_FALLBACK(plan.target)
                    logger.info(f"Trying {len(fallbacks)} fallback strategies...")
                    
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
                            logger.info(f"Fallback {i} succeeded! Using results from {fallback.get('description')}")
                            fallback_success = True
                            
                            # Close new tab if we opened one
                            try:
                                if new_tab and self.page == new_tab and old_page:
                                    await new_tab.close()
                                    self.page = old_page
                            except:
                                pass
                            
                            # Return successful result
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
                
                # Step 3: Read the search results page and extract detailed content (only if no CAPTCHA)
                if not self.captcha_detected and result.success:
                    read_result = await self.READ_TOP_RESULTS(limit=5)
                    self.RECORD_STEP("Read top search results", read_result)
                    
                    # Check if CAPTCHA was detected during read
                    if read_result.error == "CAPTCHA_DETECTED":
                        logger.warning("CAPTCHA detected while reading results. Trying fallbacks...")
                        
                        # Try fallbacks again
                        fallbacks = await self.REASON_AND_CHOOSE_FALLBACK(plan.target)
                        for i, fallback in enumerate(fallbacks, 1):
                            logger.info(f"Fallback {i}/{len(fallbacks)}: {fallback.get('description')}")
                            fallback_result = await self.EXECUTE_FALLBACK_STRATEGY(fallback, plan.target)
                            self.RECORD_STEP(f"Fallback attempt {i}: {fallback.get('description')}", fallback_result)
                            
                            if fallback_result.success and fallback_result.error != "CAPTCHA_DETECTED":
                                logger.info(f"Fallback {i} succeeded!")
                                return fallback_result
                        
                        # All fallbacks failed
                        return read_result
                    
                    # Successfully read results - now extract detailed content
                    if read_result.success:
                        result.data["top_results"] = read_result.data.get("results", [])
                        
                        # Extract detailed content from top results
                        logger.info(f"Extracting detailed content from top {min(3, len(read_result.data.get('results', [])))} results...")
                        detailed_results = []
                        for i, res in enumerate(read_result.data.get("results", [])[:3]):
                            if res.get("url") and res["url"].startswith("http"):
                                try:
                                    logger.info(f"Extracting content from result {i+1}: {res.get('title', res.get('url'))}")
                                    detail_result = await self.EXTRACT_DETAILED_CONTENT(res["url"], max_content_length=2000)
                                    if detail_result.success:
                                        detailed_results.append(detail_result.data)
                                        self.RECORD_STEP(f"Extracted detailed content from: {res.get('title', res.get('url'))}", detail_result)
                                    elif detail_result.error == "CAPTCHA_DETECTED":
                                        logger.warning(f"CAPTCHA detected on result {i+1}, skipping detailed extraction")
                                    else:
                                        logger.warning(f"Failed to extract content from result {i+1}: {detail_result.message}")
                                except Exception as e:
                                    logger.error(f"Error extracting content from result {i+1}: {e}")
                                    continue
                        
                        result.data["detailed_results"] = detailed_results
                        result.data["extraction_summary"] = {
                            "total_results": len(read_result.data.get("results", [])),
                            "detailed_extractions": len(detailed_results),
                            "query": plan.target
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
