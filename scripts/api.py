"""
FastAPI Backend for SmartSense
Provides REST API for Excel ingestion and chatbot
"""

import os
import shutil
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Import existing components
import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

from etl import step1_read_excel, step2_save_to_postgres, step3_extract_pdf_text, step4_index_vectors
from chat import RealEstateChatbot

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="SmartSense API",
    description="Real Estate Search Engine with Multi-Agent Chatbot",
    version="3.0.0"
)

# CORS middleware for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', 5432),
    'database': os.getenv('DB_NAME', 'realestate'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD')
}

# Store chatbot instances per user
chatbots = {}


# Request/Response Models
class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
    intent: Optional[str] = None
    sources: Optional[list] = None


class IngestResponse(BaseModel):
    status: str
    properties_ingested: int
    message: str


# Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "SmartSense API - Phase 3",
        "version": "3.0.0",
        "endpoints": ["/api/ingest", "/api/chat", "/api/health"]
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected" if DB_CONFIG.get('password') else "not configured",
        "faiss_index": "available" if Path("data/faiss_index/properties.index").exists() else "not found"
    }


@app.post("/api/ingest", response_model=IngestResponse)
async def ingest_excel(file: UploadFile = File(...)):
    """
    Upload Excel file and trigger ETL pipeline

    Runs all 4 ETL steps:
    1. Read Excel
    2. Save to PostgreSQL
    3. Extract PDF text
    4. Create FAISS index
    """

    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be Excel format (.xlsx or .xls)")

    # Save uploaded file
    file_path = UPLOAD_DIR / file.filename
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Run ETL pipeline
    try:
        # Step 1: Read Excel
        df = step1_read_excel(str(file_path))

        # Step 2: Save to PostgreSQL
        count = step2_save_to_postgres(df, DB_CONFIG)

        # Step 3: Extract PDF text
        cert_dir = "assets/certificates"
        pdf_texts = step3_extract_pdf_text(cert_dir)

        # Step 4: Index vectors
        step4_index_vectors(df, pdf_texts, DB_CONFIG)

        # Clean up uploaded file
        file_path.unlink()

        return IngestResponse(
            status="success",
            properties_ingested=count,
            message=f"ETL pipeline completed successfully. {count} properties indexed."
        )

    except Exception as e:
        # Clean up on error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"ETL pipeline failed: {str(e)}")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the real estate bot

    Uses Phase 2 multi-agent chatbot with 8 agents:
    - Router, Planner, Structured, RAG, Web Research, Report Generator, Renovation, Memory
    """

    # Get or create chatbot for this user
    if request.user_id not in chatbots:
        try:
            chatbots[request.user_id] = RealEstateChatbot(user_id=request.user_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize chatbot: {str(e)}")

    chatbot = chatbots[request.user_id]

    # Process message
    try:
        response_text = chatbot.chat(request.message)

        # Try to extract intent from debug output (if available)
        # The chatbot prints [DEBUG] Intent: ... which we can't capture here
        # So we just return the response

        return ChatResponse(
            response=response_text,
            intent=None,  # Could be enhanced to capture this
            sources=None  # Could be enhanced to capture this
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")


@app.delete("/api/chat/{user_id}/history")
async def clear_history(user_id: str):
    """Clear conversation history for a user"""

    if user_id in chatbots:
        chatbots[user_id].memory.clear_conversation()
        return {"status": "success", "message": f"Conversation history cleared for {user_id}"}
    else:
        raise HTTPException(status_code=404, detail=f"No active session for user {user_id}")


@app.get("/api/chat/{user_id}/preferences")
async def get_preferences(user_id: str):
    """Get user preferences"""

    if user_id in chatbots:
        prefs = chatbots[user_id].memory.get_all_preferences()
        return {"preferences": prefs}
    else:
        # Create temporary chatbot to fetch preferences
        temp_chatbot = RealEstateChatbot(user_id=user_id)
        prefs = temp_chatbot.memory.get_all_preferences()
        return {"preferences": prefs}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
