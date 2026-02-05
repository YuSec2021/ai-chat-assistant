"""FastAPI application entry point"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.config import settings
from src.db.mongo import mongodb, init_db
from src.api import chat, conversations, upload
from src.agents import agent_registry
from src.utils.logger import configure_logging
import structlog

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""

    # Startup
    configure_logging()
    logger.info("Starting AI Chat Assistant")

    # Connect to database
    await mongodb.connect()
    await init_db()

    # List registered agents
    agents = agent_registry.list_agents()
    logger.info("Registered agents", count=len(agents), agents=[a.name for a in agents])

    yield

    # Shutdown
    logger.info("Shutting down AI Chat Assistant")
    await mongodb.disconnect()


# Create FastAPI app
app = FastAPI(
    title="AI Chat Assistant",
    description="Full-stack AI chat assistant with agent routing",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(upload.router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/api/agents")
async def list_agents():
    """List all available agents"""
    agents = agent_registry.list_agents()
    return {"agents": [a.model_dump() for a in agents]}


# Mount frontend static files (if built)
# app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="frontend")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Chat Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
