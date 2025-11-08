from pydantic import BaseModel

class KPI(BaseModel):
    """KPI model."""
    kpi: str
    expected_value: str

