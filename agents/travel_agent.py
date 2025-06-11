from videosdk.agents import Agent, function_tool, AgentCard, A2AMessage, MCPServerHTTP
import asyncio
from typing import Dict, Any
from config.settings import ZAPIER_EMAIL_WEBHOOK_URL

class TravelAgent(Agent):
    """Main travel agent that coordinates with specialists"""
    
    def __init__(self, system_prompt: str):
        super().__init__(
            agent_id="travel_agent_1",
            instructions=system_prompt,
            mcp_servers=[
                MCPServerHTTP(
                    url=ZAPIER_EMAIL_WEBHOOK_URL,
                    client_session_timeout_seconds=30
                )
            ] if ZAPIER_EMAIL_WEBHOOK_URL else []
        )

    @function_tool
    async def end_call(self) -> None:
        """End the call upon request by the user"""
        print("[Travel Agent] User requested to end call.")
        await self.session.say("Thank you for choosing our travel services. Have a great trip!")
        await asyncio.sleep(1)
        await self.session.leave()

    @function_tool
    async def book_travel_package(self, destination: str, travel_dates: str, email: str) -> Dict[str, Any]:
        """
        Book a complete travel package including flights and hotels
        Args:
            destination: Where the customer wants to travel
            travel_dates: When they want to travel
            email: Customer email for confirmations
        """
        print(f"[Travel Agent] Processing travel package booking for {destination}")
        
        try:
            await self.session.say(f"Let me search for travel options to {destination}. Please wait a moment while I connect to our booking services...")
            
            # Give specialist agents time to register (with retry mechanism)
            flight_agents = []
            hotel_agents = []
            
            for attempt in range(3):  # Try 3 times
                print(f"[Travel Agent] Attempt {attempt + 1}: Looking for specialist agents...")
                
                flight_agents = self.a2a.registry.find_agents_by_domain("flight")
                hotel_agents = self.a2a.registry.find_agents_by_domain("hotel")
                
                if flight_agents and hotel_agents:
                    print(f"[Travel Agent] Found both flight and hotel agents on attempt {attempt + 1}")
                    break
                    
                if attempt < 2:  # Don't wait on the last attempt
                    print(f"[Travel Agent] Agents not ready yet. Waiting 2 seconds...")
                    await asyncio.sleep(2)

            # Check if we found the required agents
            if not flight_agents:
                await self.session.say("I'm sorry, our flight booking service is temporarily unavailable. Please try again in a moment.")
                return {"error": "No flight agent available"}

            if not hotel_agents:
                await self.session.say("I'm sorry, our hotel booking service is temporarily unavailable. Please try again in a moment.")
                return {"error": "No hotel agent available"}

            await self.session.say(f"Great! I've connected to our booking services. Searching for flights and hotels for {destination}...")

            # Send flight query
            await self.a2a.send_message(
                to_agent=flight_agents[0],
                message_type="flight_search_query",
                content={
                    "destination": destination,
                    "dates": travel_dates,
                    "customer_email": email,
                    "from_agent_id": "travel_agent_1"
                }
            )

            # Send hotel query
            await self.a2a.send_message(
                to_agent=hotel_agents[0], 
                message_type="hotel_search_query",
                content={
                    "destination": destination,
                    "dates": travel_dates,
                    "customer_email": email,
                    "from_agent_id": "travel_agent_1"
                }
            )

            return {
                "status": "processing",
                "message": f"Searching for travel options to {destination}..."
            }

        except Exception as e:
            print(f"[Travel Agent] Error in book_travel_package: {e}")
            await self.session.say("I encountered an error while processing your request. Please try again.")
            return {"error": str(e)}

    async def handle_flight_response(self, message: A2AMessage) -> None:
        """Handle flight booking responses"""
        response = message.content.get("response")
        booking_details = message.content.get("booking_details")
        
        if response:
            print(f"[Travel Agent] Received flight response: {response}")
            await asyncio.sleep(0.5)
            await self.session.say(f"Flight update: {response}")

    async def handle_hotel_response(self, message: A2AMessage) -> None:
        """Handle hotel booking responses"""
        response = message.content.get("response") 
        booking_details = message.content.get("booking_details")
        
        if response:
            print(f"[Travel Agent] Received hotel response: {response}")
            await asyncio.sleep(0.5)
            await self.session.say(f"Hotel update: {response}")

    async def handle_email_sent(self, message: A2AMessage) -> None:
        """Handle email confirmation"""
        status = message.content.get("status")
        email_type = message.content.get("email_type")
        
        if status == "sent":
            await self.session.say(f"I've sent you a {email_type.replace('_', ' ')} confirmation email. Please check your inbox.")
        elif status == "failed":
            await self.session.say(f"I had trouble sending the {email_type.replace('_', ' ')} email, but I've recorded your booking details.")

    async def on_enter(self):
        print("[Travel Agent] TravelAgent entered session.")
        await self.register_a2a(AgentCard(
            id="travel_agent_1",
            name="Travel Coordinator",
            domain="travel",
            capabilities=["travel_planning", "booking_coordination", "customer_service"],
            description="Main travel agent that coordinates bookings and customer communication"
        ))
        
        # Register A2A message handlers
        self.a2a.on_message("flight_booking_response", self.handle_flight_response)
        self.a2a.on_message("hotel_booking_response", self.handle_hotel_response)
        self.a2a.on_message("email_confirmation", self.handle_email_sent)
        print("[Travel Agent] A2A registered and listening for specialist responses.")
        
        # Initial greeting
        await asyncio.sleep(0.5)
        await self.session.say("Hello! I'm your travel agent. I can help you book flights, hotels, and send you confirmation emails. Where would you like to travel?")
        print("[Travel Agent] Initial greeting sent.")

    async def on_exit(self):
        print("[Travel Agent] TravelAgent left the session.")
        if hasattr(self, 'a2a') and self.a2a:
            await self.unregister_a2a() 