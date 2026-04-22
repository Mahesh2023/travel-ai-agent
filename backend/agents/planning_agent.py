"""
Trip Planning AI Agent
"""

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from config import settings
import json

class PlanningAgent:
    """AI agent for trip planning"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.7,
            openai_api_key=settings.openai_api_key
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert travel planner. Create detailed, personalized trip itineraries.
            Consider:
            - Budget optimization
            - Time management
            - Local experiences
            - Transportation between locations
            - Restaurant recommendations
            - Cultural insights
            
            Provide a day-by-day breakdown with specific recommendations."""),
            ("human", """Plan a trip to {destination} from {start_date} to {end_date} with a budget of ${budget}.
            
            Preferences: {preferences}
            
            Create a detailed itinerary with:
            1. Day-by-day schedule
            2. Recommended activities
            3. Restaurant suggestions
            4. Transportation tips
            5. Budget breakdown""")
        ])
        
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
    
    def generate_plan(self, destination: str, start_date: str, end_date: str, budget: float, preferences: str = None):
        """Generate trip plan"""
        try:
            result = self.chain.run(
                destination=destination,
                start_date=start_date,
                end_date=end_date,
                budget=budget,
                preferences=preferences or "No specific preferences"
            )
            
            return {
                "destination": destination,
                "start_date": start_date,
                "end_date": end_date,
                "budget": budget,
                "itinerary": result,
                "status": "generated"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "failed"
            }
