import os
import traceback
from videosdk.agents import AgentSession
from agents import MyVoiceAgent, MyConversationFlow
from models import MeetingReqConfig
from .session_manager import session_manager
from .pipeline_factory import PipelineFactory


class AgentService:
    """Service class for handling agent operations and business logic."""
    
    @staticmethod
    async def start_agent_session(config: MeetingReqConfig) -> None:
        """
        Start an agent session for a meeting.
        
        Args:
            config: Meeting configuration containing all necessary parameters
        """
        meeting_id = config.meeting_id
        print(f"[{meeting_id}] Initializing agent operations...")
        
        try:
            # Set VideoSDK auth token as environment variable if provided
            if config.token:
                os.environ["VIDEOSDK_AUTH_TOKEN"] = config.token
            
            # Create agent components
            agent = MyVoiceAgent(
                system_prompt=config.system_prompt,
                personality=config.personality
            )
            
            conversation_flow = MyConversationFlow(agent)
            pipeline = PipelineFactory.get_default_pipeline(config)
            
            # Create agent session
            session = AgentSession(
                agent=MyVoiceAgent(config.system_prompt, config.personality),
                pipeline=pipeline,
                conversation_flow=conversation_flow,
                context={
                    "meetingId": meeting_id,
                    "name": "My Agent",
                    "videosdk_auth": config.token,
                }
            )
            
            # Store session
            session_manager.add_session(meeting_id, session)
            
            # Start the session
            print(f"[{meeting_id}] Agent attempting to start...")
            await session.start()
            print(f"[{meeting_id}] Agent session.start() completed normally.")
            
        except Exception as ex:
            print(f"[{meeting_id}] [ERROR] in agent session: {ex}")
            print(f"[{meeting_id}] Error traceback: {traceback.format_exc()}")
            
            # Cleanup on error
            stored_session = session_manager.get_session(meeting_id)
            if stored_session:
                session_manager.remove_session(meeting_id)
                try:
                    if hasattr(stored_session, 'leave') and stored_session.leave is not None:
                        await stored_session.leave()
                except Exception as leave_ex:
                    print(f"[{meeting_id}] [ERROR] during cleanup after failed start: {leave_ex}")
        
        finally:
            print(f"[{meeting_id}] Server operations completed for this session.")
    
    @staticmethod
    def stop_agent_session(meeting_id: str) -> dict:
        """
        Stop an agent session for a meeting.
        
        Args:
            meeting_id: Unique identifier for the meeting
            
        Returns:
            Dictionary with operation status and details
        """
        print(f"[{meeting_id}] Received stop agent session request.")
        
        session = session_manager.remove_session(meeting_id)
        
        if session:
            return {
                "status": "removed",
                "meeting_id": meeting_id,
                "message": f"Session for meeting {meeting_id} has been removed."
            }
        else:
            return {
                "status": "not_found",
                "meeting_id": meeting_id,
                "message": f"No session found for meeting {meeting_id}."
            }
    
    @staticmethod
    def check_existing_session(meeting_id: str) -> bool:
        """
        Check if an agent session already exists for a meeting.
        
        Args:
            meeting_id: Unique identifier for the meeting
            
        Returns:
            True if session exists, False otherwise
        """
        return session_manager.has_session(meeting_id)
    
    @staticmethod
    def get_session_info(meeting_id: str) -> dict:
        """
        Get information about an agent session.
        
        Args:
            meeting_id: Unique identifier for the meeting
            
        Returns:
            Dictionary with session information
        """
        session = session_manager.get_session(meeting_id)
        
        if session:
            return {
                "meeting_id": meeting_id,
                "status": "active",
                "context": session.context
            }
        else:
            return {
                "meeting_id": meeting_id,
                "status": "not_found"
            } 