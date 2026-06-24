-- 电商业务表（Tool Calling 模拟数据源）

CREATE TABLE IF NOT EXISTS ec_users (
    id          SERIAL PRIMARY KEY,
    phone       VARCHAR(20) NOT NULL UNIQUE,
    name        VARCHAR(64) NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ec_products (
    id          SERIAL PRIMARY KEY,
    sku         VARCHAR(64) NOT NULL UNIQUE,
    name        VARCHAR(256) NOT NULL,
    category    VARCHAR(64) NOT NULL,
    price       NUMERIC(10, 2) NOT NULL,
    stock       INT NOT NULL DEFAULT 0,
    description TEXT,
    status      VARCHAR(16) NOT NULL DEFAULT 'on_sale',
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ec_orders (
    id               SERIAL PRIMARY KEY,
    order_no         VARCHAR(32) NOT NULL UNIQUE,
    user_id          INT NOT NULL REFERENCES ec_users(id),
    status           VARCHAR(32) NOT NULL,
    total_amount     NUMERIC(10, 2) NOT NULL,
    shipping_address TEXT,
    created_at       TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ec_order_items (
    id           SERIAL PRIMARY KEY,
    order_id     INT NOT NULL REFERENCES ec_orders(id) ON DELETE CASCADE,
    product_id   INT NOT NULL REFERENCES ec_products(id),
    sku          VARCHAR(64) NOT NULL,
    product_name VARCHAR(256) NOT NULL,
    quantity     INT NOT NULL,
    unit_price   NUMERIC(10, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS ec_logistics (
    id            SERIAL PRIMARY KEY,
    order_id      INT NOT NULL REFERENCES ec_orders(id) ON DELETE CASCADE,
    order_no      VARCHAR(32) NOT NULL,
    carrier       VARCHAR(64) NOT NULL,
    tracking_no   VARCHAR(64) NOT NULL,
    status        VARCHAR(32) NOT NULL,
    latest_event  TEXT,
    updated_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ec_refunds (
    id          SERIAL PRIMARY KEY,
    refund_no   VARCHAR(32) NOT NULL UNIQUE,
    order_id    INT NOT NULL REFERENCES ec_orders(id),
    order_no    VARCHAR(32) NOT NULL,
    reason      TEXT NOT NULL,
    amount      NUMERIC(10, 2) NOT NULL,
    status      VARCHAR(32) NOT NULL DEFAULT 'pending',
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ec_orders_user_id ON ec_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_ec_orders_order_no ON ec_orders(order_no);
CREATE INDEX IF NOT EXISTS idx_ec_logistics_order_no ON ec_logistics(order_no);
CREATE INDEX IF NOT EXISTS idx_ec_logistics_tracking_no ON ec_logistics(tracking_no);
CREATE INDEX IF NOT EXISTS idx_ec_refunds_order_no ON ec_refunds(order_no);
CREATE INDEX IF NOT EXISTS idx_ec_products_name ON ec_products(name);
CREATE INDEX IF NOT EXISTS idx_ec_products_category ON ec_products(category);
