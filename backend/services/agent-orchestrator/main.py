"""
AI Agent Orchestrator - Coordinates multiple AI agents for trip planning
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
import httpx
import json

app = FastAPI(title="AI Agent Orchestrator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LLM
llm = ChatOpenAI(
    model="gpt-4-turbo-preview",
    temperature=0.7,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# MCP Gateway URL
MCP_GATEWAY_URL = os.getenv("MCP_GATEWAY_URL", "http://mcp-service:8007")
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://rag-service:8006")

class TripPlanRequest(BaseModel):
    destination: str
    start_date: str
    end_date: str
    budget: Optional[float] = None
    travelers: int = 1
    preferences: Optional[List[str]] = []
    conversation_history: Optional[List[Dict]] = []

class AgentResponse(BaseModel):
    response: str
    trip_plan: Optional[Dict] = None
    actions_taken: List[str] = []

async def call_mcp_tool(tool_name: str, params: dict) -> dict:
    """Call MCP tool via gateway"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MCP_GATEWAY_URL}/mcp/execute",
            json={"tool": tool_name, "params": params},
            timeout=30.0
        )
        return response.json()

async def call_rag(query: str, document_types: Optional[List[str]] = None) -> dict:
    """Call RAG service"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{RAG_SERVICE_URL}/rag/query",
            json={"query": query, "document_types": document_types, "top_k": 5},
            timeout=30.0
        )
        return response.json()

def create_planning_agent():
    """Create planning agent with tools"""
    
    tools = [
        Tool(
            name="search_flights",
            description="Search for flights to a destination",
            func=lambda params: call_mcp_tool("search_flights", params)
        ),
        Tool(
            name="search_hotels",
            description="Search for hotels in a city",
            func=lambda params: call_mcp_tool("search_hotels", params)
        ),
        Tool(
            name="get_weather",
            description="Get weather forecast for a city",
            func=lambda params: call_mcp_tool("get_weather", params)
        ),
        Tool(
            name="search_knowledge",
            description="Search travel knowledge base for information",
            func=lambda query: call_rag(query)
        )
    ]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert travel planning AI assistant. Help users plan their trips by:
1. Understanding their preferences and constraints
2. Searching for flights, hotels, and activities
3. Providing personalized recommendations
4. Creating detailed itineraries

Use the available tools to gather information and provide comprehensive trip plans.
Be conversational and helpful."""),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    
    agent = create_openai_functions_agent(llm, tools, prompt)
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    
    return AgentExecutor(agent=agent, tools=tools, memory=memory, verbose=True)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "agent-orchestrator"}

@app.post("/agent/plan-trip", response_model=AgentResponse)
async def plan_trip(request: TripPlanRequest):
    """Plan trip using AI agent"""
    
    try:
        agent = create_planning_agent()
        
        # Build initial message
        message = f"""Plan a trip to {request.destination} from {request.start_date} to {request.end_date} for {request.travelers} traveler(s)."""
        
        if request.budget:
            message += f" Budget: ${request.budget}."
        
        if request.preferences:
            message += f" Preferences: {', '.join(request.preferences)}."
        
        # Execute agent
        result = agent.invoke({"input": message})
        
        # Extract actions taken
        actions = []
        if "search_flights" in result["output"].lower():
            actions.append("Searched for flights")
        if "search_hotels" in result["output"].lower():
            actions.append("Searched for hotels")
        if "weather" in result["output"].lower():
            actions.append("Checked weather forecast")
        if "knowledge" in result["output"].lower():
            actions.append("Consulted knowledge base")
        
        return AgentResponse(
            response=result["output"],
            actions_taken=actions
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/chat")
async def chat(message: str, conversation_history: Optional[List[Dict]] = None):
    """Chat with AI agent"""
    
    try:
        agent = create_planning_agent()
        
        # Set conversation history if provided
        if conversation_history:
            agent.memory.chat_memory = conversation_history
        
        result = agent.invoke({"input": message})
        
        return {
            "response": result["output"],
            "conversation_history": [
                {"role": msg.type, "content": msg.content}
                for msg in agent.memory.chat_memory.messages
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)
