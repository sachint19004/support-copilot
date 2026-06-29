from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from app.generation.generator import generate_response_stream

app = FastAPI(title="Support Copilot Engine")

# Enable CORS for React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite local development port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/chat/stream")
def stream_chat(query: str = Query(..., description="The user query to support copilot")):
    return StreamingResponse(
        generate_response_stream(query), 
        media_type="text/event-stream"
    )

@app.get("/api/health")
def health_check():
    return {"status": "healthy"}