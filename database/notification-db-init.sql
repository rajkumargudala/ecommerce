-- Dedicated Database: notification_db (Notification Service - Ruby Sinatra)
CREATE TABLE IF NOT EXISTS notifications (
  id BIGSERIAL PRIMARY KEY,
  recipient VARCHAR(200) NOT NULL,
  type VARCHAR(50) NOT NULL,
  subject VARCHAR(200) NOT NULL,
  message TEXT NOT NULL,
  is_read BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notifications_recipient ON notifications(lower(recipient));

-- Seed welcome notification
INSERT INTO notifications(recipient, type, subject, message)
VALUES(
  'admin@admin.com',
  'WELCOME',
  'Polyglot platform is ready',
  'Ruby Notification Service is ready with its dedicated PostgreSQL database on EKS.'
);

