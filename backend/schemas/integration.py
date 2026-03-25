from pydantic import BaseModel
from typing import Dict, Any

class IntegrationCreate(BaseModel):
    provider: str
    config: Dict[str, Any]
    is_enabled: bool = True

class IntegrationResponse(BaseModel):
    id: int
    provider: str
    config: Dict[str, Any]
    is_enabled: bool

    class Config:
        orm_mode = True
