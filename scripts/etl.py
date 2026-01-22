"""
Simple ETL Pipeline for Real Estate Data
Steps:
1. Read Excel file
2. Save canonical data to PostgreSQL
3. Extract text from PDF certificates
4. Index everything to vector database with embeddings
"""

import os
import pandas as pd
import psycopg2
from sentence_transformers import SentenceTransformer
from pathlib import Path
from dotenv import load_dotenv

# PDF text extraction
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

# Vector database - using FAISS (simple, no server needed)
import faiss
import numpy as np
VECTOR_DB = 'faiss'


def step1_read_excel(file_path):
    """Step 1: Read Excel file"""
    print(f"\n=== STEP 1: Reading Excel file ===")
    df = pd.read_excel(file_path)

    # Rename the column with special characters
    if 'title / short_description' in df.columns:
        df.rename(columns={'title / short_description': 'title_short_description'}, inplace=True)

    print(f"Loaded {len(df)} properties")
    print(f"Columns: {df.columns.tolist()}")
    return df


def step2_save_to_postgres(df, db_config):
    """Step 2: Save canonical data to PostgreSQL"""
    print(f"\n=== STEP 2: Saving to PostgreSQL ===")

    # Connect to database
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    # Insert each row
    count = 0
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO properties (
                property_id, num_rooms, property_size_sqft,
                title_short_description, long_description, location,
                price, seller_type, listing_date,
                certificates, seller_contact, metadata_tags
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (property_id) DO UPDATE SET
                num_rooms = EXCLUDED.num_rooms,
                price = EXCLUDED.price,
                location = EXCLUDED.location
        """, (
            row['property_id'],
            int(row.get('num_rooms', 0)),
            int(row.get('property_size_sqft', 0)),
            str(row.get('title_short_description', '')),
            str(row.get('long_description', '')),
            str(row.get('location', '')),
            int(row.get('price', 0)),
            str(row.get('seller_type', '')),
            pd.to_datetime(row.get('listing_date'), errors='coerce'),
            str(row.get('certificates', '')),
            str(row.get('seller_contact', '')),
            str(row.get('metadata_tags', ''))
        ))
        count += 1

    conn.commit()
    cursor.close()
    conn.close()

    print(f"Saved {count} properties to database")
    return count


def step3_extract_pdf_text(cert_dir):
    """Step 3: Extract text from PDF certificates"""
    print(f"\n=== STEP 3: Extracting PDF text ===")

    if not pdfplumber:
        print("WARNING: pdfplumber not installed, skipping PDF extraction")
        return {}

    cert_path = Path(cert_dir)
    pdf_texts = {}

    if not cert_path.exists():
        print(f"WARNING: Certificate directory {cert_dir} not found")
        return {}

    for pdf_file in cert_path.glob('*.pdf'):
        try:
            with pdfplumber.open(pdf_file) as pdf:
                text = '\n'.join([page.extract_text() or '' for page in pdf.pages])
                pdf_texts[pdf_file.name] = text
                print(f"Extracted {len(text)} chars from {pdf_file.name}")
        except Exception as e:
            print(f"ERROR: Failed to extract {pdf_file.name}: {e}")

    print(f"Extracted text from {len(pdf_texts)} PDFs")
    return pdf_texts


def step4_index_vectors(df, pdf_texts, vector_config):
    """Step 4: Create embeddings and index to vector database"""
    print(f"\n=== STEP 4: Indexing to vector database (FAISS) ===")

    # Load embedding model
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("Loaded embedding model")

    # Create FAISS index
    dimension = 384
    index = faiss.IndexFlatIP(dimension)

    vectors = []
    id_map = []

    for idx, row in df.iterrows():
        # Combine all text for this property
        text_parts = [
            row.get('title_short_description', ''),
            row.get('long_description', ''),
            row.get('location', ''),
            row.get('metadata_tags', '')
        ]

        # Add certificate text if available
        certs = str(row.get('certificates', '')).split('|')
        for cert in certs:
            cert = cert.strip()
            if cert in pdf_texts:
                text_parts.append(pdf_texts[cert])

        combined_text = ' '.join(text_parts)
        embedding = model.encode(combined_text)

        vectors.append(embedding)
        id_map.append(row['property_id'])

    # Add to FAISS
    vectors = np.array(vectors, dtype='float32')
    faiss.normalize_L2(vectors)
    index.add(vectors)

    # Save to disk
    Path('data/faiss_index').mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, 'data/faiss_index/properties.index')
    with open('data/faiss_index/id_map.txt', 'w') as f:
        f.write('\n'.join(id_map))

    print(f"Indexed {len(vectors)} properties to FAISS")
    print(f"Saved index to data/faiss_index/")


def main():
    """Main ETL pipeline"""
    print("=" * 50)
    print("Real Estate ETL Pipeline")
    print("=" * 50)

    # Load configuration
    load_dotenv()

    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'realestate'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '')
    }

    vector_config = {
        'host': os.getenv('QDRANT_HOST', 'localhost'),
        'port': int(os.getenv('QDRANT_PORT', 6333))
    }

    # Run pipeline
    df = step1_read_excel('assets/Property_list.xlsx')
    step2_save_to_postgres(df, db_config)
    pdf_texts = step3_extract_pdf_text('assets/certificates')
    step4_index_vectors(df, pdf_texts, vector_config)

    print("\n" + "=" * 50)
    print("ETL Pipeline Complete!")
    print("=" * 50)


if __name__ == '__main__':
    main()
