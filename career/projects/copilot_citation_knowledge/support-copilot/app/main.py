from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from app.generation.generator import generate_response_stream

app = FastAPI(title="Support Copilot Engine")

@app.get("/api/chat/stream")
def stream_chat(query: str = Query(..., description="The user query to support copilot")):
    """Streams the RAG-augmented generation answer block by block."""
    return StreamingResponse(
        generate_response_stream(query), 
        media_type="text/event-stream"
    )

@app.get("/api/health")
def health_check():
    return {"status": "healthy"}

@app.get("/")
def read_root():
    return {"message": "Welcome to the Support Copilot Engine API. Go to /api/health or /api/chat/stream"}