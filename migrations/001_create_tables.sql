-- Phase 1: Simple Database Schema for Real Estate Search Engine
-- Matches columns from assets/Property_list.xlsx

-- Drop existing tables
DROP TABLE IF EXISTS properties CASCADE;

-- Main properties table - stores canonical row data from Excel
CREATE TABLE properties (
    id SERIAL PRIMARY KEY,
    property_id VARCHAR(50) UNIQUE NOT NULL,
    num_rooms INTEGER,
    property_size_sqft INTEGER,
    title_short_description TEXT,
    long_description TEXT,
    location TEXT,
    price BIGINT,
    seller_type VARCHAR(50),
    listing_date TIMESTAMP,
    certificates TEXT,
    seller_contact TEXT,
    metadata_tags TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Basic indexes for search
CREATE INDEX idx_location ON properties(location);
CREATE INDEX idx_price ON properties(price);
CREATE INDEX idx_num_rooms ON properties(num_rooms);
