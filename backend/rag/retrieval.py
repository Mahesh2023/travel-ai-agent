"""
RAG retrieval system
"""

from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from pinecone import Pinecone
from config import settings

class TravelRAGRetrieval:
    """RAG retrieval for travel knowledge base"""
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
            openai_api_key=settings.openai_api_key
        )
        
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.5,
            openai_api_key=settings.openai_api_key
        )
        
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index = self.pc.Index("travel-knowledge-base")
    
    def query(self, query: str, document_types: list = None, filters: dict = None):
        """Query knowledge base with RAG"""
        # Embed query
        query_embedding = self.embeddings.embed_query(query)
        
        # Build filter
        query_filter = {}
        if document_types:
            query_filter["document_type"] = {"$in": document_types}
        if filters:
            query_filter.update(filters)
        
        # Search vector database
        results = self.index.query(
            vector=query_embedding,
            filter=query_filter if query_filter else None,
            top_k=5,
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
        
        from langchain.chains import LLMChain
        chain = LLMChain(llm=self.llm, prompt=prompt)
        response = chain.run(context=context, question=query)
        
        return {
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
