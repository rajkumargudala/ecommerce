-- Dedicated cart_db schema (Cart Service - Python FastAPI)
CREATE TABLE IF NOT EXISTS cart_items (
  customer_id VARCHAR(200) NOT NULL,
  product_id BIGINT NOT NULL CHECK (product_id > 0),
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (customer_id, product_id)
);
