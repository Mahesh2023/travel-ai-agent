"""
Notification Service - Send emails, SMS, push notifications
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import json
from kafka import KafkaConsumer, KafkaProducer
import threading
import sendgrid
from sendgrid.helpers.mail import Mail
from twilio.rest import Client
from datetime import datetime

app = FastAPI(title="Notification Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SendGrid
sg = sendgrid.SendGridAPIClient(api_key=os.getenv("SENDGRID_API_KEY"))

# Twilio
twilio_client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

# Kafka
kafka_producer = KafkaProducer(
    bootstrap_servers=os.getenv("KAFKA_BROKERS", "localhost:9092"),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

class EmailRequest(BaseModel):
    to: str
    subject: str
    content: str
    template_id: Optional[str] = None

class SMSRequest(BaseModel):
    to: str
    message: str

class PushRequest(BaseModel):
    user_id: str
    title: str
    body: str
    data: dict = {}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "notification"}

@app.post("/notifications/email")
async def send_email(request: EmailRequest):
    """Send email"""
    
    message = Mail(
        from_email="noreply@travelai.com",
        to_emails=request.to,
        subject=request.subject,
        html_content=request.content
    )
    
    try:
        response = sg.send(message)
        return {"message": "Email sent", "status_code": response.status_code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/notifications/sms")
async def send_sms(request: SMSRequest):
    """Send SMS"""
    
    try:
        message = twilio_client.messages.create(
            body=request.message,
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            to=request.to
        )
        return {"message": "SMS sent", "message_id": message.sid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/notifications/push")
async def send_push(request: PushRequest):
    """Send push notification (placeholder for FCM/APNS)"""
    
    # Implementation would use Firebase Cloud Messaging or Apple Push Notification Service
    return {"message": "Push notification queued", "user_id": request.user_id}

def consume_events():
    """Consume events and send notifications"""
    consumer = KafkaConsumer(
        'booking.confirmed',
        'booking.cancelled',
        'payment.success',
        'payment.failed',
        bootstrap_servers=os.getenv("KAFKA_BROKERS", "localhost:9092"),
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    
    for message in consumer:
        event = message.value
        
        if message.topic == 'booking.confirmed':
            # Send confirmation email
            email_request = EmailRequest(
                to=f"user{event['user_id']}@example.com",
                subject="Booking Confirmed",
                content=f"Your booking {event['booking_id']} has been confirmed."
            )
            send_email(email_request)
            
        elif message.topic == 'booking.cancelled':
            # Send cancellation email
            email_request = EmailRequest(
                to=f"user{event['user_id']}@example.com",
                subject="Booking Cancelled",
                content=f"Your booking {event['booking_id']} has been cancelled."
            )
            send_email(email_request)
            
        elif message.topic == 'payment.success':
            # Send payment success email
            email_request = EmailRequest(
                to=f"user{event['user_id']}@example.com",
                subject="Payment Successful",
                content=f"Your payment of ${event['amount']} was successful."
            )
            send_email(email_request)

# Start event consumer in background
consumer_thread = threading.Thread(target=consume_events, daemon=True)
consumer_thread.start()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
