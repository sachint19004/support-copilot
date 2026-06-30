import os
import json
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from google import genai
from google.genai import types

# 1. Safely resolve local paths relative to this file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
ENV_PATH = os.path.join(BACKEND_DIR, ".env")
load_dotenv(dotenv_path=ENV_PATH)

# Initialize Gemini
api_key_val = os.getenv("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=api_key_val)

# 2. LOCAL ENGINE: Persistent on-disk vector store folder inside your repo
qdrant_client = QdrantClient(path=os.path.join(BACKEND_DIR, "qdrant_local_data"))
COLLECTION_NAME = "support_docs"

# 3. LOCAL CACHE: Point cleanly to the backend data directory
BM25_CACHE_PATH = os.path.join(BACKEND_DIR, "data", "chunks.json")

local_chunks = []
if os.path.exists(BM25_CACHE_PATH):
    with open(BM25_CACHE_PATH, "r", encoding="utf-8") as f:
        local_chunks = json.load(f)

def keyword_search(query: str, top_k: int = 3) -> list:
    """Fuzzy keyword matching over local cached JSON file."""
    query_terms = [t.lower() for t in query.split() if len(t) > 3]
    scored_chunks = []
    
    for chunk in local_chunks:
        text = chunk.get("text", "").lower()
        score = 0
        if "refund" in query.lower() and "refund" in text: score += 5
        if "return" in query.lower() and "return" in text: score += 5
        for term in query_terms:
            if term in text: score += 1
            
        if score > 0:
            scored_chunks.append({"chunk": chunk, "score": score})
            
    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    return [item["chunk"] for item in scored_chunks[:top_k]]

def hybrid_search(query: str, top_k: int = 3) -> list:
    """Attempts semantic search via local vector database; falls back to keyword matching."""
    try:
        response = gemini_client.models.embed_content(
            model='gemini-embedding-001',
            contents=query,
            config=types.EmbedContentConfig(output_dimensionality=768)
        )
        query_vector = response.embeddings[0].values
        
        qdrant_results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=top_k
        )
        results = [hit.payload for hit in qdrant_results]
        
        # Trigger fallback if vector results are weak or empty
        if not results or any(hit.score < 0.5 for hit in qdrant_results):
            return keyword_search(query, top_k)
            
        return results
        
    except Exception as e:
        print(f"\n[NETWORK FALLBACK] Semantic failure: {e}")
        return keyword_search(query, top_k=top_k)