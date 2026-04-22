"""
Inventory Service - Real-time inventory management with Cassandra
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from datetime import datetime, timedelta
import os
import redis
import json
from kafka import KafkaProducer, KafkaConsumer
import threading
import time

app = FastAPI(title="Inventory Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cassandra cluster
cluster = Cluster([os.getenv("CASSANDRA_CONTACT_POINTS", "localhost")])
session = cluster.connect()

# Create keyspace and tables
session.execute("""
    CREATE KEYSPACE IF NOT EXISTS travel_inventory 
    WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 3}
""")
session.set_keyspace('travel_inventory')

session.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        hotel_id text,
        room_type text,
        date date,
        available_rooms int,
        total_rooms int,
        price float,
        PRIMARY KEY ((hotel_id, date), room_type)
    )
""")

# Redis for hot inventory
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

class InventoryCheck(BaseModel):
    hotel_id: str
    room_type: str
    date: str
    guests: int

class InventoryUpdate(BaseModel):
    hotel_id: str
    room_type: str
    date: str
    available_rooms: int
    total_rooms: int
    price: float

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "inventory"}

@app.post("/inventory/check")
async def check_inventory(request: InventoryCheck):
    """Check if rooms are available"""
    
    # Check Redis cache first
    cache_key = f"inventory:{request.hotel_id}:{request.date}:{request.room_type}"
    cached = redis_client.get(cache_key)
    
    if cached:
        data = json.loads(cached)
        available = data['available_rooms'] >= request.guests
        return {"available": available, "available_rooms": data['available_rooms']}
    
    # Query Cassandra
    query = SimpleStatement("""
        SELECT available_rooms, total_rooms, price 
        FROM inventory 
        WHERE hotel_id = %s AND date = %s AND room_type = %s
    """)
    result = session.execute(query, (request.hotel_id, request.date, request.room_type))
    
    if not result:
        return {"available": False, "available_rooms": 0}
    
    row = result.one()
    available = row.available_rooms >= request.guests
    
    # Cache result
    redis_client.setex(cache_key, 300, json.dumps({
        "available_rooms": row.available_rooms,
        "total_rooms": row.total_rooms,
        "price": row.price
    }))
    
    return {"available": available, "available_rooms": row.available_rooms}

@app.post("/inventory/update")
async def update_inventory(request: InventoryUpdate):
    """Update inventory (called by suppliers)"""
    
    query = SimpleStatement("""
        INSERT INTO inventory (hotel_id, room_type, date, available_rooms, total_rooms, price)
        VALUES (%s, %s, %s, %s, %s, %s)
    """)
    
    session.execute(query, (
        request.hotel_id,
        request.room_type,
        request.date,
        request.available_rooms,
        request.total_rooms,
        request.price
    ))
    
    # Invalidate cache
    cache_key = f"inventory:{request.hotel_id}:{request.date}:{request.room_type}"
    redis_client.delete(cache_key)
    
    # Publish event
    kafka_producer.send("inventory.updated", {
        "hotel_id": request.hotel_id,
        "room_type": request.room_type,
        "date": request.date,
        "available_rooms": request.available_rooms,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return {"message": "Inventory updated"}

@app.post("/inventory/reserve")
async def reserve_inventory(request: InventoryCheck):
    """Reserve inventory (optimistic locking)"""
    
    # Get current inventory
    query = SimpleStatement("""
        SELECT available_rooms, total_rooms 
        FROM inventory 
        WHERE hotel_id = %s AND date = %s AND room_type = %s
    """)
    result = session.execute(query, (request.hotel_id, request.date, request.room_type))
    
    if not result:
        raise HTTPException(status_code=404, detail="Inventory not found")
    
    row = result.one()
    
    if row.available_rooms < request.guests:
        return {"success": False, "message": "Not enough rooms available"}
    
    # Update inventory (optimistic locking)
    update_query = SimpleStatement("""
        UPDATE inventory 
        SET available_rooms = available_rooms - %s 
        WHERE hotel_id = %s AND date = %s AND room_type = %s 
        AND available_rooms >= %s
    """)
    
    session.execute(update_query, (
        request.guests,
        request.hotel_id,
        request.date,
        request.room_type,
        request.guests
    ))
    
    # Invalidate cache
    cache_key = f"inventory:{request.hotel_id}:{request.date}:{request.room_type}"
    redis_client.delete(cache_key)
    
    return {"success": True, "message": "Inventory reserved"}

@app.post("/inventory/release")
async def release_inventory(request: InventoryCheck):
    """Release inventory back to pool"""
    
    update_query = SimpleStatement("""
        UPDATE inventory 
        SET available_rooms = available_rooms + %s 
        WHERE hotel_id = %s AND date = %s AND room_type = %s
    """)
    
    session.execute(update_query, (
        request.guests,
        request.hotel_id,
        request.date,
        request.room_type
    ))
    
    # Invalidate cache
    cache_key = f"inventory:{request.hotel_id}:{request.date}:{request.room_type}"
    redis_client.delete(cache_key)
    
    return {"success": True, "message": "Inventory released"}

def consume_events():
    """Consume booking events to update inventory"""
    consumer = KafkaConsumer(
        'booking.confirmed',
        'booking.cancelled',
        bootstrap_servers=os.getenv("KAFKA_BROKERS", "localhost:9092"),
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    
    for message in consumer:
        event = message.value
        
        if message.topic == 'booking.confirmed':
            # Inventory already reserved during booking
            pass
        elif message.topic == 'booking.cancelled':
            # Release inventory
            release_request = InventoryCheck(
                hotel_id=event['hotel_id'],
                room_type='standard',  # Would come from booking
                date=event['check_in'].split('T')[0],
                guests=event['guests']
            )
            release_inventory(release_request)

# Start event consumer in background
consumer_thread = threading.Thread(target=consume_events, daemon=True)
consumer_thread.start()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
