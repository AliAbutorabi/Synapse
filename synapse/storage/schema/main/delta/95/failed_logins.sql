CREATE TABLE IF NOT EXISTS failed_logins (
    id SERIAL PRIMARY KEY,
    user_id TEXT,
    ip_address TEXT,
    user_agent TEXT,
    failure_time BIGINT
);