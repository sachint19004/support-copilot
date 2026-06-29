import os
import json
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from google import genai
from app.ingestion.parser import load_and_chunk_docs
from google.genai import types

load_dotenv()

# Initialize Gemini and Local Qdrant Storage
gemini_client = genai.Client()
qdrant_client = QdrantClient(path="qdrant_data") 
COLLECTION_NAME = "support_docs"

def setup_qdrant():
    """Initializes a local Qdrant collection configured for Gemini 768-dim vectors."""
    # Get a list of all existing collections
    existing_collections = [c.name for c in qdrant_client.get_collections().collections]
    
    # Create the collection if it doesn't exist
    if COLLECTION_NAME not in existing_collections:
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )
def main():
    print("[1/3] Parsing markdown documentation...")
    chunks = load_and_chunk_docs("docs")
    if not chunks:
        print("Error: No markdown files found in 'docs/' directory.")
        return
        
    print(f"Found {len(chunks)} text chunks.")
    setup_qdrant()
    
    points = []
    saved_chunks = [] 

    print("[2/3] Generating embeddings via Gemini text-embedding-001...")
    for i, chunk in enumerate(chunks):
        response = gemini_client.models.embed_content(
            model='gemini-embedding-001',
            contents=chunk.text,
            config=types.EmbedContentConfig(output_dimensionality=768)
        )
        vector = response.embeddings[0].values
        
        payload = chunk.metadata.model_dump()
        payload["text"] = chunk.text
        payload["chunk_id"] = i
        
        points.append(PointStruct(id=i, vector=vector, payload=payload))
        saved_chunks.append(payload)

    print("[3/3] Committing payloads to Vector and Local storage...")
    qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)
    
    os.makedirs("data", exist_ok=True)
    with open("data/chunks.json", "w") as f:
        json.dump(saved_chunks, f, indent=2)
        
    print("Ingestion pipeline successfully completed.")

if __name__ == "__main__":
    main()