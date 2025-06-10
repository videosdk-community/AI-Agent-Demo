"""
HR Policy RAG Handler
Handles retrieval of HR policy information from Pinecone vector store.
"""

import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone
import logging

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HRPolicyRAGHandler:
    """Handles retrieval of HR policy information from Pinecone vector store."""
    
    def __init__(self):
        self.embeddings_model = None
        self.pinecone_index = None
        self.initialized = False
        
    async def initialize(self):
        """Initialize the RAG handler with Pinecone and OpenAI connections."""
        try:
            # Initialize OpenAI embeddings
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
                
            self.embeddings_model = OpenAIEmbeddings(
                openai_api_key=openai_api_key,
                request_timeout=60
            )
            
            # Initialize Pinecone
            pinecone_api_key = os.getenv("PINECONE_API_KEY")
            pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")
            
            if not pinecone_api_key or not pinecone_index_name:
                raise ValueError("PINECONE_API_KEY or PINECONE_INDEX_NAME not found in environment variables")
            
            pc = Pinecone(api_key=pinecone_api_key)
            self.pinecone_index = pc.Index(pinecone_index_name)
            
            self.initialized = True
            logger.info("HR Policy RAG Handler initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize HR Policy RAG Handler: {e}")
            raise
    
    async def search_hr_policy(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search for relevant HR policy information based on the query.
        
        Args:
            query: The search query
            top_k: Number of top results to return
            
        Returns:
            List of relevant HR policy chunks with metadata
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Generate embedding for the query
            query_embedding = self.embeddings_model.embed_query(query)
            
            # Search in Pinecone
            search_results = self.pinecone_index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter={"type": "hr_policy"}  # Filter for HR policy documents only
            )
            
            # Format results
            formatted_results = []
            for match in search_results.matches:
                formatted_results.append({
                    "content": match.metadata.get("text", ""),
                    "page": match.metadata.get("page", ""),
                    "source": match.metadata.get("source", ""),
                    "score": match.score,
                    "id": match.id
                })
            
            logger.info(f"Found {len(formatted_results)} relevant HR policy chunks for query: {query}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching HR policy: {e}")
            return []
    
    def format_context_for_llm(self, search_results: List[Dict], query: str) -> str:
        """
        Format search results into context for the LLM.
        
        Args:
            search_results: Results from Pinecone search
            query: Original query
            
        Returns:
            Formatted context string
        """
        if not search_results:
            return "No relevant HR policy information found for your query."
        
        context_parts = [
            f"Based on the HR Policy Manual, here's relevant information for your query: '{query}'\n"
        ]
        
        for i, result in enumerate(search_results, 1):
            context_parts.append(
                f"--- HR Policy Reference {i} (Page {result['page']}) ---\n"
                f"{result['content']}\n"
            )
        
        context_parts.append(
            "\nPlease provide a helpful response based on this HR policy information. "
            "If the information doesn't fully address the query, mention that additional "
            "HR resources or direct contact with HR may be needed."
        )
        
        return "\n".join(context_parts)

# Global instance
hr_rag_handler = HRPolicyRAGHandler()

async def search_hr_policy_knowledge(query: str, max_results: int = 3) -> str:
    """
    Function tool to search HR policy knowledge base.
    
    Args:
        query: The HR policy question or topic to search for
        max_results: Maximum number of relevant policy sections to return
        
    Returns:
        Formatted HR policy information relevant to the query
    """
    try:
        search_results = await hr_rag_handler.search_hr_policy(query, top_k=max_results)
        formatted_context = hr_rag_handler.format_context_for_llm(search_results, query)
        return formatted_context
    except Exception as e:
        logger.error(f"Error in search_hr_policy_knowledge: {e}")
        return f"I apologize, but I'm having trouble accessing the HR policy database right now. Please try again later or contact HR directly for assistance." 