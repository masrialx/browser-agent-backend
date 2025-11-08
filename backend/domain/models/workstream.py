from typing import List, Optional
from pydantic import BaseModel
from domain.models.module import Module
from domain.models.kpi import KPI

class Workstream(BaseModel):
    """Workstream model."""
    work_stream_id: str
    sub_goal_id: str
    goal_id: str
    agent_id: str
    workstream: str
    modules: List[Module]
    frequency: str
    kpis: List[KPI]

