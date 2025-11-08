import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class AgentRepository:
    """Repository for agent data operations."""
    
    def __init__(self):
        # In a real implementation, this would connect to a database
        self.agents = {}
    
    def get_agent(self, agent_id: str) -> Optional[Dict]:
        """Get agent by ID."""
        return self.agents.get(agent_id)
    
    def create_agent(self, agent_data: Dict) -> str:
        """Create a new agent."""
        agent_id = agent_data.get("agent_id", f"agent_{len(self.agents) + 1}")
        self.agents[agent_id] = agent_data
        return agent_id
    
    def update_agent(self, agent_id: str, agent_data: Dict) -> bool:
        """Update an existing agent."""
        if agent_id in self.agents:
            self.agents[agent_id].update(agent_data)
            return True
        return False

