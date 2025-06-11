# main.py - Modularized Travel A2A Server with Email Integration

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, BackgroundTasks, HTTPException
import uvicorn
import asyncio
from typing import Optional
import traceback

# Import modularized components
from config import PORT, GOOGLE_API_KEY
from models import TravelBookingRequest, LeaveAgentReqConfig
from utils import (
    create_main_pipeline, 
    create_specialist_pipeline, 
    create_session, 
    active_sessions
)
from agents import TravelAgent, FlightAgent, HotelAgent, EmailAgent

# --- FastAPI App Setup ---
app = FastAPI(title="Travel A2A Server with Email")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Agent Orchestration Logic ---

async def start_travel_agents_for_meeting(req: TravelBookingRequest):
    """Start all travel agents for a meeting"""
    meeting_id = req.meeting_id
    print(f"[{meeting_id}] Initializing Travel A2A agent operations...")

    if not GOOGLE_API_KEY:
        print(f"[{meeting_id}] ERROR: GOOGLE_API_KEY not set in environment variables.")
        active_sessions.pop(meeting_id, None)
        return

    travel_session: Optional = None
    flight_session: Optional = None
    hotel_session: Optional = None
    email_session: Optional = None

    try:
        # --- Main Travel Agent Setup ---
        travel_agent = TravelAgent(system_prompt=req.system_prompt)
        travel_pipeline = create_main_pipeline(
            llm_model=req.model,
            api_key=GOOGLE_API_KEY,
            voice=req.voice,
            temperature=req.temperature,
            top_p=req.topP,
            top_k=req.topK
        )
        travel_session = create_session(travel_agent, travel_pipeline, {
            "meetingId": meeting_id,
            "name": "Travel Agent",
            "videosdk_auth": req.token,
            "join_meeting": True,
        })

        # --- Flight Specialist Agent Setup ---
        flight_agent = FlightAgent()
        flight_pipeline = create_specialist_pipeline(req.model, GOOGLE_API_KEY)
        flight_session = create_session(flight_agent, flight_pipeline, {
            "join_meeting": False,
        })

        # --- Hotel Specialist Agent Setup ---
        hotel_agent = HotelAgent()
        hotel_pipeline = create_specialist_pipeline(req.model, GOOGLE_API_KEY)
        hotel_session = create_session(hotel_agent, hotel_pipeline, {
            "join_meeting": False,
        })

        # --- Email Specialist Agent Setup ---
        email_agent = EmailAgent()
        email_pipeline = create_specialist_pipeline(req.model, GOOGLE_API_KEY)
        email_session = create_session(email_agent, email_pipeline, {
            "join_meeting": False,
        })

        # Store main travel session
        active_sessions[meeting_id] = travel_session
        print(f"[{meeting_id}] Travel agent session stored. Current active sessions: {list(active_sessions.keys())}")

        print(f"[{meeting_id}] Starting specialist agents first...")
        # Start specialist agents first to ensure they register before main agent
        flight_task = asyncio.create_task(flight_session.start())
        hotel_task = asyncio.create_task(hotel_session.start())
        email_task = asyncio.create_task(email_session.start())
        
        # Give specialist agents time to register
        await asyncio.sleep(3)
        
        print(f"[{meeting_id}] Starting main travel agent...")
        travel_task = asyncio.create_task(travel_session.start())
        
        print(f"[{meeting_id}] All Travel A2A agents started and running...")
        
        # Wait for all to complete
        await asyncio.gather(
            travel_task, 
            flight_task, 
            hotel_task,
            email_task,
            return_exceptions=True
        )
        print(f"[{meeting_id}] Travel A2A agent sessions completed their lifecycle.")

    except Exception as ex:
        print(f"[{meeting_id}] [ERROR] during Travel A2A agent setup or runtime: {ex}")
        traceback.print_exc()
    finally:
        # Cleanup
        if meeting_id in active_sessions:
            print(f"[{meeting_id}] Session completed naturally - removing from active_sessions.")
            active_sessions.pop(meeting_id, None)
        else:
            print(f"[{meeting_id}] Session was already removed by leave-agent endpoint.")
        print(f"[{meeting_id}] Travel server operations completed for this session.")

# --- FastAPI Endpoints ---

@app.post("/join-agent")
async def join_agent(req: TravelBookingRequest, bg_tasks: BackgroundTasks):
    """Join travel agents to a meeting"""
    if req.meeting_id in active_sessions:
        print(f"[{req.meeting_id}] Travel agent already exists for this meeting.")
        raise HTTPException(status_code=400, detail="Travel agent already active for this meeting")

    bg_tasks.add_task(start_travel_agents_for_meeting, req)
    return {"message": f"Travel A2A agents joining process initiated for meeting {req.meeting_id}"}

@app.post("/leave-agent")
async def leave_agent(req: LeaveAgentReqConfig):
    """Remove travel agents from a meeting"""
    meeting_id = req.meeting_id
    print(f"[{meeting_id}] Received /leave-agent request.")

    session = active_sessions.pop(meeting_id, None)

    if session:
        print(f"[{meeting_id}] Travel session removed from active_sessions.")
        return {
            "status": "removed",
            "meeting_id": meeting_id,
            "message": f"Travel session for meeting {meeting_id} has been removed."
        }
    else:
        print(f"[{meeting_id}] No travel session found in active_sessions (likely already completed).")
        return {
            "status": "removed",
            "meeting_id": meeting_id,
            "message": f"Travel session for meeting {meeting_id} has been removed (was already completed)."
        }

@app.get("/test")
async def test():
    """Test endpoint for travel server"""
    print("Travel A2A Test endpoint hit!")
    return {"message": "VideoSDK Travel A2A Server with Email is running!", "agents": ["travel", "flight", "hotel", "email"]}

# --- Main execution block ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True, log_level="info") 