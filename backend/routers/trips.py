"""
Trips router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from database import get_db, Trip, User
from routers.auth import get_current_user

router = APIRouter()

class TripCreate(BaseModel):
    destination: str
    start_date: str
    end_date: str
    budget: float

class TripResponse(BaseModel):
    id: int
    destination: str
    start_date: str
    end_date: str
    budget: float
    status: str
    itinerary: Optional[str] = None

@router.post("/", response_model=dict)
async def create_trip(
    trip: TripCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new trip"""
    db_trip = Trip(
        user_id=current_user["id"],
        destination=trip.destination,
        start_date=datetime.fromisoformat(trip.start_date),
        end_date=datetime.fromisoformat(trip.end_date),
        budget=trip.budget
    )
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    
    return {"message": "Trip created", "trip_id": db_trip.id}

@router.get("/", response_model=list)
async def get_trips(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all user trips"""
    trips = db.query(Trip).filter(Trip.user_id == current_user["id"]).all()
    return [
        {
            "id": trip.id,
            "destination": trip.destination,
            "start_date": trip.start_date.isoformat(),
            "end_date": trip.end_date.isoformat(),
            "budget": trip.budget,
            "status": trip.status
        }
        for trip in trips
    ]

@router.get("/{trip_id}")
async def get_trip(
    trip_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific trip"""
    trip = db.query(Trip).filter(
        Trip.id == trip_id,
        Trip.user_id == current_user["id"]
    ).first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    return {
        "id": trip.id,
        "destination": trip.destination,
        "start_date": trip.start_date.isoformat(),
        "end_date": trip.end_date.isoformat(),
        "budget": trip.budget,
        "status": trip.status,
        "itinerary": trip.itinerary
    }
