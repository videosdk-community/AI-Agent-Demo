# from fastapi.middleware.cors import CORSMiddleware
# from fastapi import FastAPI, BackgroundTasks
# from pydantic import BaseModel
# from videosdk.agents import Agent, AgentSession, RealTimePipeline, function_tool, MCPServerStdio, MCPServerHTTP
# from videosdk.plugins.google import GeminiRealtime, GeminiLiveConfig
# import os
# import sys
# import uvicorn
# from dotenv import load_dotenv
# import asyncio
# from typing import Dict
# import traceback
# from pathlib import Path
# load_dotenv()

# port = int(os.getenv("PORT", 8000)) # Use environment variable for port, default to 8000
# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True, # More common for public APIs not relying on browser cookies
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # --- Global store for active agent sessions ---
# # We'll map meeting_id to the AgentSession instance
# active_sessions: Dict[str, AgentSession] = {}
# # --- ---

# class MyVoiceAgent(Agent):
#     def __init__(self, system_prompt: str, personality: str):
#         # mcp_script = Path(__file__).parent / "mcp_studio.py"
#         mcp_script_weather = Path(__file__).parent / "mcp_weather.py"
#         # mcp_servers = [
#         #     MCPServerStdio(
#         #     command=sys.executable,
#         #     args=[str(mcp_script_weather)],
#         #     client_session_timeout_seconds=30
#         # ),
#         #     MCPServerHTTP(
#         #         url=os.getenv("ZAPIER_WEBHOOK_URL")
#         #     )
#         # ]
#         super().__init__(
#             instructions=system_prompt,
#             # mcp_servers=mcp_servers
#         )
#         self.personality = personality

#     async def on_enter(self) -> None:
#         await self.session.say(f"Hey, How can I help you today?")
    
#     async def on_exit(self) -> None:
#         await self.session.say("Goodbye!")
        

#     @function_tool
#     async def end_call(self) -> None:
#         """End the call upon request by the user"""
#         await self.session.say("Goodbye!")
#         await asyncio.sleep(1)
#         await self.session.leave()
  

# class MeetingReqConfig(BaseModel):
#     meeting_id: str
#     token: str
#     model: str
#     voice: str
#     personality: str
#     temperature: float
#     system_prompt: str
#     topP: float
#     topK: float


# class LeaveAgentReqConfig(BaseModel): # For the leave endpoint
#     meeting_id: str

# async def server_operations(req: MeetingReqConfig):
#     print(f"req body : {req}")
#     meeting_id = req.meeting_id
#     print(f"[{meeting_id}] Initializing agent operations...")
    

#     # Use all values from the request
#     model = GeminiRealtime(
#         model=req.model,
#         api_key=os.getenv("GOOGLE_API_KEY"),
#         config=GeminiLiveConfig(
#             voice=req.voice,
#             response_modalities=["AUDIO"],
#             temperature=req.temperature,
#             top_p=req.topP,
#             top_k=int(req.topK),
#         )
#     )

#     pipeline = RealTimePipeline(model=model)

#     # Pass system_prompt and personality in the context if your agent uses them
#     session = AgentSession(
#         agent=MyVoiceAgent(req.system_prompt, req.personality),
#         pipeline=pipeline,
#         context={
#             "meetingId": meeting_id,
#             "name": "Gemini Agent",
#             "videosdk_auth": req.token,
#         }
#     )

#     active_sessions[meeting_id] = session
#     print(f"[{meeting_id}] Agent session stored. Current active sessions: {list(active_sessions.keys())}")

#     try:
#         print(f"[{meeting_id}] Agent attempting to start...")
#         await session.start()
#         print(f"[{meeting_id}] Agent session.start() completed normally.")
#     except Exception as ex:
#         print(f"[{meeting_id}] [ERROR] in agent session: {ex}")
#         if active_sessions.get(meeting_id) is session:
#             active_sessions.pop(meeting_id, None)
#             try:
#                 if hasattr(session, 'leave') and session.leave is not None:
#                     await session.leave()
#             except Exception as leave_ex:
#                 print(f"[{meeting_id}] [ERROR] during cleanup after failed start: {leave_ex}")
#     finally:
#         print(f"[{meeting_id}] Server operations completed for this session.")


# @app.post("/join-agent")
# async def join_agent(req: MeetingReqConfig, bg_tasks: BackgroundTasks):
#     if req.meeting_id in active_sessions:
#         # Optional: decide how to handle re-joining an already active meeting
#         # For now, let's allow it, the new agent will replace the old one in `active_sessions`
#         # The old background task will eventually complete and clean itself up.
#         print(f"Agent joining meeting {req.meeting_id} which might already have an active agent. A new one will be started.")

#     bg_tasks.add_task(server_operations, req)
#     return {"message": f"AI agent joining process initiated for meeting {req.meeting_id}"}


# # --- NEW/MODIFIED ENDPOINT ---
# @app.post("/leave-agent")
# async def leave_agent(req: LeaveAgentReqConfig):
#     meeting_id = req.meeting_id
#     print(f"[{meeting_id}] Received /leave-agent request.")

#     session = active_sessions.pop(meeting_id, None)

#     if session:
#         print(f"[{meeting_id}] Session removed from active_sessions.")
#         return {
#             "status": "removed",
#             "meeting_id": meeting_id,
#             "message": f"Session for meeting {meeting_id} has been removed."
#         }
#     else:
#         print(f"[{meeting_id}] No session found in active_sessions.")
#         return {
#             "status": "not_found",
#             "meeting_id": meeting_id,
#             "message": f"No session found for meeting {meeting_id}."
#         }
# # --- END NEW/MODIFIED ENDPOINT ---


# @app.get("/test")
# async def test():
#     return {"message": "Server is running!"}


# if __name__ == "__main__":
#     # The uvicorn.run in the original question was "main:app" and port 8001
#     # Assuming the file is named main.py
#     uvicorn.run("main:app", host="127.0.0.1", port=port, reload=True) # Added reload=True for dev

# server.py

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from videosdk.agents import Agent, AgentSession, RealTimePipeline, function_tool, AgentCard, A2AMessage
from videosdk.plugins.google import GeminiRealtime, GeminiLiveConfig
import os
import uvicorn
from dotenv import load_dotenv
import asyncio
from typing import Dict, Any, Optional, Tuple
import traceback
from pathlib import Path # Required if you're using local MCP servers or external files

# --- Load environment variables ---
load_dotenv()

port = int(os.getenv("PORT", 8000))
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global store for active agent sessions ---
# This dictionary will map meeting_id to a dict containing both customer and loan agent sessions.
# Example: { "meeting_id_1": {"customer": AgentSession, "loan": AgentSession} }
active_sessions: Dict[str, Dict[str, AgentSession]] = {}
# --- ---

# --- Agent Definitions ---

class CustomerServiceAgent(Agent):
    def __init__(self, system_prompt: str):
        super().__init__(
            agent_id="customer_service_1", # Unique ID for A2A registry
            instructions=system_prompt,
            # If you were using MCP servers for this agent, you'd add them here:
            # mcp_servers=[
            #     MCPServerStdio(command=sys.executable, args=[str(Path(__file__).parent / "mcp_weather.py")], client_session_timeout_seconds=30),
            #     MCPServerHTTP(url=os.getenv("ZAPIER_WEBHOOK_URL"))
            # ]
        )
        self.agent_id = "customer_service_1"  # Unique ID for A2A registry

    # Function tool for ending the call, remains with the customer-facing agent
    @function_tool
    async def end_call(self) -> None:
        """End the call upon request by the user"""
        print("[Customer Agent] User requested to end call.")
        await self.session.say("Goodbye!")
        await asyncio.sleep(1)
        await self.session.leave()

    @function_tool
    async def forward_to_specialist(self, query: str, domain: str) -> Dict[str, Any]:
        """
        Forwards a user query to a specialized agent based on domain.
        Args:
            query: The user's query that needs specialist attention.
            domain: The domain of the specialist (e.g., 'loan', 'tech_support').
        """
        if not hasattr(self, 'a2a') or not self.a2a: # Ensure A2A is initialized (should be in on_enter)
            print("[Customer Agent] A2A not initialized for this agent during forward_to_specialist call.")
            await self.session.say("I'm having trouble connecting to my internal team. Please try again later.")
            return {"error": "A2A not initialized for this agent."}

        print(f"[Customer Agent] Attempting to forward query: '{query}' to domain: '{domain}'")
        specialists = self.a2a.registry.find_agents_by_domain(domain)
        id_of_target_agent = specialists[0] if specialists else None
        
        if not id_of_target_agent:
            print(f"[Customer Agent] No specialist found for domain {domain}")
            await self.session.say(f"I'm sorry, I cannot find a specialist for {domain} at the moment. Can I help with anything else?")
            return {"error": f"no specialist found for domain {domain}"}

        # Send message to the specialist
        await self.a2a.send_message(
            to_agent=id_of_target_agent,
            message_type="specialist_query", # A custom message type for this communication
            content={"query": query, "from_agent_id": self.agent_id} # Pass sender ID for robust response routing
        )
        message_to_user = f"Let me get that information for you from our {domain} specialist..."
        await self.session.say(message_to_user) # Inform the user that the query is being forwarded
        return {
            "status": "forwarded",
            "specialist": id_of_target_agent,
            "message": message_to_user
        }

    async def handle_specialist_response(self, message: A2AMessage) -> None:
        """
        Handles responses coming back from a specialist agent.
        This method is registered to listen for 'specialist_response' A2A messages.
        """
        response = message.content.get("response")
        if response:
            print(f"[Customer Agent] Received specialist response from {message.from_agent_id}: {response}")
            await asyncio.sleep(0.5) # Add a small delay for more natural speech flow
            
            # Formulate a natural reply, possibly including the specialist's domain
            domain = message.from_agent_card.domain if message.from_agent_card else "specialist"
            prompt = f"The {domain} specialist has responded: {response}"
            
            # Try different methods to relay the response, prioritizing `say` for audio agents
            try:
                await self.session.say(response) # Directly vocalize the response
            except Exception as e:
                print(f"[Customer Agent] Error with self.session.say: {e}. Trying send_text_message.")
                try:
                    await self.session.pipeline.send_text_message(prompt)
                except Exception as e2:
                    print(f"[Customer Agent] Error with send_text_message: {e2}. Giving up on relay.")
        else:
            print(f"[Customer Agent] Received empty specialist response from {message.from_agent_id}")

    async def on_enter(self):
        print("[Customer Agent] CustomerServiceAgent entered session.")
        # Register this agent with the A2A system
        await self.register_a2a(AgentCard(
            id=self.agent_id, # Use the agent_id defined in __init__
            name="Customer Service Agent",
            domain="customer_service", # This agent handles general customer service
            capabilities=["query_handling", "specialist_coordination", "call_control"],
            description="Handles general customer queries and coordinates with specialists"
        ))
        
        # Initial greeting to the user
        await self.session.say("Hello! I am your customer service agent. How can I help you today?")
        
        # Register the A2A message listener for specialist responses
        self.a2a.on_message("specialist_response", self.handle_specialist_response)
        print(f"[Customer Agent] A2A registered. Listening for 'specialist_response' messages.")

    async def on_exit(self):
        print("[Customer Agent] CustomerServiceAgent left the session.")
        # Ensure unregistration on exit for cleanup
        if hasattr(self, 'a2a') and self.a2a:
            await self.unregister_a2a()

class LoanAgent(Agent):
    def __init__(self):
        super().__init__(
            agent_id="loan_specialist_1", # Unique ID for A2A registry
            instructions=(
                "You are a highly specialized loan expert at a bank. "
                "You receive direct queries related to loans. "
                "Provide accurate, concise, and helpful information about loans including interest rates, terms, and requirements. "
                "You can discuss personal loans, car loans, home loans, and business loans. "
                "Keep your responses to 2-3 sentences and focus purely on providing the requested loan information. "
                "Do NOT attempt to act as a general customer service agent or ask follow-up questions to the customer. "
                "Your goal is to provide the requested information so the customer service agent can relay it."
            )
        )
        self.agent_id = "loan_specialist_1"  # Unique ID for A2A registry
        # Store the ID of the agent that sent the last query, to send response back
        self.current_requesting_agent_id: Optional[str] = None

    async def handle_specialist_query(self, message: A2AMessage):
        """
        Receives a query from another agent (e.g., CustomerServiceAgent).
        This method is registered to listen for 'specialist_query' A2A messages.
        """
        query = message.content.get("query")
        # Use message.content.get("from_agent_id") for robust routing back, if passed
        requesting_agent_id_from_content = message.content.get("from_agent_id")
        self.current_requesting_agent_id = requesting_agent_id_from_content or message.from_agent_id

        if query:
            print(f"[Loan Agent] Received specialist query from {self.current_requesting_agent_id}: '{query}'")
            # Send the query to its own LLM for processing.
            # The response from the LLM will then trigger handle_model_response.
            await self.session.pipeline.send_text_message(query)
        else:
            print(f"[Loan Agent] Received empty specialist query from {self.current_requesting_agent_id}")
            # Optionally, send an error response back
            if self.current_requesting_agent_id and hasattr(self, 'a2a') and self.a2a:
                await self.a2a.send_message(
                    to_agent=self.current_requesting_agent_id,
                    message_type="specialist_response",
                    content={"response": "I received an empty query. Please provide more details."}
                )

    async def handle_model_response(self, message: A2AMessage):
        """
        Handles the response from the LoanAgent's own LLM after processing a query.
        This response then needs to be sent back to the original requesting agent.
        """
        response = message.content.get("response")
        
        requesting_agent = self.current_requesting_agent_id
        
        if response and requesting_agent and hasattr(self, 'a2a') and self.a2a:
            print(f"[Loan Agent] Generated response: '{response}'. Sending back to {requesting_agent}")
            await self.a2a.send_message(
                to_agent=requesting_agent,
                message_type="specialist_response", # Custom message type for the response
                content={"response": response}
            )
            # Clear the requesting agent id after sending response
            self.current_requesting_agent_id = None
        else:
            print(f"[Loan Agent] Could not send response. Response: {response}, Requesting Agent: {requesting_agent}, A2A Status: {hasattr(self, 'a2a') and self.a2a}")

    async def on_enter(self):
        print("[Loan Agent] LoanAgent entered session (running in background).")
        # Register this specialist agent with the A2A system
        await self.register_a2a(AgentCard(
            id=self.agent_id,
            name="Loan Specialist Agent",
            domain="loan", # This agent specializes in 'loan' domain
            capabilities=["loan_consultation", "loan_information", "interest_rates"],
            description="Handles loan queries and provides expert information"
        ))
        
        # Register A2A message listeners for incoming queries and internal model responses
        self.a2a.on_message("specialist_query", self.handle_specialist_query)
        self.a2a.on_message("model_response", self.handle_model_response) # Listen for its own LLM's responses
        print(f"[Loan Agent] A2A registered. Listening for 'specialist_query' and 'model_response' messages.")

    async def on_exit(self):
        print("[Loan Agent] LoanAgent left the session.")
        if hasattr(self, 'a2a') and self.a2a:
            await self.unregister_a2a()

# --- Session and Pipeline Management ---

def create_pipeline(llm_model: str, api_key: str, agent_type: str, voice: str = "Leda", temperature: float = 0.7, top_p: float = 0.9, top_k: int = 1) -> RealTimePipeline:
    """
    Creates a RealTimePipeline tailored for the agent's role.
    agent_type: 'customer' for audio interaction, 'specialist' for text-only.
    """
    if agent_type == "customer":
        model = GeminiRealtime(
            model=llm_model,
            api_key=api_key,
            config=GeminiLiveConfig(
                voice=voice,
                response_modalities=["AUDIO"],
                temperature=temperature,
                top_p=top_p,
                top_k=int(top_k),
            )
        )
    elif agent_type == "specialist":
        model = GeminiRealtime(
            model=llm_model,
            api_key=api_key,
            config=GeminiLiveConfig(
                response_modalities=["TEXT"]
            )
        )
    else:
        raise ValueError(f"Unknown agent_type: {agent_type}. Must be 'customer' or 'specialist'.")

    return RealTimePipeline(model=model)

def create_session(agent: Agent, pipeline: RealTimePipeline, context: Dict[str, Any]) -> AgentSession:
    """Creates an AgentSession."""
    return AgentSession(agent=agent, pipeline=pipeline, context=context)

# --- FastAPI Models ---

class MeetingReqConfig(BaseModel):
    meeting_id: str
    token: str # VideoSDK authentication token
    model: str # LLM model name (e.g., "gemini-2.0-flash-live-001")
    voice: str # Voice for the customer agent (e.g., "Leda")
    personality: str # Personality for the customer agent (not used in this example, but can be extended
    system_prompt: str # Specific prompt for the customer agent
    temperature: float = 0.7 # Default values for optional fields
    topP: float = 0.9
    topK: float = 1.0

class LeaveAgentReqConfig(BaseModel):
    meeting_id: str

# --- FastAPI Endpoints Logic ---

async def start_a2a_agents_for_meeting(req: MeetingReqConfig):
    meeting_id = req.meeting_id
    print(f"[{meeting_id}] Initializing A2A agent operations...")

    google_api_key = os.getenv("GOOGLE_API_KEY")

    if not google_api_key:
        print(f"[{meeting_id}] ERROR: GOOGLE_API_KEY not set in environment variables. Aborting agent start.")
        # Ensure cleanup if error occurs before session objects are fully formed
        active_sessions.pop(meeting_id, None)
        return

    customer_session: Optional[AgentSession] = None
    loan_session: Optional[AgentSession] = None

    try:
        # --- Customer Service Agent Setup ---
        customer_agent = CustomerServiceAgent(system_prompt=req.system_prompt)
        customer_pipeline = create_pipeline(
            llm_model=req.model,
            api_key=google_api_key,
            agent_type="customer",
            voice=req.voice,
            temperature=req.temperature,
            top_p=req.topP,
            top_k=req.topK
        )
        customer_session = create_session(customer_agent, customer_pipeline, {
            "name": "Customer Service Assistant",
            "meetingId": meeting_id,
            "videosdk_auth": req.token,
            "join_meeting": True # Customer agent joins the meeting
        })

        # --- Loan Specialist Agent Setup ---
        loan_agent = LoanAgent() # Loan agent uses its own fixed instructions
        loan_pipeline = create_pipeline(
            llm_model=req.model, # Can use the same LLM model, or a different one
            api_key=google_api_key,
            agent_type="specialist" # Text-only pipeline for specialists
        )
        loan_session = create_session(loan_agent, loan_pipeline, {
            "name": "Loan Specialist",
            "meetingId": meeting_id, # Can be the same, but agent doesn't join the meeting
            "videosdk_auth": req.token,
            "join_meeting": False # Loan agent runs in background
        })

        # Store both sessions in the global dictionary BEFORE starting them
        # This prevents race conditions if another request tries to stop them quickly
        active_sessions[meeting_id] = {
            "customer": customer_session,
            "loan": loan_session
        }
        print(f"[{meeting_id}] Agent sessions stored. Current active meetings: {list(active_sessions.keys())}")

        print(f"[{meeting_id}] Agents attempting to start...")
        # Start both sessions concurrently.
        # This will block until the agents finish (e.g., meeting ends, or session.leave() is called).
        await asyncio.gather(
            customer_session.start(),
            loan_session.start()
        )
        print(f"[{meeting_id}] All agent sessions for this meeting have completed their lifecycle.")

    except Exception as ex:
        print(f"[{meeting_id}] [ERROR] during A2A agent setup or runtime: {ex}")
        traceback.print_exc() # Print full traceback for debugging
    finally:
        # Ensure sessions are removed from active_sessions once their lifecycle is complete
        # This handles cases where `session.start()` completes naturally or due to an error.
        if meeting_id in active_sessions:
            print(f"[{meeting_id}] Removing sessions from active_sessions map due to completion/error.")
            sessions_to_close = active_sessions.pop(meeting_id)
            for agent_type, session_obj in sessions_to_close.items():
                if session_obj:
                    try:
                        # Ensure close is called, even if start failed or completed
                        if hasattr(session_obj, 'close') and session_obj.close is not None:
                            await session_obj.close()
                        print(f"[{meeting_id}] Closed {agent_type} agent session during final cleanup.")
                    except Exception as close_ex:
                        print(f"[{meeting_id}] ERROR during final cleanup closing {agent_type} session: {close_ex}")
        print(f"[{meeting_id}] Server operations for this meeting completed.")


# --- FastAPI Endpoints ---

@app.post("/join-agent")
async def join_agent(req: MeetingReqConfig, bg_tasks: BackgroundTasks):
    if req.meeting_id in active_sessions:
        print(f"[{req.meeting_id}] Agent already exists. Removing existing sessions to start new ones.")
        existing_sessions = active_sessions.pop(req.meeting_id, None)
        if existing_sessions:
            # Add a background task to clean up the old sessions
            bg_tasks.add_task(
                asyncio.gather,
                *(session_obj.close() for session_obj in existing_sessions.values())
            )
            print(f"[{req.meeting_id}] Old agent sessions scheduled for cleanup.")
        # Give a small moment for previous cleanup tasks to potentially begin
        await asyncio.sleep(0.1)

    bg_tasks.add_task(start_a2a_agents_for_meeting, req)
    return {"message": f"AI A2A agents joining process initiated for meeting {req.meeting_id}"}


@app.post("/leave-agent")
async def leave_agent(req: LeaveAgentReqConfig):
    meeting_id = req.meeting_id
    print(f"[{meeting_id}] Received /leave-agent request.")

    # Remove sessions from active_sessions immediately to prevent new operations on them
    sessions_for_meeting = active_sessions.pop(meeting_id, None)

    if sessions_for_meeting:
        print(f"[{meeting_id}] Sessions found. Attempting to close all agents for this meeting...")
        close_tasks = []
        for agent_type, session_obj in sessions_for_meeting.items():
            if session_obj:
                print(f"[{meeting_id}] Scheduling {agent_type} agent session for close...")
                close_tasks.append(session_obj.close())
        
        try:
            # Use return_exceptions=True to ensure all tasks are attempted even if one fails
            await asyncio.gather(*close_tasks, return_exceptions=True)
            print(f"[{meeting_id}] All agent sessions for meeting {meeting_id} closed.")
            return {
                "status": "closed",
                "meeting_id": meeting_id,
                "message": f"All A2A agent sessions for meeting {meeting_id} have been closed."
            }
        except Exception as e:
            print(f"[{meeting_id}] ERROR during closing agents: {e}")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Error closing agents: {e}")
    else:
        print(f"[{meeting_id}] No active sessions found for meeting {meeting_id}.")
        raise HTTPException(status_code=404, detail=f"No active A2A agent sessions found for meeting {meeting_id}.")


@app.get("/test")
async def test():
    """A simple endpoint to check if the server is running."""
    print("Test endpoint hit!")
    return {"message": "VideoSDK A2A Agent Server is running!"}

# --- Main execution block ---
if __name__ == "__main__":
    # Ensure `server:app` maps to this file (server.py) and the FastAPI app instance `app`
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True, log_level="info")