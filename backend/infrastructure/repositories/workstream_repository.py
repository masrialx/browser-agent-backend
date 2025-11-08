import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

class WorkstreamRepository:
    """Repository for workstream data operations."""
    
    def __init__(self):
        # In a real implementation, this would connect to a database
        self.workstreams = {}
    
    def create_workstream(self, workstream) -> str:
        """Create a new workstream."""
        workstream_id = workstream.work_stream_id if hasattr(workstream, 'work_stream_id') else f"ws_{len(self.workstreams) + 1}"
        # Convert workstream to dict if it's a Pydantic model
        if hasattr(workstream, 'dict'):
            self.workstreams[workstream_id] = workstream.dict()
        elif hasattr(workstream, 'model_dump'):
            self.workstreams[workstream_id] = workstream.model_dump()
        else:
            self.workstreams[workstream_id] = workstream
        logger.info(f"Created workstream: {workstream_id}")
        return workstream_id
    
    def get_workstream(self, workstream_id: str) -> Optional[Dict]:
        """Get workstream by ID."""
        return self.workstreams.get(workstream_id)
    
    def get_workstreams_by_agent(self, agent_id: str) -> List[Dict]:
        """Get all workstreams for an agent."""
        return [ws for ws in self.workstreams.values() if ws.get("agent_id") == agent_id]

