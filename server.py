#!/usr/bin/env python3
"""
AI Agent Demo Server - Entry Point

This is the main entry point for the AI Agent Demo server.
The server is built using a modular architecture with separated concerns.

Usage:
    python server_new.py
    
Or with uvicorn directly:
    uvicorn server_new:app --host 127.0.0.1 --port 8000 --reload
"""

import uvicorn
from main import app
from config import settings


if __name__ == "__main__":
    # Run the server with configuration from settings
    uvicorn.run(
        "server_new:app",  # Module and app reference
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level="info"
    ) 