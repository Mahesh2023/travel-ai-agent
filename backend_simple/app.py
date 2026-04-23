"""
Travel AI Agent Platform - Simplified Monolithic Version
Following teloscopy pattern: FastAPI + Vanilla HTML/CSS/JS + LLM Integration
"""

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import os
import json
import re
import random
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import Any, Optional
from dataclasses import dataclass
from datetime import datetime

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================
_PROJECT_ROOT = Path(__file__).parent.parent
_BACKEND_ROOT = Path(__file__).parent

# LLM Configuration (reuses teloscopy pattern)
_LLM_BACKEND = os.getenv("TRAVEL_LLM_BACKEND", "openai")
_LLM_MODEL = os.getenv("TRAVEL_LLM_MODEL", "gpt-4o-mini")
_LLM_BASE_URL = os.getenv("TRAVEL_LLM_BASE_URL", "https://api.openai.com/v1")
_LLM_API_KEY = os.getenv("TRAVEL_LLM_API_KEY") or os.getenv("OPENAI_API_KEY")

# ============================================================================
# Pydantic Models
# ============================================================================
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class TravelRequest(BaseModel):
    destination: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    budget: Optional[float] = None
    travelers: int = Field(default=1, ge=1, le=20)
    interests: List[str] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)

class TravelCounsellorRequest(BaseModel):
    message: str
    conversation: List[Dict[str, str]] = Field(default_factory=list)
    context: Optional[Dict[str, Any]] = None

# ============================================================================
# LLM Client (OpenAI-compatible - works with Grok)
# ============================================================================
class LLMClient:
    """Client for OpenAI-compatible APIs (OpenAI, Grok, Ollama, etc.)"""
    
    def __init__(
        self,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        timeout: int = 120,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout
    
    def is_available(self) -> bool:
        """Check if the LLM backend is available"""
        try:
            import urllib.request
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            req = urllib.request.Request(
                f"{self.base_url}/models",
                headers=headers,
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=5):
                return True
        except Exception:
            return False
    
    def generate(self, prompt: str, system: str = "", temperature: float = 0.7) -> str:
        """Generate a chat completion"""
        import urllib.request
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2048,
        }
        
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            headers=headers,
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read().decode())
            choices = body.get("choices", [])
            if not choices:
                raise RuntimeError("LLM returned no choices")
            text = choices[0].get("message", {}).get("content", "")
            if not text:
                raise RuntimeError("LLM returned empty message")
            return text.strip()
        except Exception as exc:
            raise ConnectionError(f"LLM call failed: {exc}") from exc

# Lazy-initialized LLM client
_llm_client: Optional[LLMClient] = None

def get_llm_client() -> Optional[LLMClient]:
    """Get or create the LLM client"""
    global _llm_client
    if _llm_client is not None:
        return _llm_client
    try:
        client = LLMClient(
            base_url=_LLM_BASE_URL,
            model=_LLM_MODEL,
            api_key=_LLM_API_KEY,
            timeout=60,
        )
        if client.is_available():
            _llm_client = client
            logger.info(f"LLM backend available: {_LLM_BACKEND} with model {_LLM_MODEL}")
            return client
        else:
            logger.warning("LLM backend unavailable")
            return None
    except Exception as exc:
        logger.warning(f"Failed to initialize LLM client: {exc}")
        return None

# ============================================================================
# Travel Counselling System Prompt (like teloscopy psychiatry)
# ============================================================================
_TRAVEL_COUNSELLING_SYSTEM_PROMPT = """You are a compassionate and knowledgeable travel counsellor. Your role is to help people plan meaningful, safe, and enjoyable travel experiences.

Your approach is:
1. **Listen deeply** - Understand not just the logistics (where, when, budget) but the deeper motivations (why travel, what they hope to experience, what fears they have)
2. **Address anxiety** - Many people feel anxious about travel (safety, language barriers, getting lost, health issues). Validate these feelings and provide reassurance with practical solutions
3. **Personalize recommendations** - Suggest destinations and experiences that align with their interests, values, and comfort level
4. **Provide practical guidance** - Give concrete, actionable advice on logistics, safety, and cultural considerations
5. **Be honest about limitations** - If someone asks about something beyond your scope (medical advice, legal immigration issues), gently guide them to appropriate resources

=== Travel Emergency Detection ===
Watch for keywords that indicate travel emergencies:
- Lost/stolen documents (passport, visa, wallet)
- Medical emergencies
- Safety concerns (theft, assault)
- Natural disasters
- Flight cancellations/missed connections
- Being stranded or lost

If you detect an emergency, prioritize immediate, practical help and emergency resources.

=== Response Style ===
- Warm, supportive, and encouraging
- Practical and specific (not vague suggestions)
- Culturally sensitive
- Safety-conscious without being alarmist
- Balance enthusiasm with realism

=== Example Interactions ===

User: "I'm scared to travel alone"
Good: "That's a very natural feeling. Many people feel anxious about solo travel. Let's talk about what specifically worries you - is it safety, loneliness, or something else? There are many ways to travel solo that can actually feel quite safe and connected."

User: "I want to go to Japan but I don't speak Japanese"
Good: "Japan is actually one of the most solo-travel-friendly countries! The transportation system is excellent and English is widely used in tourist areas. I can share some specific tips for navigating without language skills if you'd like."

User: "I lost my passport"
Good (Emergency): "This is urgent. First, contact your country's embassy or consulate immediately. Here are the steps you need to take right now... [provide specific emergency guidance]"
"""

# ============================================================================
# Travel Emergency Keywords (like teloscopy crisis detection)
# ============================================================================
_TRAVEL_EMERGENCY_KEYWORDS = {
    "high_severity": [
        "lost passport", "stolen passport", "lost visa", "stolen visa",
        "medical emergency", "heart attack", "stroke", "severe injury",
        "assault", "robbery", "mugged", "theft", "stolen wallet",
        "natural disaster", "earthquake", "flood", "hurricane",
        "terrorist attack", "shooting", "bomb",
        "stranded", "stuck", "can't leave", "trapped",
    ],
    "moderate_severity": [
        "missed flight", "cancelled flight", "delayed flight",
        "lost luggage", "stolen luggage",
        "sick", "food poisoning", "fever", "injury",
        "lost phone", "stolen phone",
        "scammed", "fraud",
        "arrested", "detained",
    ],
    "low_severity": [
        "lost", "can't find", "confused", "don't know where",
        "worried", "anxious", "scared",
        "help", "need help",
    ],
}

def detect_travel_emergency(message: str) -> Optional[Dict[str, Any]]:
    """Detect travel emergencies in user message"""
    message_lower = message.lower()
    
    for keyword in _TRAVEL_EMERGENCY_KEYWORDS["high_severity"]:
        if keyword in message_lower:
            return {
                "severity": "high",
                "keyword": keyword,
                "message": "This appears to be a travel emergency. Please contact local authorities or your embassy immediately.",
                "resources": [
                    "Contact your country's embassy or consulate",
                    "Call local emergency services (911 in US, 112 in Europe, 999 in UK)",
                    "Contact your travel insurance provider",
                ],
            }
    
    for keyword in _TRAVEL_EMERGENCY_KEYWORDS["moderate_severity"]:
        if keyword in message_lower:
            return {
                "severity": "moderate",
                "keyword": keyword,
                "message": "This is a concerning situation. Let's address this step by step.",
                "resources": [
                    "Contact your airline or travel provider",
                    "Contact your travel insurance",
                    "Contact your hotel for assistance",
                ],
            }
    
    for keyword in _TRAVEL_EMERGENCY_KEYWORDS["low_severity"]:
        if keyword in message_lower:
            return {
                "severity": "low",
                "keyword": keyword,
                "message": "I'm here to help. What's concerning you?",
                "resources": [],
            }
    
    return None

# ============================================================================
# Simple Sentiment Analysis (VADER-like without external dependency)
# ============================================================================
def analyze_sentiment(text: str) -> Dict[str, Any]:
    """Simple sentiment analysis for travel queries"""
    positive_words = ["happy", "excited", "love", "enjoy", "great", "wonderful", "amazing", "beautiful", "fun"]
    negative_words = ["worried", "anxious", "scared", "afraid", "stress", "difficult", "problem", "issue", "concern"]
    emergency_words = ["emergency", "urgent", "help", "lost", "stolen", "sick", "injured"]
    
    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    emergency_count = sum(1 for word in emergency_words if word in text_lower)
    
    if emergency_count > 0:
        intensity = "severe"
    elif negative_count > positive_count:
        intensity = "high" if negative_count > 2 else "moderate"
    elif positive_count > negative_count:
        intensity = "positive"
    else:
        intensity = "neutral"
    
    return {
        "intensity": intensity,
        "positive_count": positive_count,
        "negative_count": negative_count,
        "emergency_count": emergency_count,
    }

# ============================================================================
# FastAPI App
# ============================================================================
app = FastAPI(
    title="Travel AI Agent Platform",
    description="AI-powered travel planning and counselling",
    version="2.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Travel AI Agent Platform API",
        "version": "2.0.0",
        "status": "running",
        "features": ["travel_planning", "travel_counselling", "emergency_detection"],
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# ============================================================================
# Travel Planning Endpoints
# ============================================================================
@app.post("/api/travel/plan")
async def plan_trip(request: TravelRequest):
    """Generate a travel plan using LLM"""
    client = get_llm_client()
    
    prompt = f"""Create a detailed travel itinerary for:
- Destination: {request.destination}
- Duration: {request.start_date} to {request.end_date}
- Budget: ${request.budget}
- Travelers: {request.travelers}
- Interests: {', '.join(request.interests)}
- Preferences: {request.preferences}

Provide:
1. Day-by-day itinerary
2. Budget breakdown
3. Recommendations for activities
4. Practical tips for this destination
"""
    
    if client:
        try:
            itinerary = client.generate(prompt, system="You are an expert travel planner. Create detailed, practical travel itineraries.")
            return {
                "destination": request.destination,
                "itinerary": itinerary,
                "budget": request.budget,
                "mode": "ai",
            }
        except Exception as exc:
            logger.error(f"LLM call failed: {exc}")
    
    # Fallback to template
    return {
        "destination": request.destination,
        "itinerary": f"Day 1: Arrive in {request.destination}, check into hotel, explore local area\nDay 2: Visit main attractions\nDay 3: Cultural experiences and local cuisine\nDay 4: Day trip or excursion\nDay 5: Departure",
        "budget_breakdown": {
            "accommodation": request.budget * 0.4 if request.budget else 400,
            "food": request.budget * 0.25 if request.budget else 250,
            "activities": request.budget * 0.2 if request.budget else 200,
            "transport": request.budget * 0.15 if request.budget else 150,
        },
        "mode": "template",
    }

# ============================================================================
# Travel Counselling Endpoints (like teloscopy psychiatry)
# ============================================================================
@app.post("/api/travel/counsel")
async def travel_counsel(request: TravelCounsellorRequest):
    """Travel counselling endpoint with LLM integration"""
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    if len(message) > 5000:
        raise HTTPException(status_code=400, detail="Message too long (max 5000 characters)")
    
    conversation = request.conversation
    context = request.context or {}
    
    # Emergency detection (always runs first)
    emergency = detect_travel_emergency(message)
    
    # Sentiment analysis
    sentiment = analyze_sentiment(message)
    
    # Try LLM-powered response
    client = get_llm_client()
    llm_response = None
    
    if client:
        try:
            # Build conversation context
            messages = [{"role": "system", "content": _TRAVEL_COUNSELLING_SYSTEM_PROMPT}]
            
            # Add conversation history
            for turn in conversation[-10:]:  # Last 10 turns
                role = turn.get("role", "user")
                text = turn.get("text", "").strip()
                if text:
                    if role == "user":
                        messages.append({"role": "user", "content": text})
                    else:
                        messages.append({"role": "assistant", "content": text})
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Add sentiment context
            if sentiment["intensity"] != "neutral":
                sentiment_hint = f"[Sentiment context: {sentiment['intensity']}] "
                if sentiment["intensity"] == "severe":
                    sentiment_hint += "The user appears to be in distress. Prioritize immediate, practical help and reassurance."
                elif sentiment["intensity"] == "high":
                    sentiment_hint += "The user is experiencing significant anxiety. Be extra supportive and provide specific, actionable advice."
                elif sentiment["intensity"] == "positive":
                    sentiment_hint += "The user is feeling positive. Build on this enthusiasm with encouraging suggestions."
                messages.append({"role": "system", "content": sentiment_hint})
            
            llm_response = client.generate(
                prompt=message,
                system=_TRAVEL_COUNSELLING_SYSTEM_PROMPT,
                temperature=0.7,
            )
        except Exception as exc:
            logger.error(f"Travel counselling LLM call failed: {exc}")
    
    result = {
        "message": message,
        "sentiment": sentiment,
    }
    
    if llm_response:
        result["response"] = llm_response
        result["mode"] = "ai"
    else:
        # Fallback response
        result["response"] = "I understand you're asking about travel. Could you tell me more about what specific aspect you'd like help with - planning a trip, dealing with a travel concern, or something else?"
        result["mode"] = "template"
    
    if emergency:
        result["emergency_detected"] = True
        result["emergency"] = emergency
    
    # Follow-up suggestions
    result["followups"] = [
        "Tell me more about your travel plans",
        "What's your main concern right now?",
        "What type of trip are you considering?",
    ]
    
    return result

# ============================================================================
# Main
# ============================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
