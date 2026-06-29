import os
from typing import List, Dict, Any, Generator
from dotenv import load_dotenv
from google import genai
from app.retrieval.search import hybrid_search

load_dotenv()

# Initialize Gemini Client
gemini_client = genai.Client()

def build_prompt(query: str, context_chunks: List[Dict[str, Any]]) -> str:
    """Constructs the structured prompt injecting retrieved documentation context."""
    context_str = ""
    for i, chunk in enumerate(context_chunks):
        source = chunk["metadata"].get("source_name", "Unknown Source")
        heading = chunk["metadata"].get("section_heading", "General")
        context_str += f"\n--- Context Block {i+1} (Source: {source} > {heading}) ---\n"
        context_str += chunk["text"] + "\n"

    system_instruction = (
        "You are an expert enterprise customer support copilot.\n"
        "Your task is to answer the user's query accurately using ONLY the provided context blocks below.\n"
        "Guidelines:\n"
        "1. Prioritize information from the most relevant blocks.\n"
        "2. If the context contains sufficient information, answer clearly and concisely.\n"
        "3. If the context does not contain the answer, state that you cannot find the information in the documentation.\n"
        "4. Always maintain a professional, helpful support tone.\n"
    )

    full_prompt = f"{system_instruction}\nContext:\n{context_str}\n\nUser Query: {query}\n\nAnswer:"
    return full_prompt

def generate_response_stream(query: str) -> Generator[str, None, None]:
    """Retrieves documentation context and streams the LLM-generated answer."""
    # 1. Fetch top 3 relevant chunks via Phase 3 Hybrid Search
    relevant_chunks = hybrid_search(query, top_k=3)
    
    # 2. Build out the context-infused prompt
    prompt = build_prompt(query, relevant_chunks)
    
    # 3. Stream response from gemini-2.5-flash
    response_stream = gemini_client.models.generate_content_stream(
        model='gemini-2.5-flash',
        contents=prompt
    )
    
    for chunk in response_stream:
        if chunk.text:
            yield chunk.text