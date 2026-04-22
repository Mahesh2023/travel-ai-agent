"""
Payment Service - Payment processing with Stripe
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, DateTime, Float, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from enum import Enum
import os
import stripe
import json
from kafka import KafkaProducer
import uuid

app = FastAPI(title="Payment Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stripe configuration
stripe.api_key = os.getenv("STRIPE_API_KEY")

# Database
engine = create_engine(os.getenv("DATABASE_URL", "sqlite:///./payments.db"))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Kafka for events
kafka_producer = KafkaProducer(
    bootstrap_servers=os.getenv("KAFKA_BROKERS", "localhost:9092"),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id = Column(String, index=True)
    amount = Column(Float)
    currency = Column(String, default="USD")
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    stripe_payment_intent_id = Column(String, unique=True)
    metadata = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

Base.metadata.create_all(bind=engine)

class PaymentRequest(BaseModel):
    booking_id: str
    amount: float
    currency: str = "USD"
    payment_method_id: str
    metadata: dict = {}

class PaymentResponse(BaseModel):
    id: str
    booking_id: str
    amount: float
    currency: str
    status: str
    client_secret: str = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "payment"}

@app.post("/payments/create", response_model=PaymentResponse)
async def create_payment(request: PaymentRequest, db: Session = Depends(get_db)):
    """Create payment intent"""
    
    payment_id = str(uuid.uuid4())
    
    try:
        # Create Stripe Payment Intent
        payment_intent = stripe.PaymentIntent.create(
            amount=int(request.amount * 100),  # Convert to cents
            currency=request.currency.lower(),
            metadata={"booking_id": request.booking_id}
        )
        
        # Create payment record
        payment = Payment(
            id=payment_id,
            booking_id=request.booking_id,
            amount=request.amount,
            currency=request.currency,
            status=PaymentStatus.PENDING,
            stripe_payment_intent_id=payment_intent.id,
            metadata=json.dumps(request.metadata)
        )
        db.add(payment)
        db.commit()
        
        return PaymentResponse(
            id=payment_id,
            booking_id=request.booking_id,
            amount=request.amount,
            currency=request.currency,
            status="pending",
            client_secret=payment_intent.client_secret
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/payments/{payment_id}/confirm", response_model=dict)
async def confirm_payment(payment_id: str, db: Session = Depends(get_db)):
    """Confirm payment after client-side completion"""
    
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    try:
        # Retrieve payment intent from Stripe
        payment_intent = stripe.PaymentIntent.retrieve(payment.stripe_payment_intent_id)
        
        if payment_intent.status == "succeeded":
            payment.status = PaymentStatus.SUCCESS
            db.commit()
            
            # Publish event
            kafka_producer.send("payment.success", {
                "payment_id": payment_id,
                "booking_id": payment.booking_id,
                "amount": payment.amount,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return {"payment_id": payment_id, "status": "success"}
        else:
            payment.status = PaymentStatus.FAILED
            db.commit()
            
            kafka_producer.send("payment.failed", {
                "payment_id": payment_id,
                "booking_id": payment.booking_id,
                "error": payment_intent.last_payment_error,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return {"payment_id": payment_id, "status": "failed"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/payments/{payment_id}/refund", response_model=dict)
async def refund_payment(payment_id: str, db: Session = Depends(get_db)):
    """Refund payment"""
    
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment.status != PaymentStatus.SUCCESS:
        raise HTTPException(status_code=400, detail="Payment cannot be refunded")
    
    try:
        # Create refund in Stripe
        refund = stripe.Refund.create(
            payment_intent=payment.stripe_payment_intent_id
        )
        
        payment.status = PaymentStatus.REFUNDED
        db.commit()
        
        # Publish event
        kafka_producer.send("payment.refunded", {
            "payment_id": payment_id,
            "booking_id": payment.booking_id,
            "amount": payment.amount,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {"payment_id": payment_id, "status": "refunded", "refund_id": refund.id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/payments/{payment_id}")
async def get_payment(payment_id: str, db: Session = Depends(get_db)):
    """Get payment details"""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return {
        "id": payment.id,
        "booking_id": payment.booking_id,
        "amount": payment.amount,
        "currency": payment.currency,
        "status": payment.status.value,
        "created_at": payment.created_at.isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
