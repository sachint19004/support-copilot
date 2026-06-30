import os
import json
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from google import genai
from google.genai import types

# 1. Setup local paths
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BACKEND_DIR, ".env")
load_dotenv(dotenv_path=ENV_PATH)

api_key_val = os.getenv("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=api_key_val)

# 2. Local database and cache tracking path metrics
LOCAL_DB_PATH = os.path.join(BACKEND_DIR, "qdrant_local_data")
qdrant_client = QdrantClient(path=LOCAL_DB_PATH)
COLLECTION_NAME = "support_docs"

BM25_CACHE_PATH = os.path.join(BACKEND_DIR, "data", "chunks.json")

def create_collection():
    """Initializes or resets the local Qdrant collection."""
    # Robustly check if collection exists across all Qdrant versions
    existing_collections = [c.name for c in qdrant_client.get_collections().collections]
    
    if COLLECTION_NAME in existing_collections:
        qdrant_client.delete_collection(collection_name=COLLECTION_NAME)
        
    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=768,  # Match gemini-embedding-001 output dimension
            distance=Distance.COSINE
        )
    )
    print(f"[SUCCESS] Local vector collection '{COLLECTION_NAME}' ready.")

def run_ingestion(documents: list):
    """Processes chunks into local vectors and JSON backups."""
    print(f"Starting ingestion for {len(documents)} document chunks...")
    create_collection()
    
    points = []
    for idx, doc in enumerate(documents):
        text_content = doc.get("text", "")
        metadata = doc.get("metadata", {})
        
        response = gemini_client.models.embed_content(
            model='gemini-embedding-001',
            contents=text_content,
            config=types.EmbedContentConfig(output_dimensionality=768)
        )
        vector = response.embeddings[0].values
        
        points.append(
            PointStruct(
                id=idx,
                vector=vector,
                payload={"text": text_content, "metadata": metadata}
            )
        )
    
    qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"[SUCCESS] Loaded vectors into: {LOCAL_DB_PATH}")
    
    # Save the fallback cache file natively
    os.makedirs(os.path.dirname(BM25_CACHE_PATH), exist_ok=True)
    with open(BM25_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=4, ensure_ascii=False)
    print(f"[SUCCESS] Local backup cache tracking file saved at: {BM25_CACHE_PATH}")

if __name__ == "__main__":
    mock_chunks = [
        {
            "text": "Corporate Refund Policy: Returns made within 14 days receive a full refund. Returns made between 15 and 30 days are not eligible for a refund but will receive standard store credit.",
            "metadata": {"source_name": "refund_policy.md", "section_heading": "Eligibility Window"}
        },
        {
            "text": "API Authentication FAQ: All endpoints require an Authorization header containing a Bearer JWT token issued from the oauth/token routing node.",
            "metadata": {"source_name": "api_faq.md", "section_heading": "Security"}
        }
    ]
    run_ingestion(mock_chunks)