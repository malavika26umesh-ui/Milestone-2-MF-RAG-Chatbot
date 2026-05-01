import os
from runtime.phase_5_retrieval.retriever import MFRetriever
from runtime.phase_6_generation.generator import GroqGenerator
from runtime.phase_7_safety.router import QueryRouter, QueryCategory

class SafetyManager:
    def __init__(self, educational_url: str = "https://www.amfiindia.com/investor-corner"):
        self.router = QueryRouter()
        self.educational_url = educational_url
        self.retriever = None
        self.generator = None

    def _lazy_init_rag(self):
        """Initializes RAG components only when needed to save time on routing-only tasks."""
        if not self.retriever:
            self.retriever = MFRetriever()
        if not self.generator:
            self.generator = GroqGenerator()

    def answer(self, query: str) -> str:
        """
        Orchestrates the safety check and RAG flow.
        """
        category = self.router.route(query)
        
        if category == QueryCategory.PII_DETECTED:
            return (
                "For your security, please do not share personal identifiers like PAN, Aadhaar, or account numbers. "
                "I have blocked this request for privacy reasons."
            )
            
        if category == QueryCategory.ADVISORY:
            return (
                "I am a facts-only assistant and cannot provide investment advice, recommendations, or comparisons. "
                "Please refer to official investor education resources for more guidance."
            )
            
        if category == QueryCategory.OUT_OF_SCOPE:
            return "I'm sorry, but that question is outside the scope of my mutual fund knowledge base."

        # If FAQ, proceed to RAG
        try:
            self._lazy_init_rag()
            print("Query categorized as FAQ. Proceeding to retrieval...")
            context_chunks = self.retriever.retrieve(query, k=3)
            
            if not context_chunks:
                return "I'm sorry, I couldn't find any relevant information in the indexed sources to answer that question."
                
            print("Context retrieved. Proceeding to generation...")
            return self.generator.generate_answer(query, context_chunks)
            
        except Exception as e:
            print(f"Error in SafetyManager.answer: {e}")
            return "I encountered an error while processing your request. Please try again later."
