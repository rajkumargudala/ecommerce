-- Dedicated search_db schema (Search Service - Python FastAPI)
CREATE TABLE IF NOT EXISTS search_documents (
  product_id BIGINT PRIMARY KEY CHECK (product_id > 0),
  name VARCHAR(160) NOT NULL,
  category VARCHAR(100) NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  price NUMERIC(12,2) NOT NULL CHECK (price >= 0),
  image TEXT NOT NULL DEFAULT '',
  active BOOLEAN NOT NULL DEFAULT TRUE,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_search_documents_vector
  ON search_documents USING GIN (
    to_tsvector('english', name || ' ' || category || ' ' || description)
  );
