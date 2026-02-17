import os
from langchain_community.vectorstores import Qdrant
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Configuration
DB_PATH = "./qdrant_db"
COLLECTION_NAME = "research_memory"

class MemoryManager:
    def __init__(self):
        # ---------------------------------------------------------
        # FINAL FIX: Using the newest standard embedding model.
        # This fixes the "404 models/embedding-001" error.
        # ---------------------------------------------------------
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        
        # Initialize Qdrant Client (Local persistence)
        self.client = QdrantClient(path=DB_PATH)
        
        # Create Collection if it doesn't exist
        try:
            self.client.get_collection(COLLECTION_NAME)
        except:
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE)
            )

        # Connect LangChain wrapper to Qdrant
        self.vector_store = Qdrant(
            client=self.client,
            collection_name=COLLECTION_NAME,
            embeddings=self.embeddings,
        )

    def search_memory(self, query, threshold=0.8):
        """Semantic search to find if we already answered this."""
        try:
            results = self.vector_store.similarity_search_with_score(query, k=1)
            
            if not results: return None
            
            doc, score = results[0]
            if score > threshold:
                return {
                    "content": doc.page_content, 
                    "score": score
                }
        except Exception:
            return None
        return None

    def save_memory(self, query, answer, mode):
        """Saves the research result to Qdrant."""
        self.vector_store.add_texts(
            texts=[f"Question: {query}\nAnswer: {answer}"],
            metadatas=[{"mode": mode, "query": query}]
        )