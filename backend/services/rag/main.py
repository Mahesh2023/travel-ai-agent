"""
RAG Service - Knowledge base retrieval for AI
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pinecone import Pinecone, ServerlessSpec
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from pydantic import BaseModel
from typing import Optional, List
import os
import redis

app = FastAPI(title="RAG Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large",
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

llm = ChatOpenAI(
    model="gpt-4-turbo-preview",
    temperature=0.5,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = "travel-knowledge-base"

if index_name not in [index.name for index in pc.list_indexes()]:
    pc.create_index(
        name=index_name,
        dimension=3072,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )

index = pc.Index(index_name)

# Redis for caching
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    length_function=len
)

class QueryRequest(BaseModel):
    query: str
    document_types: Optional[List[str]] = None
    top_k: int = 5

class EmbedRequest(BaseModel):
    document_type: str
    content: str
    metadata: dict

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "rag"}

@app.post("/rag/query")
async def query_knowledge_base(request: QueryRequest):
    """Query knowledge base with RAG"""
    
    # Check cache
    cache_key = f"rag:{hash(request.query)}"
    cached = redis_client.get(cache_key)
    if cached:
        return eval(cached)
    
    # Embed query
    query_embedding = embeddings.embed_query(request.query)
    
    # Build filter
    query_filter = {}
    if request.document_types:
        query_filter["document_type"] = {"$in": request.document_types}
    
    # Search vector database
    results = index.query(
        vector=query_embedding,
        filter=query_filter if query_filter else None,
        top_k=request.top_k,
        include_metadata=True
    )
    
    # Extract context
    context = "\n\n".join([
        match['metadata']['text'] for match in results['matches']
    ])
    
    # Generate response
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a travel expert. Use the provided context to answer questions."),
        ("human", """Context: {context}
        
        Question: {question}
        
        Provide a helpful answer based on the context.""")
    ])
    
    chain = LLMChain(llm=llm, prompt=prompt)
    response = chain.run(context=context, question=request.query)
    
    result = {
        "response": response,
        "sources": [
            {
                "text": match['metadata']['text'],
                "score": match['score'],
                "document_type": match['metadata'].get('document_type')
            }
            for match in results['matches']
        ]
    }
    
    # Cache result
    redis_client.setex(cache_key, 300, str(result))
    
    return result

@app.post("/rag/embed")
async def embed_document(request: EmbedRequest):
    """Embed and store document"""
    
    chunks = text_splitter.split_text(request.content)
    chunk_embeddings = embeddings.embed_documents(chunks)
    
    vectors = []
    for i, (chunk, embedding) in enumerate(zip(chunks, chunk_embeddings)):
        vectors.append({
            "id": f"{request.metadata.get('id', 'doc')}_{request.document_type}_{i}",
            "values": embedding,
            "metadata": {
                **request.metadata,
                "document_type": request.document_type,
                "chunk_index": i,
                "text": chunk
            }
        })
    
    index.upsert(vectors=vectors)
    
    return {"message": "Document embedded successfully", "chunks": len(chunks)}

@app.delete("/rag/{document_id}")
async def delete_document(document_id: str):
    """Delete document from vector database"""
    
    # Find all chunks for this document
    results = index.query(
        vector=[0] * 3072,  # Dummy vector
        filter={"document_id": document_id},
        top_k=100,
        include_metadata=True
    )
    
    # Delete all chunks
    ids_to_delete = [match['id'] for match in results['matches']]
    if ids_to_delete:
        index.delete(ids=ids_to_delete)
    
    return {"message": "Document deleted", "chunks_deleted": len(ids_to_delete)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
