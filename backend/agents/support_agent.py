"""
Customer Support AI Agent
"""

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from config import settings

class SupportAgent:
    """AI agent for customer support"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.5,
            openai_api_key=settings.openai_api_key
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful travel customer support agent. 
            Assist customers with:
            - Booking modifications
            - Cancellations
            - Travel advice
            - Problem resolution
            
            Be empathetic, clear, and solution-oriented."""),
            ("human", """Customer message: {message}
            
            Context: {context}
            
            Provide a helpful response.""")
        ])
        
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
    
    def respond(self, message: str, context: str = None):
        """Generate support response"""
        try:
            result = self.chain.run(
                message=message,
                context=context or "No additional context"
            )
            
            return {
                "response": result,
                "status": "success"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "failed"
            }
