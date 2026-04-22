"""
Analytics Service - Real-time analytics and reporting
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
import json
from kafka import KafkaConsumer
import threading
import clickhouse_connect

app = FastAPI(title="Analytics Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ClickHouse for analytics
client = clickhouse_connect.get_client(
    host=os.getenv("CLICKHOUSE_HOST", "localhost"),
    port=int(os.getenv("CLICKHOUSE_PORT", 8123)),
    username=os.getenv("CLICKHOUSE_USER", "default"),
    password=os.getenv("CLICKHOUSE_PASSWORD", "")
)

# Create tables
client.command("""
    CREATE TABLE IF NOT EXISTS bookings_analytics (
        timestamp DateTime,
        booking_id String,
        user_id String,
        hotel_id String,
        amount Float32,
        status String
    ) ENGINE = MergeTree()
    ORDER BY timestamp
""")

client.command("""
    CREATE TABLE IF NOT EXISTS searches_analytics (
        timestamp DateTime,
        query String,
        results_count Int32,
        user_id String
    ) ENGINE = MergeTree()
    ORDER BY timestamp
""")

class AnalyticsQuery(BaseModel):
    metric: str
    start_date: str
    end_date: str
    filters: Optional[Dict] = {}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "analytics"}

@app.post("/analytics/query")
async def query_analytics(request: AnalyticsQuery):
    """Query analytics data"""
    
    try:
        if request.metric == "bookings":
            query = f"""
                SELECT 
                    toStartOfDay(timestamp) as day,
                    count() as bookings,
                    sum(amount) as revenue
                FROM bookings_analytics
                WHERE timestamp >= '{request.start_date}' 
                AND timestamp <= '{request.end_date}'
                GROUP BY day
                ORDER BY day
            """
        elif request.metric == "searches":
            query = f"""
                SELECT 
                    toStartOfDay(timestamp) as day,
                    count() as searches,
                    avg(results_count) as avg_results
                FROM searches_analytics
                WHERE timestamp >= '{request.start_date}' 
                AND timestamp <= '{request.end_date}'
                GROUP BY day
                ORDER BY day
            """
        else:
            raise HTTPException(status_code=400, detail="Unknown metric")
        
        result = client.query(query)
        
        return {
            "metric": request.metric,
            "data": [
                {
                    "date": row[0],
                    "count": row[1],
                    "value": row[2] if len(row) > 2 else None
                }
                for row in result.result_rows
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/dashboard")
async def get_dashboard():
    """Get dashboard metrics"""
    
    try:
        # Total bookings today
        today = datetime.now().strftime("%Y-%m-%d")
        total_bookings = client.query(f"""
            SELECT count() 
            FROM bookings_analytics 
            WHERE toDate(timestamp) = '{today}'
        """).first_row[0]
        
        # Total revenue today
        total_revenue = client.query(f"""
            SELECT sum(amount) 
            FROM bookings_analytics 
            WHERE toDate(timestamp) = '{today}'
        """).first_row[0] or 0
        
        # Total searches today
        total_searches = client.query(f"""
            SELECT count() 
            FROM searches_analytics 
            WHERE toDate(timestamp) = '{today}'
        """).first_row[0]
        
        # Average booking value
        avg_booking = client.query(f"""
            SELECT avg(amount) 
            FROM bookings_analytics 
            WHERE toDate(timestamp) = '{today}'
        """).first_row[0] or 0
        
        return {
            "date": today,
            "total_bookings": total_bookings,
            "total_revenue": total_revenue,
            "total_searches": total_searches,
            "avg_booking_value": avg_booking,
            "conversion_rate": (total_bookings / total_searches * 100) if total_searches > 0 else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def consume_events():
    """Consume events and store in analytics"""
    consumer = KafkaConsumer(
        'booking.confirmed',
        'search.completed',
        bootstrap_servers=os.getenv("KAFKA_BROKERS", "localhost:9092"),
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    
    for message in consumer:
        event = message.value
        
        if message.topic == 'booking.confirmed':
            # Store booking analytics
            client.insert(
                'bookings_analytics',
                [
                    {
                        'timestamp': datetime.utcnow(),
                        'booking_id': event['booking_id'],
                        'user_id': str(event['user_id']),
                        'hotel_id': event['hotel_id'],
                        'amount': event.get('amount', 0),
                        'status': 'confirmed'
                    }
                ]
            )
            
        elif message.topic == 'search.completed':
            # Store search analytics
            client.insert(
                'searches_analytics',
                [
                    {
                        'timestamp': datetime.utcnow(),
                        'query': event.get('query', ''),
                        'results_count': event.get('results_count', 0),
                        'user_id': str(event.get('user_id', ''))
                    }
                ]
            )

# Start event consumer in background
consumer_thread = threading.Thread(target=consume_events, daemon=True)
consumer_thread.start()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
