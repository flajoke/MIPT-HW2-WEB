import sqlite3
from .config import settings
from .utils import now_iso

DEMO_CATEGORY_ID = "10000000-0000-0000-0000-000000000001"
DEMO_PRODUCT_ID = "00000000-0000-0000-0000-000000000001"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id TEXT PRIMARY KEY,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                sku TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                slug TEXT NOT NULL UNIQUE,
                description TEXT,
                category_id TEXT NOT NULL,
                price REAL NOT NULL CHECK (price >= 0),
                currency TEXT NOT NULL DEFAULT 'RUB',
                stock_qty INTEGER NOT NULL DEFAULT 0 CHECK (stock_qty >= 0),
                reserved_qty INTEGER NOT NULL DEFAULT 0 CHECK (reserved_qty >= 0),
                socket_type TEXT NOT NULL,
                wattage INTEGER NOT NULL CHECK (wattage > 0),
                color_temperature INTEGER NOT NULL CHECK (color_temperature > 0),
                voltage INTEGER,
                status TEXT NOT NULL CHECK (status IN ('ACTIVE', 'ARCHIVED', 'OUT_OF_STOCK')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(category_id) REFERENCES categories(id)
            );

            CREATE TABLE IF NOT EXISTS product_images (
                id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL,
                url TEXT NOT NULL,
                alt_text TEXT,
                sort_order INTEGER NOT NULL DEFAULT 0,
                is_primary INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
            CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);
            CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
            """
        )
        seed_database(conn)


def seed_database(conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO categories (id, code, name, is_active) VALUES (?, ?, ?, ?)",
        (DEMO_CATEGORY_ID, "led-lamps", "LED лампы", 1),
    )
    exists = conn.execute("SELECT id FROM products WHERE id = ?", (DEMO_PRODUCT_ID,)).fetchone()
    if exists:
        return
    ts = now_iso()
    conn.execute(
        """
        INSERT INTO products (
            id, sku, name, slug, description, category_id, price, currency,
            stock_qty, reserved_qty, socket_type, wattage, color_temperature,
            voltage, status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            DEMO_PRODUCT_ID,
            "LMP-A60-10W-E27-4000K",
            "Лампочка LED A60 10W E27 4000K",
            "lampochka-led-a60-10w-e27-4000k",
            "Матовая светодиодная лампа для дома",
            DEMO_CATEGORY_ID,
            199.0,
            "RUB",
            120,
            0,
            "E27",
            10,
            4000,
            220,
            "ACTIVE",
            ts,
            ts,
        ),
    )
    conn.executemany(
        """
        INSERT INTO product_images (id, product_id, url, alt_text, sort_order, is_primary)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            ("11000000-0000-0000-0000-000000000001", DEMO_PRODUCT_ID, "https://example.com/images/led-a60-main.jpg", "Лампочка LED A60, главное фото", 1, 1),
            ("11000000-0000-0000-0000-000000000002", DEMO_PRODUCT_ID, "https://example.com/images/led-a60-box.jpg", "Упаковка LED A60", 2, 0),
        ],
    )
