-- Dedicated Database: payment_db (Payment Service - C# ASP.NET Core)
CREATE TABLE IF NOT EXISTS payments (
  id BIGSERIAL PRIMARY KEY,
  order_id BIGINT NOT NULL,
  amount NUMERIC(12,2) NOT NULL CHECK(amount>0),
  method VARCHAR(40) NOT NULL,
  status VARCHAR(40) NOT NULL,
  transaction_ref VARCHAR(100) NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  refunded_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS idx_payments_order_id ON payments(order_id);

