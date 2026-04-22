"""
MCP Server for Travel API Tools
"""

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import httpx
import os
from config import settings

travel_mcp_server = Server("travel-agency-tools")

@travel_mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools"""
    return [
        Tool(
            name="search_flights",
            description="Search for flights using Amadeus API",
            inputSchema={
                "type": "object",
                "properties": {
                    "origin": {"type": "string", "description": "Origin airport code"},
                    "destination": {"type": "string", "description": "Destination airport code"},
                    "departure_date": {"type": "string", "description": "Departure date (YYYY-MM-DD)"},
                    "passengers": {"type": "integer", "description": "Number of passengers"}
                },
                "required": ["origin", "destination", "departure_date"]
            }
        ),
        Tool(
            name="search_hotels",
            description="Search for hotels",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"},
                    "check_in": {"type": "string", "description": "Check-in date (YYYY-MM-DD)"},
                    "check_out": {"type": "string", "description": "Check-out date (YYYY-MM-DD)"},
                    "guests": {"type": "integer", "description": "Number of guests"}
                },
                "required": ["city", "check_in", "check_out"]
            }
        ),
        Tool(
            name="get_weather",
            description="Get weather forecast",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"},
                    "days": {"type": "integer", "description": "Number of days (1-7)"}
                },
                "required": ["city"]
            }
        )
    ]

@travel_mcp_server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute MCP tool calls"""
    
    if name == "search_flights":
        result = await search_flights(arguments)
        return [TextContent(type="text", text=str(result))]
    
    elif name == "search_hotels":
        result = await search_hotels(arguments)
        return [TextContent(type="text", text=str(result))]
    
    elif name == "get_weather":
        result = await get_weather(arguments)
        return [TextContent(type="text", text=str(result))]
    
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def search_flights(params):
    """Search flights (demo implementation)"""
    # In production, integrate with Amadeus API
    return {
        "flights": [
            {
                "airline": "Demo Airline",
                "flight_number": "DA123",
                "origin": params["origin"],
                "destination": params["destination"],
                "departure_time": "10:00",
                "arrival_time": "14:00",
                "price": 299
            }
        ],
        "status": "demo_mode"
    }

async def search_hotels(params):
    """Search hotels (demo implementation)"""
    # In production, integrate with Booking.com API
    return {
        "hotels": [
            {
                "name": "Demo Hotel",
                "city": params["city"],
                "price_per_night": 150,
                "rating": 4.5,
                "amenities": ["WiFi", "Pool", "Restaurant"]
            }
        ],
        "status": "demo_mode"
    }

async def get_weather(params):
    """Get weather (demo implementation)"""
    # In production, integrate with OpenWeatherMap API
    return {
        "city": params["city"],
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

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await travel_mcp_server.run(
            read_stream,
            write_stream,
            travel_mcp_server.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
