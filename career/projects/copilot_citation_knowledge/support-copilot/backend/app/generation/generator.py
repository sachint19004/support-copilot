import os
from ollama import chat
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

def generate_response_stream(query: str, context: list = None):
    """
    Streams response from Gemini, automatically falling back to 
    local Phi-3 if Google's servers hit rate limits or go down.
    """
    # 1. Build your standard prompt string
    context_str = "\n".join(context) if context else ""
    full_prompt = f"Context:\n{context_str}\n\nUser Query: {query}"
    
    try:
        # 2. PRIMARY PIPELINE: Attempt Google Gemini Stream
        # (Make sure this matches your exact Gemini model setup)
        response = gemini_client.models.generate_content_stream(
            model='gemini-2.5-flash',
            contents=full_prompt
        )
        
        for chunk in response:
            if chunk.text:
                yield chunk.text

    except Exception as e:
        error_msg = str(e)
        
        # 3. FALLBACK TRIGGER: Catch rate limits (429) or overloads (503)
        if "503" in error_msg or "429" in error_msg or "exhausted" in error_msg.lower():
            
            # Optional: Send a UI signal so the user knows what happened
            yield "\n\n*(Cloud API overloaded. Seamlessly routing to local Phi-3...)*\n\n"
            
            # 4. SECONDARY PIPELINE: Stream from local Ollama
            local_stream = chat(
                model='phi3',
                messages=[{'role': 'user', 'content': full_prompt}],
                stream=True,
                options={'temperature': 0.3}
            )
            
            for chunk in local_stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    yield chunk['message']['content']
        else:
            # If it is a completely different error (like missing API keys), fail gracefully
            yield f"\n\n❌ System Error: {error_msg}"