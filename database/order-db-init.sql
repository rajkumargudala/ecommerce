-- Dedicated Database: order_db (Order Service - Python FastAPI)
CREATE TABLE IF NOT EXISTS orders (
  id BIGSERIAL PRIMARY KEY,
  user_email VARCHAR(200) NOT NULL,
  status VARCHAR(40) NOT NULL DEFAULT 'CREATED',
  total NUMERIC(12,2) NOT NULL CHECK(total>=0),
  items JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_orders_user_email ON orders(user_email);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);

