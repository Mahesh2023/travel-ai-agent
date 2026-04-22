# Travel AI Agent Platform

An AI-powered travel agency platform with intelligent agents for trip planning, booking, and customer support.

## Features

- **AI Trip Planning Agent**: Personalized itinerary generation using RAG
- **Booking Agent**: Automated flight, hotel, and activity bookings
- **Support Agent**: 24/7 customer service with natural language understanding
- **Research Agent**: Destination insights and travel recommendations
- **RAG System**: Knowledge base with vector embeddings for travel data
- **MCP Integration**: Model Context Protocol for external API access

## Tech Stack

### Backend
- Python 3.11+
- FastAPI
- LangChain
- OpenAI GPT-4
- PostgreSQL
- Redis
- Pinecone (Vector DB)

### Frontend
- Next.js 14
- TypeScript
- TailwindCSS
- shadcn/ui

### Infrastructure
- Docker
- Render (Deployment)

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL
- Pinecone API key
- OpenAI API key

### Installation

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Environment Variables

```env
# Backend
OPENAI_API_KEY=your_openai_key
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENVIRONMENT=your_pinecone_env
DATABASE_URL=postgresql://user:pass@localhost/travel
REDIS_URL=redis://localhost:6379
AMADEUS_API_KEY=your_amadeus_key
AMADEUS_SECRET=your_amadeus_secret
BOOKING_API_KEY=your_booking_key
WEATHER_API_KEY=your_weather_key
VIATOR_API_KEY=your_viator_key

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

## Deployment

This project is configured for deployment on Render. See `render.yaml` for configuration.

## License

MIT
