from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from api import router


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    # Validate required environment variables
    settings.validate_required_keys()
    
    # Create FastAPI app
    app = FastAPI(
        title="AI Agent Demo",
        description="VideoSDK AI Agent Demo with voice capabilities",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_CREDENTIALS,
        allow_methods=settings.CORS_METHODS,
        allow_headers=settings.CORS_HEADERS,
    )
    
    # Include API routes
    app.include_router(router)
    
    @app.on_event("startup")
    async def startup_event():
        """Application startup event."""
        print("🚀 AI Agent Demo Server starting up...")
        print(f"📊 Server running on {settings.HOST}:{settings.PORT}")
        if not settings.validate_required_keys():
            print("⚠️  Some required environment variables are missing!")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Application shutdown event."""
        print("🛑 AI Agent Demo Server shutting down...")
        # Clean up any remaining sessions
        from services import session_manager
        cleared_sessions = session_manager.clear_all_sessions()
        if cleared_sessions > 0:
            print(f"🧹 Cleaned up {cleared_sessions} remaining sessions")
    
    return app


# Create the app instance
app = create_app() 