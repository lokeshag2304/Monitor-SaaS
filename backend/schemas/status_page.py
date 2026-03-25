from pydantic import BaseModel
from typing import List, Optional

class StatusGroupItemCreate(BaseModel):
    monitor_id: int

class StatusGroupCreate(BaseModel):
    name: str
    items: List[StatusGroupItemCreate]

class StatusPageCreate(BaseModel):
    name: str
    slug: str
    custom_message: Optional[str] = None
    groups: List[StatusGroupCreate]
    # logo is handled via form data if there's an image, or we might upload logo separately

class StatusGroupItemResponse(BaseModel):
    id: int
    monitor_id: int
    
    class Config:
        orm_mode = True

class StatusGroupResponse(BaseModel):
    id: int
    name: str
    items: List[StatusGroupItemResponse]
    
    class Config:
        orm_mode = True

class StatusPageResponse(BaseModel):
    id: int
    name: str
    slug: str
    logo: Optional[str] = None
    custom_message: Optional[str] = None
    groups: List[StatusGroupResponse]
    
    class Config:
        orm_mode = True
