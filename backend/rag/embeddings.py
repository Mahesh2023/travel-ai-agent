"""
Travel embeddings for RAG system
"""

from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pinecone import Pinecone, ServerlessSpec
from config import settings
import os

class TravelEmbeddings:
    """Handle travel content embeddings"""
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
            openai_api_key=settings.openai_api_key
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            length_function=len
        )
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index_name = "travel-knowledge-base"
        
        # Create index if it doesn't exist
        if self.index_name not in [index.name for index in self.pc.list_indexes()]:
            self.pc.create_index(
                name=self.index_name,
                dimension=3072,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
        
        self.index = self.pc.Index(self.index_name)
    
    def embed_and_store(self, document_type: str, content: str, metadata: dict):
        """Embed document and store in vector database"""
        chunks = self.text_splitter.split_text(content)
        embeddings = self.embeddings.embed_documents(chunks)
        
        vectors = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vectors.append({
                "id": f"{metadata.get('id', 'doc')}_{document_type}_{i}",
                "values": embedding,
                "metadata": {
                    **metadata,
                    "document_type": document_type,
                    "chunk_index": i,
                    "text": chunk
                }
            })
        
        self.index.upsert(vectors=vectors)
        return f"{metadata.get('id', 'doc')}_{document_type}"
