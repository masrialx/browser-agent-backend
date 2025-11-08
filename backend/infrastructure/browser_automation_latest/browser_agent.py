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
    
    def REASON_AND_DECIDE(self, query: str) -> ActionPlan:
        """
        Use reasoning to decide the best action for the query.
        
        Args:
            query: User query
            
        Returns:
            ActionPlan with recommended action
        """
        if self.llm_service:
            try:
                # Use LLM to reason about the query
                reasoning_prompt = f"""
                Analyze this user query and determine the best action:
                Query: "{query}"
                
                Determine:
                1. Does the query contain a URL? If yes, extract it.
                2. If no URL, should we search Google? What search terms?
                3. What is the user trying to accomplish?
                4. What action should we take? (OPEN_URL, SEARCH_GOOGLE, READ_PAGE, FIX_ISSUE)
                
                Respond with JSON only, no additional text:
                {{
                    "action": "OPEN_URL|SEARCH_GOOGLE|READ_PAGE|FIX_ISSUE",
                    "target": "url or search query",
                    "reason": "why this action",
                    "expected_outcome": "what we expect to achieve"
                }}
                """
                response = self.llm_service.generate_content(reasoning_prompt)
                # Parse response (might be JSON or text with JSON)
                import json
                # Try to extract JSON from response
                json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
                if json_match:
                    try:
                        plan_dict = json.loads(json_match.group())
                        return ActionPlan(**plan_dict)
                    except Exception as e:
                        logger.warning(f"Failed to parse LLM response as ActionPlan: {e}, using fallback")
            except Exception as e:
                logger.error(f"Reasoning failed: {e}")
        
        # Fallback logic without LLM
        query_lower = query.lower()
        
        # Check for URL
        url_pattern = r'https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9-]+\.[a-zA-Z]{2,}'
        urls = re.findall(url_pattern, query)
        if urls:
            url = urls[0]
            if not url.startswith('http'):
                url = 'https://' + url
            return ActionPlan(
                action="OPEN_URL",
                target=url,
                reason="URL detected in query",
                expected_outcome="Navigate to the specified website"
            )
        
        # Check for search intent
        search_keywords = ['search', 'find', 'look for', 'what is', 'how to', 'where is']
        if any(keyword in query_lower for keyword in search_keywords):
            # Extract search terms
            search_terms = query
            for keyword in search_keywords:
                search_terms = re.sub(keyword, '', search_terms, flags=re.IGNORECASE).strip()
            return ActionPlan(
                action="SEARCH_GOOGLE",
                target=search_terms or query,
                reason="Search intent detected",
                expected_outcome="Find relevant information via Google search"
            )
        
        # Default: search Google
        return ActionPlan(
            action="SEARCH_GOOGLE",
            target=query,
            reason="No specific URL provided, using Google search",
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
            await asyncio.sleep(2)  # Wait for page to fully load
            
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
                await self.OPEN_URL(url)
            
            current_url = self.page.url
            title = await self.page.title()
            
            # Extract page content
            try:
                # Get main content
                body_text = await self.page.evaluate('() => document.body.innerText')
                # Get meta description
                meta_desc = await self.page.evaluate("""() => {
                    const meta = document.querySelector('meta[name="description"]');
                    return meta ? meta.content : "";
                }""")
                # Get headings
                headings = await self.page.evaluate("""() => {
                    const h1s = Array.from(document.querySelectorAll("h1")).map(h => h.innerText);
                    const h2s = Array.from(document.querySelectorAll("h2")).map(h => h.innerText);
                    return {h1: h1s, h2: h2s};
                }""")
            except Exception as e:
                logger.warning(f"Error extracting page content: {e}")
                body_text = ""
                meta_desc = ""
                headings = {}
            
            # Analyze for errors or issues
            issues = []
            try:
                # Check for common error indicators
                error_indicators = ['error', '404', 'not found', 'page not found', 'access denied']
                if any(indicator in body_text.lower() for indicator in error_indicators):
                    issues.append("Possible error detected on page")
            except:
                pass
            
            return TaskResult(
                success=True,
                message=f"Successfully read page: {title}",
                data={
                    "title": title,
                    "url": current_url,
                    "content_preview": body_text[:500] if body_text else "",
                    "meta_description": meta_desc,
                    "headings": headings,
                    "issues": issues
                }
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
                
                # After opening, read the page
                read_result = await self.READ_PAGE()
                self.RECORD_STEP(f"Read page content from {plan.target}", read_result)
                
            elif plan.action == "SEARCH_GOOGLE":
                result = await self.SEARCH_GOOGLE(plan.target)
                self.RECORD_STEP(f"Searched Google for: {plan.target}", result)
                
                # Read the search results page
                read_result = await self.READ_PAGE()
                self.RECORD_STEP("Read search results page", read_result)
                
            elif plan.action == "READ_PAGE":
                result = await self.READ_PAGE(plan.target if plan.target else None)
                self.RECORD_STEP(f"Read page: {plan.target or 'current page'}", result)
                
            elif plan.action == "FIX_ISSUE":
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
    
    async def cleanup(self):
        """Clean up browser resources."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
