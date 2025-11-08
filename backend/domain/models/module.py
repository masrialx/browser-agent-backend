from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

class Frequency(str, Enum):
    """Frequency enumeration."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    NOT_REQUIRED = "not_required"
    ONCE = "once"

class Module(BaseModel):
    """Module model."""
    module: str
    kpis: List = []
    frequency: str
    apis: List[str] = []

