import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Server configuration
PORT = int(os.getenv("PORT", 8002))

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ZAPIER_EMAIL_WEBHOOK_URL = os.getenv("ZAPIER_EMAIL_WEBHOOK_URL")

# Default model settings
DEFAULT_VOICE = "Puck"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.9
DEFAULT_TOP_K = 1 