from fastapi import APIRouter, BackgroundTasks
from models import (
    MeetingReqConfig, 
    LeaveAgentReqConfig,
    AgentJoinResponse,
    AgentLeaveResponse,
    HealthCheckResponse
)
from services import AgentService

router = APIRouter()


@router.post("/join-agent", response_model=AgentJoinResponse)
async def join_agent(req: MeetingReqConfig, bg_tasks: BackgroundTasks):
    """
    Join an AI agent to a meeting.
    
    Args:
        req: Meeting configuration with all necessary parameters
        bg_tasks: FastAPI background tasks to run the agent session
        
    Returns:
        Response indicating the agent joining process has been initiated
    """
    # Check if agent is already in the meeting
    if AgentService.check_existing_session(req.meeting_id):
        print(f"Agent joining meeting {req.meeting_id} which might already have an active agent. A new one will be started.")
    
    # Start agent session in background
    bg_tasks.add_task(AgentService.start_agent_session, req)
    
    return AgentJoinResponse(
        message=f"AI agent joining process initiated for meeting {req.meeting_id}",
        meeting_id=req.meeting_id,
        status="initiated"
    )


@router.post("/leave-agent", response_model=AgentLeaveResponse)
async def leave_agent(req: LeaveAgentReqConfig):
    """
    Remove an AI agent from a meeting.
    
    Args:
        req: Request containing the meeting ID
        
    Returns:
        Response indicating the operation status
    """
    result = AgentService.stop_agent_session(req.meeting_id)
    
    return AgentLeaveResponse(
        status=result["status"],
        meeting_id=result["meeting_id"],
        message=result["message"]
    )


@router.get("/test", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint to verify server is running.
    
    Returns:
        Simple health check response
    """
    return HealthCheckResponse(
        message="Server is running!",
        status="healthy"
    )


@router.get("/sessions/{meeting_id}")
async def get_session_info(meeting_id: str):
    """
    Get information about an agent session.
    
    Args:
        meeting_id: Unique identifier for the meeting
        
    Returns:
        Session information
    """
    return AgentService.get_session_info(meeting_id)


@router.get("/sessions")
async def list_active_sessions():
    """
    List all active agent sessions.
    
    Returns:
        List of active session IDs
    """
    from services import session_manager
    active_sessions = session_manager.get_active_sessions()
    
    return {
        "active_sessions": list(active_sessions.keys()),
        "count": len(active_sessions)
    } 