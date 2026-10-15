-- Dedicated reviews_db schema (Product Reviews Service - Python FastAPI)
CREATE TABLE IF NOT EXISTS product_reviews (
  id BIGSERIAL PRIMARY KEY,
  product_id BIGINT NOT NULL CHECK (product_id > 0),
  customer_id VARCHAR(200) NOT NULL,
  rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
  title VARCHAR(200) NOT NULL DEFAULT '',
  body TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (product_id, customer_id)
);

CREATE INDEX IF NOT EXISTS idx_product_reviews_product
  ON product_reviews(product_id, created_at DESC);
