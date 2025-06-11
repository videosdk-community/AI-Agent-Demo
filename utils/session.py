from videosdk.agents import Agent, AgentSession, RealTimePipeline
from typing import Dict, Any

# Global store for active agent sessions
active_sessions: Dict[str, AgentSession] = {}

def create_session(agent: Agent, pipeline: RealTimePipeline, context: Dict[str, Any]) -> AgentSession:
    """Creates an AgentSession"""
    return AgentSession(
        agent=agent,
        pipeline=pipeline, 
        context=context,
    ) 