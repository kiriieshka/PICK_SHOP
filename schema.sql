CREATE TABLE IF NOT EXISTS orders (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    username VARCHAR(255),
    product VARCHAR(30) NOT NULL,
    amount NUMERIC(10,2) NOT NULL,
    status VARCHAR(40) NOT NULL,
    payment_id VARCHAR(100) UNIQUE,
    full_name VARCHAR(255),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP NULL,
    details_received_at TIMESTAMP NULL
);

CREATE TABLE IF NOT EXISTS activation_codes (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'available',
    order_id BIGINT NULL,
    buyer_telegram_id BIGINT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    issued_at TIMESTAMP NULL,
    activated_at TIMESTAMP NULL
);

CREATE TABLE IF NOT EXISTS activated_users (
    telegram_id BIGINT PRIMARY KEY,
    activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
