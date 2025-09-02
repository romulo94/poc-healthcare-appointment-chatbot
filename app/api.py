"""
FastAPI server for Healthcare Appointment Chatbot
================================================

Simple FastAPI wrapper around the LangGraph healthcare chatbot.
Provides /chat endpoint and serves the frontend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import uuid

from graph.builder import create_healthcare_chatbot
from langchain_core.messages import HumanMessage

# =============================================================================
# SCHEMAS
# =============================================================================


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""

    message: str
    thread_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""

    message: str
    thread_id: str
    authenticated: bool


# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(
    title="Healthcare Appointment API",
    description="API for healthcare appointment management chatbot",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create the chatbot graph once at startup
chatbot = create_healthcare_chatbot()

# =============================================================================
# ENDPOINTS
# =============================================================================


@app.get("/")
async def root():
    """Serve the frontend HTML"""
    return FileResponse("index.html")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint that processes messages through the LangGraph chatbot
    """
    # Generate thread_id if not provided
    thread_id = request.thread_id or str(uuid.uuid4())

    # Configure for the graph
    config = {"configurable": {"thread_id": thread_id}}

    # Invoke the LangGraph chatbot
    response = chatbot.invoke(
        {"messages": [HumanMessage(content=request.message)]}, config
    )

    # Extract the bot's response
    bot_message = response["messages"][-1].content
    authenticated = response.get("user_verified", False)

    return ChatResponse(
        message=bot_message, thread_id=thread_id, authenticated=authenticated
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
