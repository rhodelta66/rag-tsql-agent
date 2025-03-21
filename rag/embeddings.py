from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os
import pickle
from typing import List, Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProcedureEmbeddings:
    """
    Generate and store embeddings for T-SQL stored procedures.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embeddings generator.
        
        Args:
            model_name: Name of the sentence-transformers model to use
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.procedure_data = []
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a text.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            Numpy array containing the embedding
        """
        return self.model.encode(text)
    
    def add_procedure(self, procedure_id: str, procedure_name: str, procedure_text: str, metadata: Dict[str, Any]) -> None:
        """
        Add a procedure to the index.
        
        Args:
            procedure_id: Unique identifier for the procedure
            procedure_name: Name of the procedure
            procedure_text: T-SQL definition of the procedure
            metadata: Additional metadata about the procedure
        """
        # Generate embedding
        embedding = self.generate_embedding(procedure_text)
        
        # Store procedure data
        self.procedure_data.append({
            "id": procedure_id,
            "name": procedure_name,
            "text": procedure_text,
            "metadata": metadata
        })
        
        # Add to index if it exists, otherwise create it
        if self.index is None:
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            faiss.normalize_L2(embedding.reshape(1, -1))
            self.index.add(embedding.reshape(1, -1))
        else:
            faiss.normalize_L2(embedding.reshape(1, -1))
            self.index.add(embedding.reshape(1, -1))
            
        logger.info(f"Added procedure {procedure_name} to index")
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar procedures.
        
        Args:
            query: Query text
            k: Number of results to return
            
        Returns:
            List of dictionaries containing similar procedures
        """
        if self.index is None or len(self.procedure_data) == 0:
            logger.warning("No procedures in index")
            return []
            
        # Generate query embedding
        query_embedding = self.generate_embedding(query)
        faiss.normalize_L2(query_embedding.reshape(1, -1))
        
        # Search index
        distances, indices = self.index.search(query_embedding.reshape(1, -1), min(k, len(self.procedure_data)))
        
        # Return results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.procedure_data):
                result = self.procedure_data[idx].copy()
                result["distance"] = float(distances[0][i])
                results.append(result)
                
        return results
    
    def save(self, directory: str) -> bool:
        """
        Save the index and procedure data to disk.
        
        Args:
            directory: Directory to save to
            
        Returns:
            True if successful, False otherwise
        """
        if self.index is None:
            logger.warning("No index to save")
            return False
            
        try:
            os.makedirs(directory, exist_ok=True)
            
            # Save index
            faiss.write_index(self.index, os.path.join(directory, "procedures.index"))
            
            # Save procedure data
            with open(os.path.join(directory, "procedures.pkl"), "wb") as f:
                pickle.dump(self.procedure_data, f)
                
            logger.info(f"Saved index and procedure data to {directory}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving index: {str(e)}")
            return False
    
    def load(self, directory: str) -> bool:
        """
        Load the index and procedure data from disk.
        
        Args:
            directory: Directory to load from
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load index
            index_path = os.path.join(directory, "procedures.index")
            if os.path.exists(index_path):
                self.index = faiss.read_index(index_path)
            else:
                logger.warning(f"Index file not found: {index_path}")
                return False
                
            # Load procedure data
            data_path = os.path.join(directory, "procedures.pkl")
            if os.path.exists(data_path):
                with open(data_path, "rb") as f:
                    self.procedure_data = pickle.load(f)
            else:
                logger.warning(f"Procedure data file not found: {data_path}")
                return False
                
            logger.info(f"Loaded index with {len(self.procedure_data)} procedures from {directory}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading index: {str(e)}")
            return False
