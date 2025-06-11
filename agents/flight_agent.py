from videosdk.agents import Agent, AgentCard, A2AMessage
import asyncio

class FlightAgent(Agent):
    """Specialist agent for flight bookings"""
    
    def __init__(self):
        super().__init__(
            agent_id="agent_flight_001",
            instructions=(
                "You are Skymate, a specialized flight booking expert. "
                "You help customers find and book flights to their destinations. "
                "Provide detailed flight information including times, prices, and airlines. "
                "Always be helpful and suggest the best options for customers. "
                "Keep responses concise and professional."
            )
        )

    async def handle_flight_search_query(self, message: A2AMessage):
        """Handle flight search requests from travel agent"""
        destination = message.content.get("destination")
        dates = message.content.get("dates")
        customer_email = message.content.get("customer_email")
        requesting_agent = message.content.get("from_agent_id") or message.from_agent_id
        
        if destination:
            print(f"[Flight Agent] Received flight search for {destination} from {requesting_agent}")
            
            # Generate flight response directly (simulating flight search)
            flight_response = (
                f"I found several flight options to {destination} for {dates}:\n\n"
                f"✈️ Option 1: Direct flight - $299\n"
                f"   Departure: 8:00 AM, Arrival: 11:30 AM\n"
                f"   Airline: SkyWings Airways\n\n"
                f"✈️ Option 2: Economy Plus - $399\n" 
                f"   Departure: 2:15 PM, Arrival: 5:45 PM\n"
                f"   Airline: CloudJet Airlines\n\n"
                f"✈️ Option 3: Premium Economy - $549\n"
                f"   Departure: 6:30 PM, Arrival: 10:00 PM\n"
                f"   Airline: AeroLink Express\n\n"
                f"All flights include complimentary snacks and beverages. "
                f"Would you like me to proceed with booking one of these options?"
            )
            
            print(f"[Flight Agent] Sending flight response to {requesting_agent} with {flight_response}")
            
            # Send response back to travel agent
            await self.a2a.send_message(
                to_agent=requesting_agent,
                message_type="flight_booking_response",
                content={
                    "response": flight_response,
                    "booking_details": {
                        "service": "flight",
                        "status": "options_available",
                        "destination": destination,
                        "dates": dates
                    }
                }
            )
            
            # Trigger email specialist to send confirmation
            email_agents = self.a2a.registry.find_agents_by_domain("email")
            if email_agents:
                await self.a2a.send_message(
                    to_agent=email_agents[0],
                    message_type="send_booking_email",
                    content={
                        "email_type": "flight_options",
                        "details": flight_response,
                        "recipient": customer_email or "customer@example.com"
                    }
                )
                
        else:
            print("[Flight Agent] Received empty flight query")

    async def on_enter(self):
        print("[Flight Agent] FlightAgent entered session (running in background).")
        await self.register_a2a(AgentCard(
            id="agent_flight_001",
            name="Skymate",
            domain="flight",
            capabilities=[
                "search_flights",
                "modify_bookings", 
                "show_flight_status"
            ],
            description="Handles all flight-related tasks"
        ))
        
        # Register message handlers
        self.a2a.on_message("flight_search_query", self.handle_flight_search_query)
        print("[Flight Agent] A2A registered and listening for flight queries.")

    async def on_exit(self):
        print("[Flight Agent] FlightAgent left the session.")
        if hasattr(self, 'a2a') and self.a2a:
            await self.unregister_a2a() 