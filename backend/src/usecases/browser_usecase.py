import asyncio
import json
import logging
from typing import Dict, Optional, List
from infrastructure.browser_automation_latest.browser_agent import BrowserAgent, TaskResult
from infrastructure.llm.open_ai_llm import GeminiLLMService
from infrastructure.repositories.agent_repository import AgentRepository
from infrastructure.repositories.workstream_repository import WorkstreamRepository
from domain.models.workstream import Workstream
from domain.models.module import Module, Frequency
from domain.models.kpi import KPI
import uuid

from pydantic import BaseModel
class ArraySchema(BaseModel):
    array: list

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class BrowserUseCase:
    def __init__(self, llm_service: GeminiLLMService, 
                 agent_repository: AgentRepository, 
                 workstream_repository: WorkstreamRepository):
        self.llm_service = llm_service
        self.agent_repository = agent_repository
        self.workstream_repository = workstream_repository

    async def execute_browser_task_async(self, query: str, agent_id: Optional[str] = None, user_id: Optional[str] = None) -> Dict:
        """
        Execute browser task with enhanced reasoning and strict JSON output format.
        
        Args:
            query: User query describing the task
            agent_id: Optional agent identifier
            user_id: Optional user identifier
            
        Returns:
            Dict matching the strict JSON format:
            {
                "agent_id": "<agent_id>",
                "overall_success": true|false,
                "query": "<original query>",
                "steps": [
                    {
                        "step": "<description>",
                        "result": {
                            "data": {"title": "...", "url": "..."},
                            "error": null|"error message",
                            "message": "<execution message>",
                            "success": true|false
                        },
                        "success": true|false
                    }
                ]
            }
        """
        try:
            user_id = user_id or "default_user"
            agent_id = agent_id or f"agent_{uuid.uuid4().hex[:8]}"
            
            logger.info(f"Executing browser task: {query} for agent: {agent_id}")
            
            # Initialize browser agent with LLM service for reasoning
            browser_agent = BrowserAgent(
                task_query=query,
                llm_service=self.llm_service,
                user_id=user_id,
                agent_id=agent_id
            )
            
            # Execute the task
            final_result: TaskResult = await browser_agent.run()
            
            # Get all recorded steps
            recorded_steps = browser_agent.get_recorded_steps()
            
            # If no steps were recorded, create one from the final result
            if not recorded_steps:
                recorded_steps = [{
                    "step": f"Execute task: {query}",
                    "success": final_result.success,
                    "result": final_result.dict()
                }]
            
            # Format steps to match required structure
            formatted_steps = []
            captcha_detected = False
            
            for step in recorded_steps:
                # Ensure result has the required structure
                result = step.get("result", {})
                step_desc = step.get("step", "Unknown step")
                
                if isinstance(result, dict):
                    # Check if this step contains a CAPTCHA error
                    if result.get("error") == "CAPTCHA_DETECTED":
                        captcha_detected = True
                        # Ensure the step description indicates CAPTCHA detection
                        if "CAPTCHA" not in step_desc.upper():
                            step_desc = f"Detect CAPTCHA and pause: {step_desc}"
                    
                    # Ensure data field exists - preserve all existing data
                    if "data" not in result:
                        result["data"] = {}
                    
                    # Ensure basic fields exist, but preserve all other data (like detailed_results, top_results, etc.)
                    if "title" not in result["data"]:
                        result["data"]["title"] = result.get("data", {}).get("title", "")
                    if "url" not in result["data"]:
                        result["data"]["url"] = result.get("data", {}).get("url", "")
                    
                    # Preserve all nested data structures (detailed_results, top_results, extraction_summary, etc.)
                    # These are important for detailed extraction information
                    if isinstance(result.get("data"), dict):
                        # Keep all existing data fields - don't overwrite them
                        pass
                    
                    # Ensure error field exists
                    if "error" not in result:
                        result["error"] = None
                    # Ensure message field exists
                    if "message" not in result:
                        result["message"] = result.get("message", "")
                    # Ensure success field exists
                    if "success" not in result:
                        result["success"] = step.get("success", False)
                elif hasattr(result, 'dict'):
                    # Convert TaskResult to dict if it's a Pydantic model
                    result = result.dict()
                    # Recursively process
                    if "data" not in result:
                        result["data"] = {}
                    if "title" not in result["data"]:
                        result["data"]["title"] = result.get("data", {}).get("title", "")
                    if "url" not in result["data"]:
                        result["data"]["url"] = result.get("data", {}).get("url", "")
                
                formatted_step = {
                    "step": step_desc,
                    "result": result,
                    "success": step.get("success", False)
                }
                formatted_steps.append(formatted_step)
            
            # If final result has CAPTCHA error, ensure it's in steps
            if final_result.error == "CAPTCHA_DETECTED" and not captcha_detected:
                captcha_step = {
                    "step": "Detect CAPTCHA and pause",
                    "result": final_result.dict(),
                    "success": False
                }
                # Ensure proper structure for CAPTCHA step
                if "data" not in captcha_step["result"]:
                    captcha_step["result"]["data"] = {}
                if "title" not in captcha_step["result"]["data"]:
                    captcha_step["result"]["data"]["title"] = final_result.data.get("title", "")
                if "url" not in captcha_step["result"]["data"]:
                    captcha_step["result"]["data"]["url"] = final_result.data.get("url", "")
                formatted_steps.append(captcha_step)
                captcha_detected = True
            
            # Calculate overall success
            # If CAPTCHA was detected but later resolved and task completed, mark as successful
            # Check if final result is successful (meaning CAPTCHA was resolved and task completed)
            if final_result.success and final_result.error != "CAPTCHA_DETECTED":
                # Task completed successfully, even if CAPTCHA was detected earlier
                overall_success = True
            elif captcha_detected and final_result.error == "CAPTCHA_DETECTED":
                # CAPTCHA detected and not resolved
                overall_success = False
            else:
                # Normal success calculation
                overall_success = all(step.get("success", False) for step in formatted_steps) and final_result.success
            
            # Build response in required format
            response = {
                "agent_id": agent_id,
                "overall_success": overall_success,
                "query": query,
                "steps": formatted_steps
            }
            
            # Cleanup browser agent
            # If CAPTCHA detected and NOT resolved (task not completed), keep browser open
            # If CAPTCHA was resolved and task completed, close browser normally
            if final_result.error == "CAPTCHA_DETECTED" and not final_result.success:
                logger.info("CAPTCHA detected but not resolved. Keeping browser open for user to complete CAPTCHA manually.")
                # Don't close browser - let user see and complete CAPTCHA
                await browser_agent.cleanup(force_close=False)
                # Note: Browser remains open. User should complete CAPTCHA manually.
            elif captcha_detected and final_result.success:
                logger.info("CAPTCHA was resolved and task completed successfully. Closing browser.")
                # CAPTCHA was resolved and task completed - close browser normally
                await browser_agent.cleanup(force_close=True)
            elif final_result.success:
                logger.info("Task completed successfully. Closing browser.")
                # Normal cleanup - close browser
                await browser_agent.cleanup(force_close=True)
            else:
                # Error case - close browser
                logger.info("Task failed. Closing browser.")
                await browser_agent.cleanup(force_close=True)
            
            # Save workstream if agent_id is provided and task succeeded
            if agent_id and overall_success:
                try:
                    sub_functions = self.generate_sub_functions("browser_task", {"query": query})
                    modules = [
                        Module(
                            module=sf.get("name", sf.get("step", "unknown")),
                            kpis=[],
                            frequency=Frequency.NOT_REQUIRED.value,
                            apis=[]
                        ) for sf in sub_functions
                    ]
                    kpis = [KPI(kpi="Task completed", expected_value="100%")]
                    workstream = Workstream(
                        work_stream_id=f"ws_{uuid.uuid4().hex}",
                        sub_goal_id=f"sg_{uuid.uuid4().hex}",
                        goal_id=f"g_{uuid.uuid4().hex}",
                        agent_id=agent_id,
                        workstream=f"Execute browser task for {query}",
                        modules=modules,
                        frequency="once",
                        kpis=kpis
                    )
                    self.workstream_repository.create_workstream(workstream)
                except Exception as e:
                    logger.warning(f"Failed to create workstream: {e}")
            
            return response

        except Exception as e:
            logger.exception(f"Browser task execution failed: {str(e)}")
            # Return error response in required format
            return {
                "agent_id": agent_id or "unknown",
                "overall_success": False,
                "query": query,
                "steps": [
                    {
                        "step": f"Execute task: {query}",
                        "success": False,
                        "result": {
                            "success": False,
                            "message": "Task execution failed",
                            "data": {
                                "title": "",
                                "url": ""
                            },
                            "error": str(e)
                        }
                    }
                ]
            }

    def generate_sub_functions(self, function_name: str, args: dict) -> List[dict]:
        """Generate sub-functions for a browser task."""
        system_instruction = """You are an AI assistant that breaks down browser tasks into sub-functions."""
        example = json.dumps([
            {"name": "open_browser", "args": {"url": "https://www.google.com"}},
            {"name": "type_query", "args": {"query": "test"}},
            {"name": "click_search", "args": {}}
        ])
        query = f"""
        Given the browser function '{function_name}' with arguments {json.dumps(args)},
        provide a list of sub-functions to accomplish it.
        Each sub-function should have a name and arguments.
        Example for 'search_google(query="test")': {example}
        Return your response as a JSON list.
        """
        try:
            response = self.llm_service.generate_content_with_Structured_schema(
                system_instruction=system_instruction,
                query=query,
                response_schema=ArraySchema
            )
            if not isinstance(response.array, list):
                logger.error(f"Invalid sub-functions response: {response.array}")
                return []
            return [json.loads(item) if isinstance(item, str) else item for item in response.array]
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse sub-functions: {e}")
            return []
        except Exception as e:
            logger.error(f"Error generating sub-functions: {str(e)}")
            return []

    def execute_browser_task(self, query: str, agent_id: Optional[str] = None, user_id: Optional[str] = None) -> Dict:
        """
        Synchronous wrapper for execute_browser_task_async.
        
        Args:
            query: User query
            agent_id: Optional agent identifier
            user_id: Optional user identifier
            
        Returns:
            Dict with execution results in strict JSON format
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.execute_browser_task_async(query, agent_id, user_id))
        except SystemExit:
            logger.info("Synchronous execution terminated due to manual browser closure")
            return {
                "agent_id": agent_id or "unknown",
                "overall_success": False,
                "query": query,
                "steps": [
                    {
                        "step": f"Execute task: {query}",
                        "success": False,
                        "result": {
                            "success": False,
                            "message": "Program terminated due to manual browser closure",
                            "data": {
                                "title": "",
                                "url": ""
                            },
                            "error": "Program terminated due to manual browser closure"
                        }
                    }
                ]
            }
        finally:
            loop.close()
