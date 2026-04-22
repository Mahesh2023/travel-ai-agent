"""
AI Agents router
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from agents.planning_agent import PlanningAgent
from agents.booking_agent import BookingAgent
from agents.support_agent import SupportAgent

router = APIRouter()

class PlanningRequest(BaseModel):
    destination: str
    start_date: str
    end_date: str
    budget: float
    preferences: Optional[str] = None

class BookingRequest(BaseModel):
    booking_type: str
    details: dict

class SupportRequest(BaseModel):
    message: str
    context: Optional[str] = None

@router.post("/plan")
async def plan_trip(request: PlanningRequest):
    """Generate trip plan using AI agent"""
    try:
        agent = PlanningAgent()
        plan = agent.generate_plan(
            destination=request.destination,
            start_date=request.start_date,
            end_date=request.end_date,
            budget=request.budget,
            preferences=request.preferences
        )
        return {"plan": plan}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/book")
async def make_booking(request: BookingRequest):
    """Make booking using AI agent"""
    try:
        agent = BookingAgent()
        result = agent.make_booking(
            booking_type=request.booking_type,
            details=request.details
        )
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/support")
async def get_support(request: SupportRequest):
    """Get customer support using AI agent"""
    try:
        agent = SupportAgent()
        response = agent.respond(
            message=request.message,
            context=request.context
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
