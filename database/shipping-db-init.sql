-- Dedicated shipping_db schema (Shipping Service - Python FastAPI)
CREATE TABLE IF NOT EXISTS shipments (
  id BIGSERIAL PRIMARY KEY,
  order_id BIGINT NOT NULL UNIQUE CHECK (order_id > 0),
  recipient_name VARCHAR(200) NOT NULL,
  address_line1 VARCHAR(250) NOT NULL,
  address_line2 VARCHAR(250) NOT NULL DEFAULT '',
  city VARCHAR(120) NOT NULL,
  region VARCHAR(120) NOT NULL DEFAULT '',
  postal_code VARCHAR(40) NOT NULL,
  country VARCHAR(100) NOT NULL,
  carrier VARCHAR(100) NOT NULL DEFAULT 'STANDARD',
  tracking_number VARCHAR(80) NOT NULL UNIQUE,
  status VARCHAR(40) NOT NULL DEFAULT 'LABEL_CREATED',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
