"""
Structured Agent - SQL Query Executor
Searches properties using PostgreSQL with filters
"""

import os
import psycopg2
from dotenv import load_dotenv


class StructuredAgent:
    """Executes SQL queries to search properties"""

    def __init__(self):
        load_dotenv()
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', 5432),
            'database': os.getenv('DB_NAME', 'realestate'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD')
        }

    def search_properties(self, filters: dict) -> list:
        """
        Search properties with filters

        Args:
            filters: dict with optional keys:
                - location: str
                - num_rooms: int
                - max_price: int
                - min_price: int
                - property_size_sqft: int

        Returns:
            List of property dictionaries
        """

        # Build query
        query, params = self._build_query(filters)

        # Execute
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()

        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        # Convert to list of dicts
        properties = []
        for row in results:
            properties.append(dict(zip(columns, row)))

        return properties

    def _build_query(self, filters: dict) -> tuple:
        """Build SQL query with filters"""

        query = "SELECT * FROM properties WHERE 1=1"
        params = []

        # Add location filter
        if filters.get('location'):
            query += " AND location ILIKE %s"
            params.append(f"%{filters['location']}%")

        # Add room filter
        if filters.get('num_rooms'):
            query += " AND num_rooms = %s"
            params.append(filters['num_rooms'])

        # Add price filters
        if filters.get('max_price'):
            query += " AND price <= %s"
            params.append(filters['max_price'])

        if filters.get('min_price'):
            query += " AND price >= %s"
            params.append(filters['min_price'])

        # Add size filter
        if filters.get('property_size_sqft'):
            query += " AND property_size_sqft >= %s"
            params.append(filters['property_size_sqft'])

        # Order by price
        query += " ORDER BY price ASC LIMIT 10"

        return query, params
