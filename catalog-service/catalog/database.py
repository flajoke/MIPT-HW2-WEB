import sqlite3
from .config import settings
from .utils import now_iso

DEMO_CATEGORY_ID = "10000000-0000-0000-0000-000000000001"
DEMO_PRODUCT_ID = "00000000-0000-0000-0000-000000000001"

CATEGORY_IDS = {
    "led-lamps": DEMO_CATEGORY_ID,
    "decor": "10000000-0000-0000-0000-000000000002",
    "fixtures": "10000000-0000-0000-0000-000000000003",
}


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
    ts = now_iso()
    conn.executemany(
        "INSERT OR IGNORE INTO categories (id, code, name, is_active) VALUES (?, ?, ?, ?)",
        [
            (CATEGORY_IDS["led-lamps"], "led-lamps", "LED лампы", 1),
            (CATEGORY_IDS["decor"], "decor", "Декоративный свет", 1),
            (CATEGORY_IDS["fixtures"], "fixtures", "Светильники", 1),
        ],
    )

    products = [
        (
            DEMO_PRODUCT_ID,
            "LMP-A60-10W-E27-4000K",
            "Лампочка LED A60 10W E27 4000K",
            "lampochka-led-a60-10w-e27-4000k",
            "Матовая светодиодная лампа для дома с нейтральным белым светом. Подходит для люстр, настольных ламп и бра.",
            CATEGORY_IDS["led-lamps"],
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
        (
            "00000000-0000-0000-0000-000000000002",
            "LMP-C37-7W-E14-3000K",
            "Лампочка-свеча C37 7W E14 3000K",
            "lampochka-svecha-c37-7w-e14-3000k",
            "Компактная лампа формы «свеча» с тёплым светом для декоративных люстр и торшеров.",
            CATEGORY_IDS["led-lamps"],
            179.0,
            "RUB",
            64,
            0,
            "E14",
            7,
            3000,
            220,
            "ACTIVE",
            ts,
            ts,
        ),
        (
            "00000000-0000-0000-0000-000000000003",
            "LMP-G45-6W-E27-2700K",
            "Лампочка-шар G45 6W E27 2700K",
            "lampochka-shar-g45-6w-e27-2700k",
            "Небольшая лампа-шар с мягким тёплым свечением для уютного освещения спальни или гостиной.",
            CATEGORY_IDS["led-lamps"],
            149.0,
            "RUB",
            0,
            0,
            "E27",
            6,
            2700,
            220,
            "OUT_OF_STOCK",
            ts,
            ts,
        ),
        (
            "00000000-0000-0000-0000-000000000004",
            "STRIP-5M-12W-RGB",
            "Светодиодная лента RGB 5 м",
            "svetodiodnaya-lenta-rgb-5m",
            "Гибкая RGB-лента для акцентной подсветки кухни, рабочего места или витрины. В комплекте пульт управления.",
            CATEGORY_IDS["decor"],
            1290.0,
            "RUB",
            27,
            0,
            "12V адаптер",
            12,
            3000,
            12,
            "ACTIVE",
            ts,
            ts,
        ),
        (
            "00000000-0000-0000-0000-000000000005",
            "FIX-ROUND-18W-4000K",
            "Встраиваемый светильник Round 18W 4000K",
            "vstraivaemyj-svetilnik-round-18w-4000k",
            "Тонкий круглый светильник для потолков с равномерным нейтральным светом и быстрым монтажом.",
            CATEGORY_IDS["fixtures"],
            890.0,
            "RUB",
            38,
            0,
            "Встроенный драйвер",
            18,
            4000,
            220,
            "ACTIVE",
            ts,
            ts,
        ),
        (
            "00000000-0000-0000-0000-000000000006",
            "TRACK-12W-3000K-BLACK",
            "Трековый светильник 12W Black 3000K",
            "trekovyj-svetilnik-12w-black-3000k",
            "Акцентный трековый светильник в чёрном корпусе для витрин, кухни и зонального освещения.",
            CATEGORY_IDS["fixtures"],
            1490.0,
            "RUB",
            16,
            0,
            "Трековый адаптер",
            12,
            3000,
            220,
            "ACTIVE",
            ts,
            ts,
        ),
        (
            "00000000-0000-0000-0000-000000000007",
            "GARLAND-10M-WARM",
            "Гирлянда Warm Light 10 м",
            "girlyanda-warm-light-10m",
            "Декоративная гирлянда с тёплым свечением для комнаты, балкона или праздничного оформления.",
            CATEGORY_IDS["decor"],
            990.0,
            "RUB",
            44,
            0,
            "USB",
            5,
            3000,
            5,
            "ACTIVE",
            ts,
            ts,
        ),
        (
            "00000000-0000-0000-0000-000000000008",
            "PANEL-36W-6000K",
            "Панельный светильник 36W 6000K",
            "panelnyj-svetilnik-36w-6000k",
            "Яркий панельный светильник холодного белого света для кабинета, коридора или рабочего пространства.",
            CATEGORY_IDS["fixtures"],
            1790.0,
            "RUB",
            21,
            0,
            "Встроенный драйвер",
            36,
            6000,
            220,
            "ACTIVE",
            ts,
            ts,
        ),
    ]

    conn.executemany(
        """
        INSERT OR IGNORE INTO products (
            id, sku, name, slug, description, category_id, price, currency,
            stock_qty, reserved_qty, socket_type, wattage, color_temperature,
            voltage, status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        products,
    )

    image_rows = [
        ("11000000-0000-0000-0000-000000000001", DEMO_PRODUCT_ID, "https://example.com/images/led-a60-main.jpg", "Лампочка LED A60, главное фото", 1, 1),
        ("11000000-0000-0000-0000-000000000002", DEMO_PRODUCT_ID, "https://example.com/images/led-a60-box.jpg", "Упаковка LED A60", 2, 0),
    ]
    conn.executemany(
        """
        INSERT OR IGNORE INTO product_images (id, product_id, url, alt_text, sort_order, is_primary)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        image_rows,
    )
