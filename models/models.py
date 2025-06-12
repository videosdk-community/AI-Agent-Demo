from pydantic import BaseModel, Field
from typing import Optional


class MeetingReqConfig(BaseModel):
    """Request model for joining an agent to a meeting."""
    meeting_id: str = Field(..., description="The unique identifier for the meeting")
    token: str = Field(..., description="VideoSDK authentication token")
    model: str = Field(..., description="AI model to use for the agent")
    voice: str = Field(..., description="Voice profile for the agent")
    personality: str = Field(..., description="Personality type for the agent")
    temperature: float = Field(..., ge=0.0, le=2.0, description="Temperature for AI responses")
    system_prompt: str = Field(..., description="System prompt for the agent")
    topP: float = Field(..., ge=0.0, le=1.0, description="Top-p parameter for AI responses")
    topK: float = Field(..., ge=0.0, description="Top-k parameter for AI responses")


class LeaveAgentReqConfig(BaseModel):
    """Request model for removing an agent from a meeting."""
    meeting_id: str = Field(..., description="The unique identifier for the meeting")


class AgentJoinResponse(BaseModel):
    """Response model for agent join operations."""
    message: str
    meeting_id: str
    status: str = "initiated"


class AgentLeaveResponse(BaseModel):
    """Response model for agent leave operations."""
    status: str
    meeting_id: str
    message: str


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint."""
    message: str
    status: str = "healthy" 