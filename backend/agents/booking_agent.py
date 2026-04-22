"""
Booking AI Agent
"""

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from config import settings
import httpx
import os

class BookingAgent:
    """AI agent for making bookings"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.3,
            openai_api_key=settings.openai_api_key
        )
    
    def make_booking(self, booking_type: str, details: dict):
        """Make booking through external APIs"""
        try:
            if booking_type == "flight":
                return self._book_flight(details)
            elif booking_type == "hotel":
                return self._book_hotel(details)
            elif booking_type == "activity":
                return self._book_activity(details)
            else:
                return {"error": "Unknown booking type", "status": "failed"}
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    def _book_flight(self, details: dict):
        """Book flight (placeholder for Amadeus API integration)"""
        # In production, integrate with Amadeus API
        return {
            "booking_type": "flight",
            "confirmation": f"FL-{hash(str(details)) % 100000}",
            "status": "confirmed",
            "details": details,
            "message": "Flight booked successfully (demo mode)"
        }
    
    def _book_hotel(self, details: dict):
        """Book hotel (placeholder for Booking.com API integration)"""
        # In production, integrate with Booking.com API
        return {
            "booking_type": "hotel",
            "confirmation": f"HT-{hash(str(details)) % 100000}",
            "status": "confirmed",
            "details": details,
            "message": "Hotel booked successfully (demo mode)"
        }
    
    def _book_activity(self, details: dict):
        """Book activity (placeholder for Viator API integration)"""
        # In production, integrate with Viator API
        return {
            "booking_type": "activity",
            "confirmation": f"AC-{hash(str(details)) % 100000}",
            "status": "confirmed",
            "details": details,
            "message": "Activity booked successfully (demo mode)"
        }
