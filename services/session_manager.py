from typing import Dict, Optional
from videosdk.agents import AgentSession


class SessionManager:
    """Manages active agent sessions across meetings."""
    
    def __init__(self):
        """Initialize the session manager with an empty sessions store."""
        self._active_sessions: Dict[str, AgentSession] = {}
    
    def add_session(self, meeting_id: str, session: AgentSession) -> None:
        """
        Add a new agent session for a meeting.
        
        Args:
            meeting_id: Unique identifier for the meeting
            session: The agent session instance
        """
        self._active_sessions[meeting_id] = session
        print(f"[{meeting_id}] Agent session stored. Current active sessions: {list(self._active_sessions.keys())}")
    
    def get_session(self, meeting_id: str) -> Optional[AgentSession]:
        """
        Get an agent session by meeting ID.
        
        Args:
            meeting_id: Unique identifier for the meeting
            
        Returns:
            The agent session if found, None otherwise
        """
        return self._active_sessions.get(meeting_id)
    
    def remove_session(self, meeting_id: str) -> Optional[AgentSession]:
        """
        Remove and return an agent session by meeting ID.
        
        Args:
            meeting_id: Unique identifier for the meeting
            
        Returns:
            The removed agent session if found, None otherwise
        """
        session = self._active_sessions.pop(meeting_id, None)
        if session:
            print(f"[{meeting_id}] Session removed from active_sessions.")
        else:
            print(f"[{meeting_id}] No session found in active_sessions.")
        return session
    
    def has_session(self, meeting_id: str) -> bool:
        """
        Check if a session exists for a meeting.
        
        Args:
            meeting_id: Unique identifier for the meeting
            
        Returns:
            True if session exists, False otherwise
        """
        return meeting_id in self._active_sessions
    
    def get_active_sessions(self) -> Dict[str, AgentSession]:
        """
        Get all active sessions.
        
        Returns:
            Dictionary of meeting_id to AgentSession
        """
        return self._active_sessions.copy()
    
    def clear_all_sessions(self) -> int:
        """
        Clear all active sessions.
        
        Returns:
            Number of sessions that were cleared
        """
        count = len(self._active_sessions)
        self._active_sessions.clear()
        print(f"Cleared {count} active sessions.")
        return count


# Global session manager instance
session_manager = SessionManager() 