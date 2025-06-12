from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from videosdk.agents import Agent, AgentSession, CascadingPipeline, function_tool, WorkerJob, MCPServerStdio, MCPServerHTTP, ConversationFlow, ChatRole
from videosdk.plugins.google import GeminiRealtime, GeminiLiveConfig
from videosdk.plugins.openai import OpenAILLM, OpenAITTS, OpenAISTT
# from videosdk.plugins.silero import SileroVAD
# from videosdk.plugins.turn_detector import TurnDetector
import os
import sys
import uvicorn
from dotenv import load_dotenv
import asyncio
from typing import Dict, AsyncIterator
import traceback
from pathlib import Path
from doc_rag_handler import search_hr_policy_knowledge
load_dotenv()

port = int(os.getenv("PORT", 8000)) # Use environment variable for port, default to 8000
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True, # More common for public APIs not relying on browser cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global store for active agent sessions ---
# We'll map meeting_id to the AgentSession instance
active_sessions: Dict[str, AgentSession] = {}
# --- ---

class MyVoiceAgent(Agent):
    def __init__(self, system_prompt: str, personality: str):
        # mcp_script = Path(__file__).parent / "mcp_studio.py"
        mcp_script_weather = Path(__file__).parent / "mcp_weather.py"
        # mcp_servers = [
        #     MCPServerStdio(
        #     command=sys.executable,
        #     args=[str(mcp_script_weather)],
        #     client_session_timeout_seconds=30
        # ),
        #     MCPServerHTTP(
        #         url=os.getenv("ZAPIER_WEBHOOK_URL")
        #     )
        # ]
        super().__init__(
            instructions=system_prompt,
            # mcp_servers=mcp_servers
        )
        self.personality = personality

    async def on_enter(self) -> None:
        await self.session.say(f"Hey, How can I help you today?")
    
    async def on_exit(self) -> None:
        await self.session.say("Goodbye!")
        

    @function_tool
    async def end_call(self) -> None:
        """End the call upon request by the user"""
        await self.session.say("Goodbye!")
        await asyncio.sleep(1)
        await self.session.leave()
  

class MyConversationFlow(ConversationFlow):
    def __init__(self, agent, stt=None, llm=None, tts=None):
        super().__init__(agent, stt, llm, tts)

    async def run(self, transcript: str) -> AsyncIterator[str]:
        """Main conversation loop: handle a user turn."""
        await self.on_turn_start(transcript)
        
        
        processed_transcript = transcript.lower().strip()

        retrieved_context = None  # Initialize to None
        try:
            # Perform RAG retrieval
            retrieved_context = await search_hr_policy_knowledge(processed_transcript)
        except Exception as e:
            print(f"[{self.agent.session.context.get('meetingId', 'UnknownMeeting')}] Error during RAG retrieval: {e}")
            # Optionally, you could inform the user or LLM that context retrieval failed
            # self.agent.chat_context.add_message(role=ChatRole.SYSTEM, content="[System: HR policy context retrieval failed.]")

        # Add retrieved context to chat history if available
        if retrieved_context:
            self.agent.chat_context.add_message(role=ChatRole.SYSTEM, content=f"Context from HR Policy Manual: {retrieved_context}")

        self.agent.chat_context.add_message(role=ChatRole.USER, content=processed_transcript)
        
        async for response_chunk in self.process_with_llm():
            yield response_chunk

        await self.on_turn_end()

    async def on_turn_start(self, transcript: str) -> None:
        """Called at the start of a user turn."""
        self.is_turn_active = True

    async def on_turn_end(self) -> None:
        """Called at the end of a user turn."""
        self.is_turn_active = False

class MeetingReqConfig(BaseModel):
    meeting_id: str
    token: str
    model: str
    voice: str
    personality: str
    temperature: float
    system_prompt: str
    topP: float
    topK: float


class LeaveAgentReqConfig(BaseModel): # For the leave endpoint
    meeting_id: str

async def server_operations(req: MeetingReqConfig):
    print(f"req body : {req}")
    meeting_id = req.meeting_id
    print(f"[{meeting_id}] Initializing agent operations...")
    

    # Use all values from the request
    # model = GeminiRealtime(
    #     model=req.model,
    #     api_key=os.getenv("GOOGLE_API_KEY"),
    #     config=GeminiLiveConfig(
    #         voice=req.voice,
    #         response_modalities=["AUDIO"],
    #         temperature=req.temperature,
    #         top_p=req.topP,
    #         top_k=int(req.topK),
    #     )
    # )

    # pipeline = RealTimePipeline(model=model)
    agent = MyVoiceAgent(
        system_prompt=req.system_prompt, # Pass system_prompt from req
        personality=req.personality    # Pass personality from req
    )
    conversation_flow = MyConversationFlow(agent)
    pipeline = CascadingPipeline(
        stt= OpenAISTT(api_key=os.getenv("OPENAI_API_KEY")),
        llm=OpenAILLM(api_key=os.getenv("OPENAI_API_KEY")),
        tts=OpenAITTS(api_key=os.getenv("OPENAI_API_KEY")),
        # vad=SileroVAD(),
        # turn_detector=TurnDetector(threshold=0.8)
    )

    # Pass system_prompt and personality in the context if your agent uses them
    session = AgentSession(
        agent=MyVoiceAgent(req.system_prompt, req.personality),
        pipeline=pipeline,
        conversation_flow=conversation_flow,
        context={
            "meetingId": meeting_id,
            "name": "My Agent",
            "videosdk_auth": req.token,
        }
    )

    active_sessions[meeting_id] = session
    print(f"[{meeting_id}] Agent session stored. Current active sessions: {list(active_sessions.keys())}")

    try:
        print(f"[{meeting_id}] Agent attempting to start...")
        await session.start()
        print(f"[{meeting_id}] Agent session.start() completed normally.")
    except Exception as ex:
        print(f"[{meeting_id}] [ERROR] in agent session: {ex}")
        if active_sessions.get(meeting_id) is session:
            active_sessions.pop(meeting_id, None)
            try:
                if hasattr(session, 'leave') and session.leave is not None:
                    await session.leave()
            except Exception as leave_ex:
                print(f"[{meeting_id}] [ERROR] during cleanup after failed start: {leave_ex}")
    finally:
        print(f"[{meeting_id}] Server operations completed for this session.")


@app.post("/join-agent")
async def join_agent(req: MeetingReqConfig, bg_tasks: BackgroundTasks):
    if req.meeting_id in active_sessions:
        # Optional: decide how to handle re-joining an already active meeting
        # For now, let's allow it, the new agent will replace the old one in `active_sessions`
        # The old background task will eventually complete and clean itself up.
        print(f"Agent joining meeting {req.meeting_id} which might already have an active agent. A new one will be started.")

    bg_tasks.add_task(server_operations, req)
    return {"message": f"AI agent joining process initiated for meeting {req.meeting_id}"}


# --- NEW/MODIFIED ENDPOINT ---
@app.post("/leave-agent")
async def leave_agent(req: LeaveAgentReqConfig):
    meeting_id = req.meeting_id
    print(f"[{meeting_id}] Received /leave-agent request.")

    session = active_sessions.pop(meeting_id, None)

    if session:
        print(f"[{meeting_id}] Session removed from active_sessions.")
        return {
            "status": "removed",
            "meeting_id": meeting_id,
            "message": f"Session for meeting {meeting_id} has been removed."
        }
    else:
        print(f"[{meeting_id}] No session found in active_sessions.")
        return {
            "status": "not_found",
            "meeting_id": meeting_id,
            "message": f"No session found for meeting {meeting_id}."
        }
# --- END NEW/MODIFIED ENDPOINT ---


@app.get("/test")
async def test():
    return {"message": "Server is running!"}


if __name__ == "__main__":
    # The uvicorn.run in the original question was "main:app" and port 8001
    # Assuming the file is named main.py
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=True) # Added reload=True for dev