# SmartSense

Minimal real estate AI assistant. Upload the Excel, ask natural language questions, get property results, renovation estimates, and PDF comparison reports.

## Quick Setup

Prerequisites: Python 3.8+, PostgreSQL running, HuggingFace token.

Clone the repository, then run:

```bash
cd SmartSense
pip install -r requirements.txt
psql -U postgres -d realestate -f migrations/001_create_tables.sql
```
Note: Make sure to use the Password that you used to login into PostgresSQL.

Copy the `.env` variables from `.env.example` file and enter your tokens/passwords there.


## Run

Two terminals:
```bash
# Backend
python -m uvicorn scripts.api:app --reload --port 8000

# Frontend
streamlit run ui/app.py --server.port 8501
```

Open: http://localhost:8501

First time: Use the upload box to submit `assets/Property_list.xlsx` (this triggers ETL automatically).

## Example Queries
```
1. Give me a list of properties in Bangalore
2. Estimate renovation for 1200 sqft
3. Give me a list of properties with 2 rooms and generate a report
4. What is the current price of properties in Hyderabad.
```

## Troubleshooting (quick)
```bash
# DB connection check
psql -U postgres -d realestate

# HuggingFace auth issue
# Verify HF_TOKEN in .env then restart backend