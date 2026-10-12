-- Dedicated Database: catalog_db (Catalog Service - Go)
CREATE TABLE IF NOT EXISTS products (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(160) NOT NULL,
  category VARCHAR(100) NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  price NUMERIC(12,2) NOT NULL CHECK(price>=0),
  image TEXT NOT NULL DEFAULT '',
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed initial products
INSERT INTO products (id, name, category, description, price, image, active) VALUES
(1, 'AI Mechanical Keyboard', 'Workspace', 'Low-profile mechanical keyboard designed for coding sessions.', 79.99, '⌨️', true),
(2, 'CloudOps Headset', 'Audio', 'Comfortable USB headset for standups and incident calls.', 64.50, '🎧', true),
(3, 'Kubernetes Desk Mat', 'Workspace', 'Large desk mat with Kubernetes command references.', 29.00, '☸️', true),
(4, 'DevSecOps Security Key', 'Security', 'Hardware security-key demo product for MFA workflows.', 49.99, '🔐', true),
(5, 'Observability Display', 'Hardware', 'Portable display for metrics and dashboards.', 189.00, '📊', true),
(6, 'SRE Incident Notebook', 'Learning', 'Structured notebook for runbooks, incidents and postmortems.', 18.75, '📘', true)
ON CONFLICT (id) DO NOTHING;

SELECT setval('products_id_seq', (SELECT COALESCE(MAX(id), 1) FROM products));

