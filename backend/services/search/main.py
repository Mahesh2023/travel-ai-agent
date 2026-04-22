"""
Search Service - High-performance hotel/flight search
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from elasticsearch import Elasticsearch
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
import redis

app = FastAPI(title="Search Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Elasticsearch client
es = Elasticsearch(os.getenv("ELASTICSEARCH_URL", "http://localhost:9200"))

# Redis client for caching
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

class SearchRequest(BaseModel):
    query: str
    location: Optional[str] = None
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    guests: Optional[int] = 1
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    amenities: Optional[List[str]] = None

class SearchResult(BaseModel):
    id: str
    name: str
    location: str
    price: float
    rating: float
    amenities: List[str]
    image: str
    available: bool

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "search"}

@app.post("/search/hotels", response_model=List[SearchResult])
async def search_hotels(request: SearchRequest):
    """Search hotels with filters"""
    
    # Check cache first
    cache_key = f"search:{hash(str(request.dict()))}"
    cached = redis_client.get(cache_key)
    if cached:
        return eval(cached)
    
    # Build Elasticsearch query
    query = {
        "query": {
            "bool": {
                "must": []
            }
        },
        "size": 20
    }
    
    # Add text search
    if request.query:
        query["query"]["bool"]["must"].append({
            "multi_match": {
                "query": request.query,
                "fields": ["name^2", "description", "location"]
            }
        })
    
    # Add filters
    if request.location:
        query["query"]["bool"]["must"].append({
            "term": {"location": request.location}
        })
    
    if request.min_price or request.max_price:
        price_range = {}
        if request.min_price:
            price_range["gte"] = request.min_price
        if request.max_price:
            price_range["lte"] = request.max_price
        query["query"]["bool"]["must"].append({
            "range": {"price": price_range}
        })
    
    if request.amenities:
        query["query"]["bool"]["must"].append({
            "terms": {"amenities": request.amenities}
        })
    
    try:
        response = es.search(index="hotels", body=query)
        
        results = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            results.append(SearchResult(
                id=hit["_id"],
                name=source["name"],
                location=source["location"],
                price=source["price"],
                rating=source["rating"],
                amenities=source["amenities"],
                image=source["image"],
                available=source["available"]
            ))
        
        # Cache results for 5 minutes
        redis_client.setex(cache_key, 300, str(results))
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index/hotel")
async def index_hotel(hotel_data: dict):
    """Index a hotel in Elasticsearch"""
    try:
        response = es.index(index="hotels", document=hotel_data)
        return {"message": "Hotel indexed", "id": response["_id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
