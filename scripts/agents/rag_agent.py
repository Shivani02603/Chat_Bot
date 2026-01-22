"""
RAG Agent - Retrieval Augmented Generation
Semantic search + LLM for answering questions about properties
"""

import os
import faiss
import numpy as np
import requests
import psycopg2
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv


class RAGAgent:
    """Retrieves relevant properties and generates answers with LLM"""

    def __init__(self):
        load_dotenv()

        # Load embedding model (same as Phase 1)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

        # Determine project root (go up from scripts/agents/ to root)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.join(current_dir, '..', '..')
        faiss_dir = os.path.join(project_root, 'data', 'faiss_index')

        # Load FAISS index
        index_path = os.path.join(faiss_dir, 'properties.index')
        self.index = faiss.read_index(index_path)

        # Load ID mapping
        id_map_path = os.path.join(faiss_dir, 'id_map.txt')
        with open(id_map_path, 'r') as f:
            self.id_map = [line.strip() for line in f]

        # Database config
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', 5432),
            'database': os.getenv('DB_NAME', 'realestate'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD')
        }

        # LLM config
        self.hf_token = os.getenv('HF_TOKEN')
        self.model = "meta-llama/Llama-3.2-3B-Instruct:novita"
        self.api_url = "https://router.huggingface.co/v1/chat/completions"

    def answer(self, question: str, top_k: int = 3, certificate_keywords: str = None) -> dict:
        """
        Answer a question using RAG

        Args:
            question: User's question
            top_k: Number of properties to retrieve
            certificate_keywords: Optional - specific certificate type to emphasize
                                 (e.g., "green building", "fire safety", or generic "certificate")

        Returns: {
            "answer": str,
            "sources": [property_ids]
        }
        """

        # Step 1: Enhance query if certificate keywords provided
        search_query = question
        if certificate_keywords:
            # If user asked about certificates, emphasize it in search
            if certificate_keywords.lower() in ['certificate', 'certification', 'certified']:
                # Generic certificate query - search for any certificate content
                search_query = f"{question} certificate certification safety building"
            else:
                # Specific certificate type - emphasize it
                search_query = f"{question} {certificate_keywords}"

            print(f"[RAG] Certificate search - Keywords: '{certificate_keywords}'")
            print(f"[RAG] Enhanced query: '{search_query}'")

        # Step 2: Retrieve relevant properties
        properties = self._retrieve(search_query, top_k)

        # Step 3: Generate answer with LLM
        answer = self._generate(question, properties, certificate_keywords)

        # Step 4: Extract citations
        sources = [p['property_id'] for p in properties]

        return {
            "answer": answer,
            "sources": sources
        }

    def _retrieve(self, query: str, top_k: int) -> list:
        """Search FAISS for relevant properties"""

        # Create query embedding
        query_embedding = self.embedding_model.encode(query)
        query_vector = np.array([query_embedding], dtype='float32')
        faiss.normalize_L2(query_vector)

        # Search FAISS
        distances, indices = self.index.search(query_vector, top_k)

        # Get property IDs
        property_ids = [self.id_map[idx] for idx in indices[0]]

        # Fetch full property details from DB
        properties = self._fetch_properties(property_ids)

        return properties

    def _fetch_properties(self, property_ids: list) -> list:
        """Get property details from database"""

        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()

        placeholders = ','.join(['%s'] * len(property_ids))
        query = f"SELECT * FROM properties WHERE property_id IN ({placeholders})"

        cursor.execute(query, property_ids)
        columns = [desc[0] for desc in cursor.description]
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        # Convert to dicts
        properties = []
        for row in results:
            properties.append(dict(zip(columns, row)))

        return properties

    def _generate(self, question: str, properties: list, certificate_keywords: str = None) -> str:
        """Generate answer using LLM with context"""

        # Build context from properties
        context = self._build_context(properties)

        # Create prompt with certificate-specific instructions if needed
        certificate_instruction = ""
        if certificate_keywords:
            certificate_instruction = f"""
CERTIFICATE QUERY DETECTED:
- The user is asking about: {certificate_keywords}
- Each property listing below includes certificates (if any)
- Mention which certificates each property has
- If no certificates match, say so clearly
"""

        prompt = f"""You are a helpful real estate assistant. Answer the question based ONLY on the provided
        property information below. Use the EXACT data provided - do not estimate, assume, or infer information.
{certificate_instruction}
Property Data:
{context}

Question: {question}

IMPORTANT:
- Use the exact number of rooms shown in the data
- Do not make assumptions or estimates about information that is already provided
- If information is missing, say so directly
- Include property IDs in your response
- If certificates are shown, mention them in your answer

Answer:"""

        # Call LLM
        response = self._call_llm(prompt)

        return response

    def _build_context(self, properties: list) -> str:
        """Build context string from properties"""

        context_parts = []
        for prop in properties:
            # Build basic property info
            prop_info = (
                f"Property {prop['property_id']}: "
                f"{prop.get('title_short_description', 'N/A')} in {prop.get('location', 'N/A')}. "
                f"Price: Rs.{prop.get('price', 0):,}. "
                f"Rooms: {prop.get('num_rooms', 'N/A')}. "
                f"Size: {prop.get('property_size_sqft', 'N/A')} sqft."
            )

            # Add certificate information if available
            certificates = prop.get('certificates', '')
            if certificates and str(certificates).lower() != 'nan':
                cert_list = [c.strip() for c in str(certificates).split('|')]
                cert_names = [c.replace('.pdf', '').replace('-', ' ').title() for c in cert_list]
                prop_info += f" Certificates: {', '.join(cert_names)}."

            context_parts.append(prop_info)

        return '\n'.join(context_parts)

    def _call_llm(self, prompt: str) -> str:
        """Call HuggingFace API using chat completions endpoint"""
        headers = {
            "Authorization": f"Bearer {self.hf_token}",
        }

        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "model": self.model,
            "max_tokens": 300,
            "temperature": 0.7
        }

        response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]
