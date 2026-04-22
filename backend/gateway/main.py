"""
API Gateway - Routes requests to microservices
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from typing import Dict
import redis

app = FastAPI(title="API Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
SERVICES = {
    "search": os.getenv("SEARCH_SERVICE_URL", "http://localhost:8001"),
    "booking": os.getenv("BOOKING_SERVICE_URL", "http://localhost:8002"),
    "inventory": os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8003"),
    "payment": os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8004"),
    "user": os.getenv("USER_SERVICE_URL", "http://localhost:8005"),
    "rag": os.getenv("RAG_SERVICE_URL", "http://localhost:8006"),
    "mcp": os.getenv("MCP_SERVICE_URL", "http://localhost:8007"),
    "notification": os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8008")
}

# Redis for rate limiting
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

async def proxy_request(service: str, path: str, method: str, body: dict = None, headers: Dict = None):
    """Proxy request to microservice"""
    
    service_url = SERVICES.get(service)
    if not service_url:
        raise HTTPException(status_code=503, detail=f"Service {service} not available")
    
    url = f"{service_url}{path}"
    
    async with httpx.AsyncClient() as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, json=body, headers=headers)
            elif method == "PUT":
                response = await client.put(url, json=body, headers=headers)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")
            
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "gateway"}

# Search endpoints
@app.api_route("/api/search/{path:path}", methods=["GET", "POST"])
async def search_proxy(request: Request, path: str):
    body = await request.json() if request.method in ["POST", "PUT"] else None
    return await proxy_request("search", f"/{path}", request.method, body, dict(request.headers))

# Booking endpoints
@app.api_route("/api/bookings/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def booking_proxy(request: Request, path: str):
    body = await request.json() if request.method in ["POST", "PUT"] else None
    return await proxy_request("booking", f"/{path}", request.method, body, dict(request.headers))

# Inventory endpoints
@app.api_route("/api/inventory/{path:path}", methods=["GET", "POST", "PUT"])
async def inventory_proxy(request: Request, path: str):
    body = await request.json() if request.method in ["POST", "PUT"] else None
    return await proxy_request("inventory", f"/{path}", request.method, body, dict(request.headers))

# Payment endpoints
@app.api_route("/api/payments/{path:path}", methods=["GET", "POST", "PUT"])
async def payment_proxy(request: Request, path: str):
    body = await request.json() if request.method in ["POST", "PUT"] else None
    return await proxy_request("payment", f"/{path}", request.method, body, dict(request.headers))

# User endpoints
@app.api_route("/api/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def auth_proxy(request: Request, path: str):
    body = await request.json() if request.method in ["POST", "PUT"] else None
    return await proxy_request("user", f"/{path}", request.method, body, dict(request.headers))

# RAG endpoints
@app.api_route("/api/rag/{path:path}", methods=["GET", "POST", "DELETE"])
async def rag_proxy(request: Request, path: str):
    body = await request.json() if request.method in ["POST", "PUT"] else None
    return await proxy_request("rag", f"/{path}", request.method, body, dict(request.headers))

# MCP endpoints
@app.api_route("/api/mcp/{path:path}", methods=["GET", "POST"])
async def mcp_proxy(request: Request, path: str):
    body = await request.json() if request.method in ["POST", "PUT"] else None
    return await proxy_request("mcp", f"/{path}", request.method, body, dict(request.headers))

# Notification endpoints
@app.api_route("/api/notifications/{path:path}", methods=["GET", "POST"])
async def notification_proxy(request: Request, path: str):
    body = await request.json() if request.method in ["POST", "PUT"] else None
    return await proxy_request("notification", f"/{path}", request.method, body, dict(request.headers))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
