# Phase 2: Multi-Agent Chatbot Architecture

Real estate chatbot with 8 specialized agents and 3 types of memory.

## Agents

1. **Query Router** - Intent classification using Llama 3.2-3B LLM
2. **Planner** - Task decomposition for complex queries
3. **Structured Agent** - SQL queries for property search
4. **RAG Agent** - Vector search + LLM for semantic answers
5. **Web Research Agent** - Live market data (Tavily API)
6. **Report Generator** - PDF reports with matplotlib charts
7. **Renovation Estimator** - Cost calculations
8. **Memory** - Episodic, Short-term (Redis), Long-term (PostgreSQL)

## Quick Start

### 1. Install New Dependencies

```bash
pip install -r requirements.txt
```

New packages: `matplotlib`, `reportlab`, `redis`, `scipy`

### 2. Setup HuggingFace Token

1. Sign up at https://huggingface.co/
2. Get token from https://huggingface.co/settings/tokens
3. Create token with "Read" permission
4. Add to `.env`:

```bash
HF_TOKEN=hf_your_token_here
```

### 3. Optional: Setup Redis

For short-term memory (optional - will fallback to dict):

```bash
# Using Docker
docker run -d -p 6379:6379 --name redis redis

# Or install locally
# Windows: Download from https://github.com/microsoftarchive/redis/releases
# Mac: brew install redis
# Linux: sudo apt install redis-server
```

### 4. Optional: Setup Tavily

For web research (optional):

1. Sign up at https://tavily.com/
2. Get API key
3. Add to `.env`:

```bash
TAVILY_API_KEY=your_tavily_key
```

### 5. Run Chatbot

```bash
python scripts/chat.py
```

## Example Queries

```
You: Find 2BHK in Mumbai under 50 lakh
Bot: Found 3 properties: ...

You: Estimate renovation cost for 1200 sqft
Bot: Basic: Rs.6,00,000, Moderate: Rs.14,40,000, Premium: Rs.30,00,000

You: Generate a comparison report
Bot: Report generated successfully! Saved to: reports/property_report_20241108_123456.pdf

You: Save my budget as 1 crore
Bot: Preferences saved!

You: What are current market rates in Bangalore?
Bot: [Web research results...]
```

## Memory Types

### 1. Episodic Memory
- In-session conversation history
- Stored in memory (cleared on exit)
- Command: `history` to view

### 2. Short-term Memory
- Session context (Redis cache)
- Auto-expires after 1 hour
- Stores: last search results, current filters

### 3. Long-term Memory
- User preferences (PostgreSQL)
- Persistent across sessions
- Stores: budget, location preferences
- Command: `prefs` to view

## Architecture

```
User Input
    ↓
Query Router (LLM)
    ↓
├─→ search_property → Structured Agent (SQL)
├─→ estimate_renovation → Renovation Estimator
├─→ generate_report → Report Generator (PDF)
├─→ save_preference → Memory (PostgreSQL)
├─→ web_research → Web Research (Tavily)
└─→ general_query → RAG Agent (FAISS + LLM)
```

## Project Structure

```
scripts/
├── chat.py                      # Main chatbot interface
└── agents/
    ├── router.py                # Intent classification
    ├── planner.py               # Task decomposition
    ├── structured_agent.py      # SQL search
    ├── rag_agent.py             # Vector search + LLM
    ├── web_research.py          # Tavily integration
    ├── report_generator.py      # PDF generation
    ├── renovation.py            # Cost estimator
    └── memory.py                # 3 memory types

reports/                         # Generated PDF reports
```

## Testing Individual Agents

Each agent can be tested standalone:

```bash
# Test router
python scripts/agents/router.py

# Test RAG agent
python scripts/agents/rag_agent.py

# Test report generator
python scripts/agents/report_generator.py
```

## Notes

- All agents use **Llama 3.2-3B** via HuggingFace Inference API
- Redis is optional (fallback to dict)
- Tavily is optional (fallback message if not available)
- Reports saved to `reports/` directory (auto-created)

## Next Steps

Proceed to **Phase 3** for UI (Streamlit) and API (FastAPI) implementation.
