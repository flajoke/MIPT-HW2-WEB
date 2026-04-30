import sqlite3
from .config import settings

DEMO_SESSION_ID = "session-demo-001"
DEMO_PRODUCT_ID = "00000000-0000-0000-0000-000000000001"
DEMO_ITEM_ID = "20000000-0000-0000-0000-000000000001"
DEMO_ORDER_ID = "30000000-0000-0000-0000-000000000001"
DEMO_ORDER_NUMBER = "ORD-20260412-0001"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS carts (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('ACTIVE', 'ORDERED', 'EXPIRED')),
                subtotal REAL NOT NULL DEFAULT 0 CHECK (subtotal >= 0),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS cart_items (
                id TEXT PRIMARY KEY,
                cart_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                sku TEXT NOT NULL,
                product_name TEXT NOT NULL,
                unit_price REAL NOT NULL CHECK (unit_price >= 0),
                qty INTEGER NOT NULL CHECK (qty > 0),
                line_total REAL NOT NULL CHECK (line_total >= 0),
                FOREIGN KEY(cart_id) REFERENCES carts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                order_number TEXT NOT NULL UNIQUE,
                cart_id TEXT,
                customer_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL,
                city TEXT NOT NULL,
                address TEXT NOT NULL,
                comment TEXT,
                subtotal REAL NOT NULL,
                delivery_cost REAL NOT NULL,
                total REAL NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('NEW', 'CONFIRMED', 'ASSEMBLING', 'SHIPPED', 'COMPLETED', 'CANCELLED')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(cart_id) REFERENCES carts(id)
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                sku TEXT NOT NULL,
                product_name TEXT NOT NULL,
                unit_price REAL NOT NULL,
                qty INTEGER NOT NULL,
                line_total REAL NOT NULL,
                FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS order_status_history (
                id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                from_status TEXT,
                to_status TEXT NOT NULL,
                changed_by TEXT NOT NULL,
                changed_at TEXT NOT NULL,
                comment TEXT,
                FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_carts_session ON carts(session_id);
            CREATE INDEX IF NOT EXISTS idx_cart_items_cart ON cart_items(cart_id);
            CREATE INDEX IF NOT EXISTS idx_orders_number ON orders(order_number);
            CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
            CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
            """
        )
        seed_database(conn)


def seed_database(conn: sqlite3.Connection) -> None:
    exists = conn.execute("SELECT id FROM orders WHERE id = ?", (DEMO_ORDER_ID,)).fetchone()
    if exists:
        return
    ts = "2026-04-12T10:00:00+00:00"
    seed_cart_id = "40000000-0000-0000-0000-000000000001"
    conn.execute(
        "INSERT OR IGNORE INTO carts (id, session_id, status, subtotal, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (seed_cart_id, "seed-order-session-001", "ORDERED", 398.0, ts, ts),
    )
    conn.execute(
        """
        INSERT INTO orders (
            id, order_number, cart_id, customer_name, phone, email, city, address, comment,
            subtotal, delivery_cost, total, status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            DEMO_ORDER_ID,
            DEMO_ORDER_NUMBER,
            seed_cart_id,
            "Иван Иванов",
            "+79990000000",
            "ivan@example.com",
            "Москва",
            "ул. Ленина, д. 1",
            "Демо-заказ из исходной Postman-коллекции",
            398.0,
            0.0,
            398.0,
            "NEW",
            ts,
            ts,
        ),
    )
    conn.execute(
        """
        INSERT INTO order_items (id, order_id, product_id, sku, product_name, unit_price, qty, line_total)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "31000000-0000-0000-0000-000000000001",
            DEMO_ORDER_ID,
            DEMO_PRODUCT_ID,
            "LMP-A60-10W-E27-4000K",
            "Лампочка LED A60 10W E27 4000K",
            199.0,
            2,
            398.0,
        ),
    )
    conn.execute(
        """
        INSERT INTO order_status_history (id, order_id, from_status, to_status, changed_by, changed_at, comment)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "32000000-0000-0000-0000-000000000001",
            DEMO_ORDER_ID,
            None,
            "NEW",
            "order-service",
            ts,
            "Заказ создан",
        ),
    )
