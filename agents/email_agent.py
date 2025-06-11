from videosdk.agents import Agent, AgentCard, A2AMessage
import asyncio

class EmailAgent(Agent):
    """Specialist agent for sending emails"""
    
    def __init__(self):
        super().__init__(
            agent_id="agent_email_001",
            instructions=(
                "You are an email automation specialist. "
                "You send booking confirmations, travel updates, and important notifications to customers."
            ),
            # mcp_servers=[
            #     MCPServerHTTP(
            #         # url=os.getenv("ZAPIER_EMAIL_WEBHOOK_URL"),
            #         url="https://mcp.zapier.com/api/mcp/s/ODk5ODA5OTctMDM2Ny00ZDEyLTk2NjctNDQ4NDE3MDI5MjA3OjE3MzQ5NjE3LTg0MjQtNDJhZC1iOWJkLTE2OTBmMmRkYzI0ZQ==/mcp",
            #         client_session_timeout_seconds=30
            #     )
            # ]
        )

    async def handle_send_booking_email(self, message: A2AMessage):
        """Handle email sending requests"""
        email_type = message.content.get("email_type")
        details = message.content.get("details") 
        recipient = message.content.get("recipient")
        
        print(f"[Email Agent] Sending {email_type} email to {recipient}")
        
        try:
            # For now, simulate email sending
            print(f"[Email Agent] ✅ Email simulated successfully: {email_type}")
            print(f"[Email Agent] → Subject: Your {email_type.replace('_', ' ').title()}")
            print(f"[Email Agent] → To: {recipient}")
            print(f"[Email Agent] → Content: {details[:100]}...")
            status = "sent"
            
        except Exception as e:
            print(f"[Email Agent] Error sending email: {e}")
            status = "failed"
        
        # Notify travel agent about email status
        await self.a2a.send_message(
            to_agent="travel_agent_1",
            message_type="email_confirmation",
            content={
                "status": status,
                "email_type": email_type,
                "recipient": recipient
            }
        )

    async def on_enter(self):
        print("[Email Agent] EmailAgent entered session (running in background).")
        await self.register_a2a(AgentCard(
            id="agent_email_001",
            name="Email Automation Service",
            domain="email", 
            capabilities=[
                "send_confirmations",
                "send_updates",
                "send_notifications"
            ],
            description="Handles all email communications and confirmations"
        ))
        
        # Register message handlers
        self.a2a.on_message("send_booking_email", self.handle_send_booking_email)
        print("[Email Agent] A2A registered and listening for email requests.")

    async def on_exit(self):
        print("[Email Agent] EmailAgent left the session.")
        if hasattr(self, 'a2a') and self.a2a:
            await self.unregister_a2a() 