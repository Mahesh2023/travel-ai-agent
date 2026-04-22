"""
Travel AI Agent Platform - Main Application
FastAPI backend with RAG, MCP, and AI agents
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

load_dotenv()

from backend.database import init_db
from backend.routers import (
    auth,
    trips,
    bookings,
    # agents,  # Disabled - requires langchain
    # rag      # Disabled - requires langchain
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    # Startup
    await init_db()
    yield
    # Shutdown
    pass

app = FastAPI(
    title="Travel AI Agent Platform",
    description="AI-powered travel agency platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(trips.router, prefix="/api/trips", tags=["Trips"])
app.include_router(bookings.router, prefix="/api/bookings", tags=["Bookings"])
# app.include_router(agents.router, prefix="/api/agents", tags=["AI Agents"])  # Disabled
# app.include_router(rag.router, prefix="/api/rag", tags=["RAG"])  # Disabled

@app.get("/")
async def root():
    return {
        "message": "Travel AI Agent Platform API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
