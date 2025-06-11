from pydantic import BaseModel
from typing import Optional

class TravelBookingRequest(BaseModel):
    meeting_id: str
    token: str
    model: str
    voice: str
    personality: str
    system_prompt: str
    temperature: float = 0.7
    topP: float = 0.9
    topK: int = 1

class LeaveAgentReqConfig(BaseModel):
    meeting_id: str 