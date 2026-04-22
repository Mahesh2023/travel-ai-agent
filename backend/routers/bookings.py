"""
Bookings router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db, Booking, Trip
from routers.auth import get_current_user

router = APIRouter()

class BookingCreate(BaseModel):
    trip_id: int
    booking_type: str
    provider: str
    details: str
    price: float

@router.post("/", response_model=dict)
async def create_booking(
    booking: BookingCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new booking"""
    # Verify trip belongs to user
    trip = db.query(Trip).filter(
        Trip.id == booking.trip_id,
        Trip.user_id == current_user["id"]
    ).first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    db_booking = Booking(
        trip_id=booking.trip_id,
        booking_type=booking.booking_type,
        provider=booking.provider,
        details=booking.details,
        price=booking.price
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    
    return {"message": "Booking created", "booking_id": db_booking.id}

@router.get("/trip/{trip_id}")
async def get_trip_bookings(
    trip_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get bookings for a trip"""
    bookings = db.query(Booking).join(Trip).filter(
        Trip.id == trip_id,
        Trip.user_id == current_user["id"]
    ).all()
    
    return [
        {
            "id": b.id,
            "booking_type": b.booking_type,
            "provider": b.provider,
            "confirmation_number": b.confirmation_number,
            "price": b.price,
            "status": b.status
        }
        for b in bookings
    ]
