-- Dedicated Database: auth_db (Auth Service - Java Spring Boot)
CREATE TABLE IF NOT EXISTS app_users (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  email VARCHAR(200) UNIQUE NOT NULL,
  password_hash VARCHAR(200) NOT NULL,
  role VARCHAR(40) NOT NULL DEFAULT 'USER',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_sessions (
  token VARCHAR(100) PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL
);

-- Seed initial admin user
INSERT INTO app_users(name, email, password_hash, role)
VALUES('DevOps Shack Admin', 'admin@devopsshack.com', '$2a$10$N.Z0/O1wW1fN6nS7gB6v.uvkFkJYjF6z.c4h7j6P1r0G0w1x2y3z4', 'ADMIN')
ON CONFLICT (email) DO NOTHING;

