from videosdk.agents import Agent, AgentCard, A2AMessage
import asyncio

class HotelAgent(Agent):
    """Specialist agent for hotel bookings"""
    
    def __init__(self):
        super().__init__(
            agent_id="agent_hotel_001", 
            instructions=(
                "You are a specialized hotel booking expert. "
                "You help customers find and book hotels at their destinations. "
                "Provide detailed hotel information including amenities, prices, and locations. "
                "Suggest hotels based on budget and preferences. "
                "Keep responses helpful and concise."
            )
        )

    async def handle_hotel_search_query(self, message: A2AMessage):
        """Handle hotel search requests from travel agent"""
        destination = message.content.get("destination")
        dates = message.content.get("dates")
        customer_email = message.content.get("customer_email")
        requesting_agent = message.content.get("from_agent_id") or message.from_agent_id
        
        if destination:
            print(f"[Hotel Agent] Received hotel search for {destination} from {requesting_agent}")
            
            # Generate hotel response directly (simulating hotel search)
            hotel_response = (
                f"I found excellent hotel options in {destination} for {dates}:\n\n"
                f"🏨 Option 1: Grand Plaza Hotel (4⭐) - $180/night\n"
                f"   • Free WiFi, Pool, Gym, Restaurant\n"
                f"   • Downtown location, 5-min walk to attractions\n\n"
                f"🏨 Option 2: Comfort Inn & Suites (3⭐) - $120/night\n"
                f"   • Free breakfast, WiFi, Parking\n" 
                f"   • Business center, Airport shuttle\n\n"
                f"🏨 Option 3: Luxury Resort & Spa (5⭐) - $350/night\n"
                f"   • Full-service spa, Pool, Beach access\n"
                f"   • Multiple restaurants, Concierge service\n\n"
                f"All hotels offer 24/7 front desk and room service. "
                f"Which option would you prefer for your stay?"
            )
            
            print(f"[Hotel Agent] Sending hotel response to {requesting_agent}")
            
            # Send response back to travel agent
            await self.a2a.send_message(
                to_agent=requesting_agent,
                message_type="hotel_booking_response",
                content={
                    "response": hotel_response,
                    "booking_details": {
                        "service": "hotel",
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
                        "email_type": "hotel_options",
                        "details": hotel_response,
                        "recipient": customer_email or "customer@example.com"
                    }
                )
                
        else:
            print("[Hotel Agent] Received empty hotel query")

    async def on_enter(self):
        print("[Hotel Agent] HotelAgent entered session (running in background).")
        await self.register_a2a(AgentCard(
            id="agent_hotel_001",
            name="Hotel Booking Specialist",
            domain="hotel",
            capabilities=[
                "search_hotels",
                "modify_reservations",
                "check_availability"
            ],
            description="Handles all hotel booking and reservation tasks"
        ))
        
        # Register message handlers
        self.a2a.on_message("hotel_search_query", self.handle_hotel_search_query)
        print("[Hotel Agent] A2A registered and listening for hotel queries.")

    async def on_exit(self):
        print("[Hotel Agent] HotelAgent left the session.")
        if hasattr(self, 'a2a') and self.a2a:
            await self.unregister_a2a() 