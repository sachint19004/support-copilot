import os
from typing import List, Dict, Any, Generator
from dotenv import load_dotenv
from google import genai
from ollama import Client

# 1. Safely resolve paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
ENV_PATH = os.path.join(BACKEND_DIR, ".env")
load_dotenv(dotenv_path=ENV_PATH)

# Initialize Gemini
api_key_val = os.getenv("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=api_key_val)

# 2. LOCAL OLLAMA: Connects directly to localhost
ollama_client = Client(host='http://localhost:11434')

def build_prompt(query: str, context_chunks: List[Dict[str, Any]]) -> str:
    """Constructs structured prompt injection context blocks."""
    context_str = ""
    for i, chunk in enumerate(context_chunks):
        metadata = chunk.get("metadata", {})
        source = metadata.get("source_name", "Unknown Source")
        heading = metadata.get("section_heading", "General")
        context_str += f"\n--- Context Block {i+1} (Source: {source} > {heading}) ---\n"
        context_str += chunk.get("text", "") + "\n"

    system_instruction = (
        "You are an expert enterprise customer support copilot.\n"
        "Your task is to answer the user's query accurately using ONLY the provided context blocks.\n"
    )
    return f"{system_instruction}\nContext:\n{context_str}\n\nUser Query: {query}\n\nAnswer:"

def generate_response_stream(query: str, context: list = None) -> Generator[str, None, None]:
    """Streams response from Gemini, automatically falling back to local Phi-3."""
    context_str = "\n---\n".join(context) if context else "No relevant context found."
    
    # 3. Strict alignment template forced into execution context
    full_prompt = f"""You are a precise and helpful customer support engineer. 
Your goal is to answer the user's question using ONLY the provided Context. 

CRITICAL INSTRUCTIONS:
- If a policy has multiple tiers or timeframes (e.g., partial refunds, store credit), you MUST explain the exact outcome for the user's specific situation.
- Do not just say "no refund" if they are eligible for store credit. 
- If the answer is not in the context, reply exactly with 'I cannot find this in our policy.'

Context:
{context_str}

User Query: {query}
Answer:"""
    
    try:
        response = gemini_client.models.generate_content_stream(
            model='gemini-2.5-flash',
            contents=full_prompt
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text

    except Exception as e:
        error_msg = str(e)
        if "503" in error_msg or "429" in error_msg or "exhausted" in error_msg.lower():
            yield "\n\n*(Cloud API overloaded. Seamlessly routing to local Phi-3...)*\n\n"
            
            # 4. Fallback execution boundary over native port
            local_stream = ollama_client.chat(
                model='phi3',
                messages=[{'role': 'user', 'content': full_prompt}],
                stream=True,
                options={'temperature': 0.1}
            )
            
            for chunk in local_stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    yield chunk['message']['content']
        else:
            yield f"\n\n❌ System Error: {error_msg}"