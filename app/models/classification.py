from typing import Literal, List
from pydantic import BaseModel, Field

DepartmentType = Literal["Engineering", "Marketing", "Support", "Finance"]

class TicketClassification(BaseModel):
    id: int = Field(description="The ID of the ticket being classified")
    department: DepartmentType = Field(description="The department responsible for the ticket")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score of the classification from 0 to 1")
    reasoning: str = Field(description="A short explanation (1-2 sentences) of why this department was chosen")

class TicketClassificationList(BaseModel):
    classifications: List[TicketClassification]
