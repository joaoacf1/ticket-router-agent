from datetime import datetime
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
    created_at: datetime
