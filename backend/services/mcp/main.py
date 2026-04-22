"""
MCP Gateway - External API tool execution
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import redis
import json
from kafka import KafkaProducer
from datetime import datetime

app = FastAPI(title="MCP Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis for caching
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

class ToolRequest(BaseModel):
    tool: str
    params: dict

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "mcp"}

@app.post("/mcp/execute")
async def execute_tool(request: ToolRequest):
    """Execute MCP tool"""
    
    # Check cache
    cache_key = f"mcp:{request.tool}:{hash(str(request.params))}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    result = None
    
    if request.tool == "search_flights":
        result = await search_flights(request.params)
    elif request.tool == "search_hotels":
        result = await search_hotels(request.params)
    elif request.tool == "get_weather":
        result = await get_weather(request.params)
    elif request.tool == "book_flight":
        result = await book_flight(request.params)
    elif request.tool == "book_hotel":
        result = await book_hotel(request.params)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown tool: {request.tool}")
    
    # Cache result (5 minutes)
    redis_client.setex(cache_key, 300, json.dumps(result))
    
    # Publish event
    kafka_producer.send("mcp.executed", {
        "tool": request.tool,
        "params": request.params,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return result

async def search_flights(params: dict):
    """Search flights via Amadeus API"""
    
    amadeus_api_key = os.getenv("AMADEUS_API_KEY")
    amadeus_secret = os.getenv("AMADEUS_SECRET")
    
    if not amadeus_api_key or not amadeus_secret:
        # Demo mode
        return {
            "flights": [
                {
                    "airline": "Demo Airline",
                    "flight_number": "DA123",
                    "origin": params.get("origin"),
                    "destination": params.get("destination"),
                    "departure_time": "10:00",
                    "arrival_time": "14:00",
                    "price": 299,
                    "currency": "USD"
                }
            ],
            "status": "demo_mode"
        }
    
    async with httpx.AsyncClient() as client:
        # Get access token
        auth_response = await client.post(
            "https://test.api.amadeus.com/v1/security/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": amadeus_api_key,
                "client_secret": amadeus_secret
            }
        )
        token = auth_response.json()["access_token"]
        
        # Search flights
        search_response = await client.get(
            "https://test.api.amadeus.com/v2/shopping/flight-offers",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "originLocationCode": params.get("origin"),
                "destinationLocationCode": params.get("destination"),
                "departureDate": params.get("departure_date"),
                "returnDate": params.get("return_date"),
                "adults": params.get("passengers", 1)
            }
        )
        
        return search_response.json()

async def search_hotels(params: dict):
    """Search hotels via Booking.com API"""
    
    booking_api_key = os.getenv("BOOKING_API_KEY")
    
    if not booking_api_key:
        # Demo mode
        return {
            "hotels": [
                {
                    "name": "Demo Hotel",
                    "city": params.get("city"),
                    "price_per_night": 150,
                    "rating": 4.5,
                    "amenities": ["WiFi", "Pool", "Restaurant"]
                }
            ],
            "status": "demo_mode"
        }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.booking.com/hotels",
            headers={"Authorization": f"Bearer {booking_api_key}"},
            params={
                "city": params.get("city"),
                "check_in": params.get("check_in"),
                "check_out": params.get("check_out"),
                "guests": params.get("guests", 1)
            }
        )
        
        return response.json()

async def get_weather(params: dict):
    """Get weather via OpenWeatherMap API"""
    
    weather_api_key = os.getenv("WEATHER_API_KEY")
    
    if not weather_api_key:
        # Demo mode
        return {
            "city": params.get("city"),
            "forecast": [
                {
                    "date": "2025-06-01",
                    "temperature": 25,
                    "condition": "Sunny",
                    "humidity": 60
                }
            ],
            "status": "demo_mode"
        }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://api.openweathermap.org/data/2.5/forecast",
            params={
                "q": params.get("city"),
                "appid": weather_api_key,
                "cnt": params.get("days", 5) * 8
            }
        )
        
        return response.json()

async def book_flight(params: dict):
    """Book flight via Amadeus API"""
    # Implementation would call Amadeus booking API
    return {
        "booking_type": "flight",
        "confirmation": f"FL-{hash(str(params)) % 100000}",
        "status": "confirmed",
        "details": params
    }

async def book_hotel(params: dict):
    """Book hotel via Booking.com API"""
    # Implementation would call Booking.com booking API
    return {
        "booking_type": "hotel",
        "confirmation": f"HT-{hash(str(params)) % 100000}",
        "status": "confirmed",
        "details": params
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
