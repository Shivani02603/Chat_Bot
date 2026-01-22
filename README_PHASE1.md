# Phase 1: Data Ingestion & Vector Indexing

Simple ETL pipeline that does 4 things:
1. **Read** Excel file
2. **Save** canonical data to PostgreSQL
3. **Extract** text from PDF certificates
4. **Index** everything to vector database with embeddings

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Database

```bash
# Create PostgreSQL database
createdb realestate

# Run schema
psql -d realestate -f migrations/001_create_tables.sql
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set your database password:
```
DB_PASSWORD=your_password_here
```

### 4. Run ETL Pipeline

```bash
python scripts/etl.py
```

That's it! The script will:
- Load property data from `assets/Property_list.xlsx`
- Save all rows to PostgreSQL `properties` table
- Extract text from PDFs in `assets/certificates/`
- Generate embeddings and index to vector DB (Qdrant or FAISS)

## What Gets Created?

**Database Table:**
```sql
properties (
    property_id,
    num_rooms,
    property_size_sqft,
    title_short_description,
    long_description,
    location,
    price,
    seller_type,
    listing_date,
    certificates,
    seller_contact,
    metadata_tags
)
```

**Vector Index:**
- Uses Qdrant if available (run: `docker run -p 6333:6333 qdrant/qdrant`)
- Falls back to FAISS automatically (saves to `data/faiss_index/`)

## Verify Results

```bash
# Check how many properties were loaded
psql -d realestate -c "SELECT COUNT(*) FROM properties;"

# View first 5 properties
psql -d realestate -c "SELECT property_id, location, price FROM properties LIMIT 5;"
```

## Code Structure

```
scripts/etl.py
├── step1_read_excel()       # Read Excel file
├── step2_save_to_postgres() # Save to database
├── step3_extract_pdf_text() # Extract PDF content
└── step4_index_vectors()    # Create embeddings & index
```

All steps run sequentially in `main()`. Check the code - it's simple and readable!

## Project Structure

```
SmartSense/
├── assets/
│   ├── Property_list.xlsx
│   └── certificates/*.pdf
├── migrations/
│   └── 001_create_tables.sql
├── scripts/
│   └── etl.py
├── requirements.txt
├── .env.example
└── README_PHASE1.md

Note: data/ folder will be auto-created by ETL script when using FAISS
```
