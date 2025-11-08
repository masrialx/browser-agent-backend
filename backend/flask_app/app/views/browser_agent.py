import os
import sys
import logging
from flask import Blueprint, request, jsonify

# Add backend directory to Python path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from infrastructure.llm.open_ai_llm import GeminiLLMService
from infrastructure.repositories.agent_repository import AgentRepository
from infrastructure.repositories.workstream_repository import WorkstreamRepository
from src.usecases.browser_usecase import BrowserUseCase

logger = logging.getLogger(__name__)

# Create Blueprint
browser_agent_bp = Blueprint('browser_agent', __name__)

# Initialize services (singleton pattern)
_llm_service = None
_agent_repository = None
_workstream_repository = None
_browser_use_case = None

def get_services():
    """Initialize and return service instances."""
    global _llm_service, _agent_repository, _workstream_repository, _browser_use_case
    
    if _llm_service is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        _llm_service = GeminiLLMService(api_key=api_key)
    
    if _agent_repository is None:
        _agent_repository = AgentRepository()
    
    if _workstream_repository is None:
        _workstream_repository = WorkstreamRepository()
    
    if _browser_use_case is None:
        _browser_use_case = BrowserUseCase(
            llm_service=_llm_service,
            agent_repository=_agent_repository,
            workstream_repository=_workstream_repository
        )
    
    return _browser_use_case

@browser_agent_bp.route('/execute', methods=['POST'])
def execute_browser_task():
    """
    Execute a browser task with strict JSON input/output format.
    
    Request Body (strict format):
        {
            "query": "<user query>",
            "agent_id": "<agent_id>"  // Optional
        }
    
    Returns (strict JSON format):
        {
            "data": {
                "agent_id": "<agent_id>",
                "overall_success": true|false,
                "query": "<original query>",
                "steps": [
                    {
                        "step": "<description of action taken>",
                        "result": {
                            "data": {
                                "title": "<page title or resource title>",
                                "url": "<accessed url>"
                            },
                            "error": null|"error message if any",
                            "message": "<short execution message>",
                            "success": true|false
                        },
                        "success": true|false
                    }
                ]
            },
            "success": true|false
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "Request body is required",
                "data": None
            }), 400
        
        query = data.get("query")
        if not query:
            return jsonify({
                "success": False,
                "error": "Query is required",
                "data": None
            }), 400
        
        agent_id = data.get("agent_id")
        user_id = data.get("user_id")  # Optional, not in strict format but allowed
        
        logger.info(f"Executing browser task: {query} for agent: {agent_id}")
        
        # Get browser use case instance
        browser_use_case = get_services()
        
        # Execute the task (synchronous wrapper)
        result_data = browser_use_case.execute_browser_task(
            query=query,
            agent_id=agent_id,
            user_id=user_id
        )
        
        # Ensure result_data has all required fields
        if "agent_id" not in result_data:
            result_data["agent_id"] = agent_id or "unknown"
        if "overall_success" not in result_data:
            result_data["overall_success"] = False
        if "query" not in result_data:
            result_data["query"] = query
        if "steps" not in result_data:
            result_data["steps"] = []
        
        # Return in strict format
        return jsonify({
            "success": result_data.get("overall_success", False),
            "data": result_data
        }), 200
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "data": None
        }), 500
    except Exception as e:
        logger.exception(f"Error executing browser task: {e}")
        # Return error in strict format
        query = data.get("query", "unknown") if 'data' in locals() else "unknown"
        agent_id = data.get("agent_id") if 'data' in locals() else None
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}",
            "data": {
                "agent_id": agent_id or "unknown",
                "overall_success": False,
                "query": query,
                "steps": [
                    {
                        "step": f"Execute task: {query}",
                        "success": False,
                        "result": {
                            "success": False,
                            "message": "Internal server error",
                            "data": {
                                "title": "",
                                "url": ""
                            },
                            "error": str(e)
                        }
                    }
                ]
            }
        }), 500

@browser_agent_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        # Try to initialize services to check if everything is configured
        get_services()
        return jsonify({
            "status": "healthy",
            "message": "Browser agent service is running"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500
