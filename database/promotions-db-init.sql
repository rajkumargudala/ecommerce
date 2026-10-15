-- Dedicated promotions_db schema (Promotions Service - Python FastAPI)
CREATE TABLE IF NOT EXISTS promotions (
  id BIGSERIAL PRIMARY KEY,
  code VARCHAR(80) NOT NULL UNIQUE,
  description VARCHAR(250) NOT NULL,
  discount_type VARCHAR(16) NOT NULL CHECK (discount_type IN ('PERCENT', 'FIXED')),
  discount_value NUMERIC(10,2) NOT NULL CHECK (discount_value > 0),
  min_subtotal NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (min_subtotal >= 0),
  starts_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ends_at TIMESTAMPTZ,
  max_redemptions INTEGER CHECK (max_redemptions IS NULL OR max_redemptions > 0),
  per_customer_limit INTEGER NOT NULL DEFAULT 1 CHECK (per_customer_limit > 0),
  active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS promotion_redemptions (
  id BIGSERIAL PRIMARY KEY,
  promotion_id BIGINT NOT NULL REFERENCES promotions(id),
  customer_id VARCHAR(200) NOT NULL,
  order_id VARCHAR(100) NOT NULL UNIQUE,
  subtotal NUMERIC(12,2) NOT NULL CHECK (subtotal >= 0),
  discount_amount NUMERIC(12,2) NOT NULL CHECK (discount_amount >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (promotion_id, customer_id, order_id)
);

CREATE INDEX IF NOT EXISTS idx_promotion_redemptions_customer
  ON promotion_redemptions(promotion_id, customer_id);

INSERT INTO promotions(code, description, discount_type, discount_value, min_subtotal)
VALUES ('WELCOME10', '10% off orders of $25 or more', 'PERCENT', 10, 25),
       ('SAVE5', 'Save $5 on orders of $20 or more', 'FIXED', 5, 20)
ON CONFLICT (code) DO NOTHING;
