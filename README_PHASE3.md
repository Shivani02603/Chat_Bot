# Phase 3: FastAPI Backend + Streamlit UI

Simple web interface for SmartSense with Excel ingestion and chatbot.

## Overview

Phase 3 adds:
1. **FastAPI Backend** - 2 endpoints (ingest, chat)
2. **Streamlit UI** - 2 pages (Excel upload, chat interface)

## Architecture

```
┌─────────────────────────┐
│  Streamlit UI           │ (Port 8501)
│  - Excel Upload         │
│  - Chat Interface       │
└───────────┬─────────────┘
            │ HTTP
            ↓
┌─────────────────────────┐
│  FastAPI Backend        │ (Port 8000)
│  - POST /api/ingest     │
│  - POST /api/chat       │
└───────────┬─────────────┘
            │
            ↓
┌─────────────────────────┐
│  Phase 1 + 2 Components │
│  - ETL Pipeline         │
│  - 8 Agents             │
│  - PostgreSQL + FAISS   │
└─────────────────────────┘
```

## Backend Endpoints (`scripts/api.py`)

### 1. Ingest Excel
```
POST /api/ingest
Content-Type: multipart/form-data

Request:
- file: Excel file (Property_list.xlsx format)

Response:
{
  "status": "success",
  "properties_ingested": 100,
  "message": "ETL pipeline completed successfully"
}
```

### 2. Chat
```
POST /api/chat
Content-Type: application/json

Request:
{
  "user_id": "user_123",
  "message": "Find 2BHK in Mumbai under 50 lakh"
}

Response:
{
  "response": "Found 5 properties...",
  "intent": "search_property",
  "sources": ["PROP-001", "PROP-002"]
}
```

## Streamlit UI (`ui/app.py`)

### Page 1: Home / Excel Ingestion
- File uploader for Excel files
- "Upload & Process" button
- Progress indicator during ETL
- Success/error messages
- Display: Number of properties ingested

### Page 2: Chat Interface
- Chat history display (scrollable)
- Text input for messages
- Send button
- Display intent classification
- Show sources when available
- Clear conversation button
- User ID input (sidebar)

## File Structure

```
SmartSense/
├── scripts/
│   ├── api.py                    # FastAPI backend (2 endpoints)
│   ├── etl.py                    # Existing Phase 1 ETL
│   ├── chat.py                   # Existing Phase 2 chatbot
│   └── agents/                   # Existing 8 agents
│
├── ui/
│   ├── app.py                    # Main Streamlit app with sidebar
│   ├── pages/
│   │   └── 1_Chat.py            # Chat interface page
│   └── utils.py                  # API call helpers
│
├── uploads/                      # Temporary upload storage
├── .env.example                  # Template for secrets
└── requirements.txt              # Updated with Phase 3 deps
```

## New Dependencies

Add to `requirements.txt`:
```txt
# Phase 3: Backend & Frontend
fastapi
uvicorn[standard]
streamlit
python-multipart
```

## Environment Configuration

`.env.example`:
```bash
# PostgreSQL Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=realestate
DB_USER=postgres
DB_PASSWORD=your_password_here

# HuggingFace API (for chatbot LLM)
HF_TOKEN=your_huggingface_token_here

# Redis (optional - will fallback to dict)
REDIS_HOST=localhost
REDIS_PORT=6379

# Tavily API (optional - for web research)
TAVILY_API_KEY=your_tavily_key_here

# Phase 3: API Configuration
API_HOST=localhost
API_PORT=8000
```

## Setup & Deployment

### 1. Database Setup
```bash
# Create database
createdb realestate

# Run migrations
psql -d realestate -f migrations/001_create_tables.sql
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Copy example env file
cp .env.example .env

# Edit .env with your credentials
# Required: DB_PASSWORD, HF_TOKEN
# Optional: TAVILY_API_KEY, REDIS_HOST
```

### 4. Run Backend
```bash
# Terminal 1: Start FastAPI backend
uvicorn scripts.api:app --reload --host 0.0.0.0 --port 8000
```

### 5. Run Frontend
```bash
# Terminal 2: Start Streamlit UI
streamlit run ui/app.py --server.port 8501
```

### 6. Access Application
- **Streamlit UI**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **API Redoc**: http://localhost:8000/redoc

## Usage Flow

### Flow 1: Ingest Properties
1. Open Streamlit UI → Home page
2. Select Excel file (`assets/Property_list.xlsx`)
3. Click "Upload & Process"
4. Wait for ETL completion (all 4 steps)
5. See confirmation with property count

### Flow 2: Chat with Bot
1. Open Streamlit UI → Chat page
2. Enter user ID in sidebar (or use default)
3. Type query: "Find 3BHK in Bangalore under 1 crore"
4. View chatbot response
5. See intent classification and sources
6. Continue conversation

## API Testing (cURL Examples)

### Test Ingest
```bash
curl -X POST "http://localhost:8000/api/ingest" \
  -F "file=@assets/Property_list.xlsx"
```

### Test Chat
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "message": "Find 2BHK properties under 50 lakh"
  }'
```

## Notes

- Simple implementation: 2 endpoints, 2 pages
- Reuse existing Phase 1 ETL and Phase 2 chatbot
- No authentication (simple user_id tracking)
- FastAPI provides automatic Swagger documentation
- Streamlit manages session state for chat history
