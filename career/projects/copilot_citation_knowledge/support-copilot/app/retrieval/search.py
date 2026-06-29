import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from google import genai
from google.genai import types
from rank_bm25 import BM25Okapi

load_dotenv()

# Initialize Clients
gemini_client = genai.Client()
qdrant_client = QdrantClient(path="qdrant_data")
COLLECTION_NAME = "support_docs"

# Load local chunks for BM25
CHUNKS_PATH = "data/chunks.json"
if not os.path.exists(CHUNKS_PATH):
    raise FileNotFoundError(f"Missing {CHUNKS_PATH}. Please run ingestion first.")

with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
    corpus_chunks = json.load(f)

# Initialize BM25 Sparse Indexer
tokenized_corpus = [chunk["text"].lower().split(" ") for chunk in corpus_chunks]
bm25 = BM25Okapi(tokenized_corpus)

def get_embedding(text: str) -> List[float]:
    """Generates a 768-dimensional embedding from Gemini."""
    response = gemini_client.models.embed_content(
        model='gemini-embedding-001',
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=768)
    )
    return response.embeddings[0].values

def dense_search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Retrieves chunks based on semantic vector similarity."""
    query_vector = get_embedding(query)
    results = qdrant_client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=top_k
    )
    return [
        {
            "chunk_id": hit.payload["chunk_id"],
            "text": hit.payload["text"],
            "metadata": hit.payload,
            "score": hit.score
        }
        for hit in results
    ]

def sparse_search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Retrieves chunks based on exact keyword matching."""
    tokenized_query = query.lower().split(" ")
    scores = bm25.get_scores(tokenized_query)
    
    # Pair chunks with scores and sort
    scored_chunks = list(enumerate(scores))
    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    
    top_results = scored_chunks[:top_k]
    return [
        {
            "chunk_id": idx,
            "text": corpus_chunks[idx]["text"],
            "metadata": corpus_chunks[idx],
            "score": score
        }
        for idx, score in top_results if score > 0
    ]

def reciprocal_rank_fusion(dense_res: List[Dict], sparse_res: List[Dict], k: int = 60) -> List[Dict]:
    """Merges dense and sparse search rankings using Reciprocal Rank Fusion."""
    rrf_scores = {}
    chunk_mapping = {}

    # Process Dense Rankings
    for rank, hit in enumerate(dense_res):
        cid = hit["chunk_id"]
        chunk_mapping[cid] = hit
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k + (rank + 1)))

    # Process Sparse Rankings
    for rank, hit in enumerate(sparse_res):
        cid = hit["chunk_id"]
        chunk_mapping[cid] = hit
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k + (rank + 1)))

    # Sort candidates by combined RRF score
    sorted_chunks = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    
    return [
        {**chunk_mapping[cid], "rrf_score": score}
        for cid, score in sorted_chunks
    ]

def hybrid_search(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Executes both search modes and blends them using RRF."""
    # Fetch extra candidates to allow intersection sorting
    d_results = dense_search(query, top_k=top_k * 2)
    s_results = sparse_search(query, top_k=top_k * 2)
    
    merged = reciprocal_rank_fusion(d_results, s_results)
    return merged[:top_k]