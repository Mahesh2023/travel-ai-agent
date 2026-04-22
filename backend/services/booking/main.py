"""
Booking Service - Reservation lifecycle management with Saga pattern
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
from enum import Enum
import os
import redis
import json
from kafka import KafkaProducer
import uuid

app = FastAPI(title="Booking Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database
engine = create_engine(os.getenv("DATABASE_URL", "sqlite:///./bookings.db"))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis for soft locks
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

# Kafka for events
kafka_producer = KafkaProducer(
    bootstrap_servers=os.getenv("KAFKA_BROKERS", "localhost:9092"),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True)
    hotel_id = Column(String, index=True)
    check_in = Column(DateTime)
    check_out = Column(DateTime)
    guests = Column(Integer)
    total_price = Column(Float)
    status = Column(SQLEnum(BookingStatus), default=BookingStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

Base.metadata.create_all(bind=engine)

class BookingRequest(BaseModel):
    user_id: str
    hotel_id: str
    check_in: str
    check_out: str
    guests: int
    total_price: float

class BookingResponse(BaseModel):
    id: str
    user_id: str
    hotel_id: str
    check_in: str
    check_out: str
    guests: int
    total_price: float
    status: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "booking"}

@app.post("/bookings/initiate", response_model=dict)
async def initiate_booking(request: BookingRequest, db: Session = Depends(get_db)):
    """Initiate booking with soft hold on inventory"""
    
    booking_id = str(uuid.uuid4())
    
    # Create soft hold in Redis (5 minutes TTL)
    hold_key = f"hold:{booking_id}"
    hold_data = {
        "hotel_id": request.hotel_id,
        "check_in": request.check_in,
        "check_out": request.check_out,
        "guests": request.guests,
        "total_price": request.total_price
    }
    redis_client.setex(hold_key, 300, json.dumps(hold_data))
    
    # Create pending booking
    booking = Booking(
        id=booking_id,
        user_id=request.user_id,
        hotel_id=request.hotel_id,
        check_in=datetime.fromisoformat(request.check_in),
        check_out=datetime.fromisoformat(request.check_out),
        guests=request.guests,
        total_price=request.total_price,
        status=BookingStatus.PENDING
    )
    db.add(booking)
    db.commit()
    
    # Publish event
    kafka_producer.send("booking.initiated", {
        "booking_id": booking_id,
        "user_id": request.user_id,
        "hotel_id": request.hotel_id,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return {
        "booking_id": booking_id,
        "status": "pending",
        "expires_at": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
    }

@app.post("/bookings/{booking_id}/confirm", response_model=dict)
async def confirm_booking(booking_id: str, db: Session = Depends(get_db)):
    """Confirm booking after successful payment"""
    
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Convert soft hold to hard booking
    hold_key = f"hold:{booking_id}"
    hold_data = redis_client.get(hold_key)
    
    if not hold_data:
        raise HTTPException(status_code=400, detail="Hold expired")
    
    # Update booking status
    booking.status = BookingStatus.CONFIRMED
    db.commit()
    
    # Remove soft hold
    redis_client.delete(hold_key)
    
    # Publish event
    kafka_producer.send("booking.confirmed", {
        "booking_id": booking_id,
        "user_id": booking.user_id,
        "hotel_id": booking.hotel_id,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return {"booking_id": booking_id, "status": "confirmed"}

@app.post("/bookings/{booking_id}/cancel", response_model=dict)
async def cancel_booking(booking_id: str, db: Session = Depends(get_db)):
    """Cancel booking and release inventory"""
    
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.status != BookingStatus.CONFIRMED:
        raise HTTPException(status_code=400, detail="Booking cannot be cancelled")
    
    # Update booking status
    booking.status = BookingStatus.CANCELLED
    db.commit()
    
    # Publish event for inventory release
    kafka_producer.send("booking.cancelled", {
        "booking_id": booking_id,
        "user_id": booking.user_id,
        "hotel_id": booking.hotel_id,
        "check_in": booking.check_in.isoformat(),
        "check_out": booking.check_out.isoformat(),
        "guests": booking.guests,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return {"booking_id": booking_id, "status": "cancelled"}

@app.get("/bookings/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id: str, db: Session = Depends(get_db)):
    """Get booking details"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return BookingResponse(
        id=booking.id,
        user_id=booking.user_id,
        hotel_id=booking.hotel_id,
        check_in=booking.check_in.isoformat(),
        check_out=booking.check_out.isoformat(),
        guests=booking.guests,
        total_price=booking.total_price,
        status=booking.status.value
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
