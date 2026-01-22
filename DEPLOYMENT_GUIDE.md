# SmartSense - Deployment Guide

Quick guide to deploy and run SmartSense Phase 3 (FastAPI + Streamlit).

## Prerequisites

- Python 3.8+
- PostgreSQL installed and running
- Required: HuggingFace API token
- Optional: Redis, Tavily API key

## Setup Steps

### 1. Install Dependencies

```bash
cd SmartSense
python -m pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Create database
createdb realestate

# Run migrations
psql -d realestate -f migrations/001_create_tables.sql
```

### 3. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your credentials:
# - DB_PASSWORD (required)
# - HF_TOKEN (required - get from https://huggingface.co/settings/tokens)
# - TAVILY_API_KEY (optional)
```

### 4. Run ETL Pipeline (First Time Only)

```bash
# Ingest property data
python scripts/etl.py
```

This will:
- Read `assets/Property_list.xlsx`
- Save to PostgreSQL database
- Extract PDF certificate text
- Create FAISS vector index

## Running the Application

You need **two terminal windows** running simultaneously:

### Terminal 1: Start FastAPI Backend

```bash
# From SmartSense directory
python -m uvicorn scripts.api:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Application startup complete.
```

### Terminal 2: Start Streamlit Frontend

```bash
# From SmartSense directory
streamlit run ui/app.py --server.port 8501
```

You should see:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

## Accessing the Application

- **Streamlit UI**: http://localhost:8501
- **FastAPI Swagger Docs**: http://localhost:8000/docs
- **FastAPI ReDoc**: http://localhost:8000/redoc
- **API Health Check**: http://localhost:8000/api/health

## Usage

### 1. Upload Properties (Optional - Skip if already done)

- Open http://localhost:8501
- Go to Home page
- Upload `assets/Property_list.xlsx`
- Click "Upload & Process"
- Wait for ETL completion

### 2. Chat with Bot

- Navigate to "Chat" page in sidebar
- Enter your user ID (or use default)
- Type queries like:
  - "Find 2BHK properties in Mumbai"
  - "Show me properties under 50 lakh"
  - "Estimate renovation cost for 1200 sqft"
  - "Save my budget as 1 crore"
  - "Generate a comparison report"

## API Testing

Test the backend directly with curl:

```bash
# Health check
curl http://localhost:8000/api/health

# Chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "Find 3BHK properties"}'

# Ingest (upload Excel)
curl -X POST http://localhost:8000/api/ingest \
  -F "file=@assets/Property_list.xlsx"
```

## Troubleshooting

### Backend Won't Start

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Fix:** Install dependencies
```bash
python -m pip install fastapi uvicorn streamlit python-multipart
```

### Database Connection Error

**Error:** `psycopg2.OperationalError: FATAL: password authentication failed`

**Fix:** Check `.env` file has correct `DB_PASSWORD`

### FAISS Index Not Found

**Error:** `RuntimeError: could not open data/faiss_index/properties.index`

**Fix:** Run ETL pipeline first
```bash
python scripts/etl.py
```

### HuggingFace 401 Unauthorized

**Error:** `401 Client Error: Unauthorized`

**Fix:**
1. Get token from https://huggingface.co/settings/tokens
2. Add to `.env`: `HF_TOKEN=your_token_here`
3. Restart backend

### Port Already in Use

**Error:** `OSError: [Errno 48] Address already in use`

**Fix:**
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn scripts.api:app --port 8001
```

## Stopping the Application

1. In **Terminal 1** (FastAPI): Press `Ctrl+C`
2. In **Terminal 2** (Streamlit): Press `Ctrl+C`

## Directory Structure After Setup

```
SmartSense/
├── data/
│   └── faiss_index/          # Created by ETL
│       ├── properties.index
│       └── id_map.txt
├── reports/                  # Created by report generator
│   └── property_report_*.pdf
├── uploads/                  # Temporary uploads (auto-created)
└── .env                      # Your configuration (not in git)
```

## Support

For issues or questions, refer to:
- README_PHASE3.md - Phase 3 architecture
- CLAUDE.md - Complete project documentation
- API Docs: http://localhost:8000/docs
