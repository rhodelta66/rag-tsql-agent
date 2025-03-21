from typing import List, Dict, Any, Optional
import logging
from .embeddings import ProcedureEmbeddings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProcedureRetriever:
    """
    Retrieve relevant stored procedures based on user queries.
    """
    
    def __init__(self, embeddings: ProcedureEmbeddings):
        """
        Initialize the procedure retriever.
        
        Args:
            embeddings: ProcedureEmbeddings instance
        """
        self.embeddings = embeddings
    
    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant procedures for a query.
        
        Args:
            query: User query
            k: Number of results to return
            
        Returns:
            List of dictionaries containing relevant procedures
        """
        # Search for similar procedures
        results = self.embeddings.search(query, k)
        
        # Log results
        logger.info(f"Retrieved {len(results)} procedures for query: {query}")
        
        return results
    
    def retrieve_with_filter(self, query: str, filter_func, k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant procedures with a filter function.
        
        Args:
            query: User query
            filter_func: Function that takes a procedure and returns True if it should be included
            k: Number of results to return
            
        Returns:
            List of dictionaries containing relevant procedures
        """
        # Search for similar procedures
        all_results = self.embeddings.search(query, k * 2)  # Get more results to account for filtering
        
        # Apply filter
        filtered_results = [result for result in all_results if filter_func(result)]
        
        # Limit to k results
        results = filtered_results[:k]
        
        # Log results
        logger.info(f"Retrieved {len(results)} procedures for query: {query} (after filtering)")
        
        return results
    
    def retrieve_ui_components(self, query: str, component_type: Optional[str] = None, k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve procedures with specific UI components.
        
        Args:
            query: User query
            component_type: Type of UI component to filter for (modal_text, modal_input, modal_button, toast)
            k: Number of results to return
            
        Returns:
            List of dictionaries containing relevant procedures
        """
        if component_type:
            # Filter for procedures with the specified component type
            def filter_func(procedure):
                if "metadata" in procedure and "ui_components" in procedure["metadata"]:
                    components = procedure["metadata"]["ui_components"]
                    return component_type in components and len(components[component_type]) > 0
                return False
                
            return self.retrieve_with_filter(query, filter_func, k)
        else:
            # No component type filter, just retrieve based on query
            return self.retrieve(query, k)
