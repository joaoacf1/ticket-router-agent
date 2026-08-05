from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class TicketCreate(BaseModel):
    title: str
    description: str

class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    description: str
    status: str
    department: Optional[str] = None
    confidence: Optional[float] = None
    created_at: datetime
