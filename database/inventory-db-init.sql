-- Dedicated Database: inventory_db (Inventory Service - Node.js Express)
CREATE TABLE IF NOT EXISTS inventory (
  product_id BIGINT PRIMARY KEY,
  quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity>=0),
  reserved INTEGER NOT NULL DEFAULT 0 CHECK(reserved>=0),
  reorder_level INTEGER NOT NULL DEFAULT 10 CHECK(reorder_level>=0),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK(reserved<=quantity)
);

-- Seed initial stock levels
INSERT INTO inventory (product_id, quantity, reserved, reorder_level) VALUES
(1, 60, 0, 10),
(2, 45, 0, 10),
(3, 85, 0, 10),
(4, 25, 0, 10),
(5, 8, 0, 10),
(6, 120, 0, 10)
ON CONFLICT (product_id) DO NOTHING;

