import json
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

DB_PATH = os.getenv("CATALOG_DB_PATH", "catalog.sqlite3")
HOST = os.getenv("CATALOG_HOST", "0.0.0.0")
PORT = int(os.getenv("CATALOG_PORT", "8081"))

DEMO_CATEGORY_ID = "10000000-0000-0000-0000-000000000001"
DEMO_PRODUCT_ID = "00000000-0000-0000-0000-000000000001"
VALID_STATUSES = {"ACTIVE", "ARCHIVED", "OUT_OF_STOCK"}

TRANSLIT = str.maketrans({
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh", "з": "z",
    "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
    "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "c", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
})


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_uuid() -> str:
    return str(uuid.uuid4())


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def slugify(value: str) -> str:
    raw = (value or "").lower().translate(TRANSLIT)
    raw = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")
    return raw or f"product-{uuid.uuid4().hex[:8]}"


def unique_slug(conn: sqlite3.Connection, name: str, product_id: str | None = None) -> str:
    base = slugify(name)
    slug = base
    idx = 2
    while True:
        if product_id:
            row = conn.execute("SELECT id FROM products WHERE slug = ? AND id <> ?", (slug, product_id)).fetchone()
        else:
            row = conn.execute("SELECT id FROM products WHERE slug = ?", (slug,)).fetchone()
        if not row:
            return slug
        slug = f"{base}-{idx}"
        idx += 1


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
    if not exists:
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


def parse_body(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", "0") or 0)
    if length == 0:
        return {}
    raw = handler.rfile.read(length).decode("utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Некорректный JSON: {exc.msg}")
    if not isinstance(data, dict):
        raise ValueError("Тело запроса должно быть JSON-объектом")
    return data


def json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict | list | None = None) -> None:
    body = json.dumps(payload if payload is not None else {}, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
    handler.wfile.write(body)


def error_response(handler: BaseHTTPRequestHandler, status: int, message: str, details: dict | None = None) -> None:
    payload = {"error": message}
    if details:
        payload["details"] = details
    json_response(handler, status, payload)


def product_to_dict(conn: sqlite3.Connection, row: sqlite3.Row) -> dict:
    category = conn.execute("SELECT id, code, name, is_active FROM categories WHERE id = ?", (row["category_id"],)).fetchone()
    images = conn.execute(
        "SELECT id, product_id, url, alt_text, sort_order, is_primary FROM product_images WHERE product_id = ? ORDER BY sort_order, id",
        (row["id"],),
    ).fetchall()
    stock = int(row["stock_qty"])
    reserved = int(row["reserved_qty"])
    return {
        "id": row["id"],
        "sku": row["sku"],
        "name": row["name"],
        "slug": row["slug"],
        "description": row["description"],
        "category_id": row["category_id"],
        "category": dict(category) if category else None,
        "price": float(row["price"]),
        "currency": row["currency"],
        "stock_qty": stock,
        "reserved_qty": reserved,
        "available_qty": max(0, stock - reserved),
        "socket_type": row["socket_type"],
        "wattage": int(row["wattage"]),
        "color_temperature": int(row["color_temperature"]),
        "voltage": row["voltage"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "images": [
            {
                "id": img["id"],
                "product_id": img["product_id"],
                "url": img["url"],
                "alt_text": img["alt_text"],
                "sort_order": int(img["sort_order"]),
                "is_primary": bool(img["is_primary"]),
            }
            for img in images
        ],
    }


def require_fields(data: dict, fields: list[str]) -> list[str]:
    return [field for field in fields if data.get(field) in (None, "")]


def normalize_status_from_stock(status: str, stock_qty: int, reserved_qty: int) -> str:
    if status == "ARCHIVED":
        return status
    if stock_qty - reserved_qty <= 0:
        return "OUT_OF_STOCK"
    return status if status in VALID_STATUSES else "ACTIVE"


class CatalogHandler(BaseHTTPRequestHandler):
    server_version = "catalog-service/1.0"

    def log_message(self, fmt: str, *args) -> None:
        print(f"[{now_iso()}] {self.address_string()} - {fmt % args}")

    def do_OPTIONS(self) -> None:
        json_response(self, 204, None)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)
        if path == "/health":
            return json_response(self, 200, {"status": "ok", "service": "catalog-service"})
        if path == "/api/v1/products":
            return self.handle_list_products(query)
        match = re.fullmatch(r"/api/v1/products/([^/]+)", path)
        if match:
            return self.handle_get_product(match.group(1))
        return error_response(self, 404, "Маршрут не найден")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        if path == "/api/v1/products":
            return self.handle_create_product()
        match = re.fullmatch(r"/api/v1/products/([^/]+)/archive", path)
        if match:
            return self.handle_archive_product(match.group(1))
        match = re.fullmatch(r"/api/v1/products/([^/]+)/(reserve|release|deduct)", path)
        if match:
            return self.handle_stock_action(match.group(1), match.group(2))
        return error_response(self, 404, "Маршрут не найден")

    def do_PATCH(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        match = re.fullmatch(r"/api/v1/products/([^/]+)", path)
        if match:
            return self.handle_patch_product(match.group(1))
        return error_response(self, 404, "Маршрут не найден")

    def handle_list_products(self, query: dict) -> None:
        page = max(1, int(query.get("page", ["1"])[0] or 1))
        limit = min(100, max(1, int(query.get("limit", ["20"])[0] or 20)))
        filters = []
        params: list[object] = []
        allowed_exact = ["status", "category_id", "socket_type", "wattage", "color_temperature"]
        for field in allowed_exact:
            if field in query and query[field][0] != "":
                filters.append(f"{field} = ?")
                params.append(query[field][0])
        if "price_min" in query:
            filters.append("price >= ?")
            params.append(float(query["price_min"][0]))
        if "price_max" in query:
            filters.append("price <= ?")
            params.append(float(query["price_max"][0]))
        if "q" in query and query["q"][0].strip():
            filters.append("(LOWER(name) LIKE ? OR LOWER(sku) LIKE ?)")
            value = f"%{query['q'][0].strip().lower()}%"
            params.extend([value, value])
        where_sql = " WHERE " + " AND ".join(filters) if filters else ""
        sort_by = query.get("sort_by", ["created_at"])[0]
        sort_map = {"name": "name", "price": "price", "created_at": "created_at", "stock_qty": "stock_qty"}
        sort_col = sort_map.get(sort_by, "created_at")
        sort_order = query.get("sort_order", ["desc"])[0].lower()
        direction = "ASC" if sort_order == "asc" else "DESC"
        offset = (page - 1) * limit
        with connect() as conn:
            total = conn.execute(f"SELECT COUNT(*) AS total FROM products{where_sql}", params).fetchone()["total"]
            rows = conn.execute(
                f"SELECT * FROM products{where_sql} ORDER BY {sort_col} {direction}, id LIMIT ? OFFSET ?",
                [*params, limit, offset],
            ).fetchall()
            items = [product_to_dict(conn, row) for row in rows]
        json_response(self, 200, {"items": items, "page": page, "limit": limit, "total": int(total)})

    def handle_get_product(self, product_id: str) -> None:
        with connect() as conn:
            row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            if not row:
                return error_response(self, 404, "Товар не найден")
            json_response(self, 200, product_to_dict(conn, row))

    def handle_create_product(self) -> None:
        try:
            data = parse_body(self)
        except ValueError as exc:
            return error_response(self, 400, str(exc))
        missing = require_fields(data, ["sku", "name", "category_id", "price", "stock_qty", "socket_type", "wattage", "color_temperature"])
        if missing:
            return error_response(self, 400, "Не заполнены обязательные поля", {"missing": missing})
        status = data.get("status", "ACTIVE")
        if status not in VALID_STATUSES:
            return error_response(self, 400, "Недопустимый статус товара")
        with connect() as conn:
            category = conn.execute("SELECT id FROM categories WHERE id = ? AND is_active = 1", (data["category_id"],)).fetchone()
            if not category:
                return error_response(self, 404, "Категория не найдена или неактивна")
            product_id = data.get("id") or new_uuid()
            ts = now_iso()
            reserved_qty = int(data.get("reserved_qty", 0) or 0)
            stock_qty = int(data["stock_qty"])
            status = normalize_status_from_stock(status, stock_qty, reserved_qty)
            try:
                conn.execute(
                    """
                    INSERT INTO products (
                        id, sku, name, slug, description, category_id, price, currency,
                        stock_qty, reserved_qty, socket_type, wattage, color_temperature,
                        voltage, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        product_id,
                        data["sku"],
                        data["name"],
                        unique_slug(conn, data["name"]),
                        data.get("description"),
                        data["category_id"],
                        float(data["price"]),
                        data.get("currency", "RUB"),
                        stock_qty,
                        reserved_qty,
                        data["socket_type"],
                        int(data["wattage"]),
                        int(data["color_temperature"]),
                        data.get("voltage"),
                        status,
                        ts,
                        ts,
                    ),
                )
                for idx, img in enumerate(data.get("images", []) or [], start=1):
                    conn.execute(
                        """
                        INSERT INTO product_images (id, product_id, url, alt_text, sort_order, is_primary)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            img.get("id") or new_uuid(),
                            product_id,
                            img["url"],
                            img.get("alt_text"),
                            int(img.get("sort_order", idx)),
                            1 if img.get("is_primary", idx == 1) else 0,
                        ),
                    )
            except sqlite3.IntegrityError as exc:
                return error_response(self, 409, "Товар с таким id, sku или slug уже существует", {"sqlite": str(exc)})
            row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            json_response(self, 201, product_to_dict(conn, row))

    def handle_patch_product(self, product_id: str) -> None:
        try:
            data = parse_body(self)
        except ValueError as exc:
            return error_response(self, 400, str(exc))
        allowed = {
            "sku", "name", "description", "category_id", "price", "currency", "stock_qty",
            "reserved_qty", "socket_type", "wattage", "color_temperature", "voltage", "status"
        }
        updates = {k: v for k, v in data.items() if k in allowed}
        if not updates:
            return error_response(self, 400, "Нет полей для обновления")
        if "status" in updates and updates["status"] not in VALID_STATUSES:
            return error_response(self, 400, "Недопустимый статус товара")
        with connect() as conn:
            row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            if not row:
                return error_response(self, 404, "Товар не найден")
            if "category_id" in updates:
                category = conn.execute("SELECT id FROM categories WHERE id = ? AND is_active = 1", (updates["category_id"],)).fetchone()
                if not category:
                    return error_response(self, 404, "Категория не найдена или неактивна")
            if "name" in updates:
                updates["slug"] = unique_slug(conn, str(updates["name"]), product_id)
            if "price" in updates:
                updates["price"] = float(updates["price"])
            for int_field in ["stock_qty", "reserved_qty", "wattage", "color_temperature", "voltage"]:
                if int_field in updates and updates[int_field] is not None:
                    updates[int_field] = int(updates[int_field])
            updates["updated_at"] = now_iso()
            set_sql = ", ".join(f"{field} = ?" for field in updates.keys())
            try:
                conn.execute(f"UPDATE products SET {set_sql} WHERE id = ?", [*updates.values(), product_id])
            except sqlite3.IntegrityError as exc:
                return error_response(self, 409, "Нарушение уникальности или ограничения БД", {"sqlite": str(exc)})
            row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            json_response(self, 200, product_to_dict(conn, row))

    def handle_archive_product(self, product_id: str) -> None:
        with connect() as conn:
            row = conn.execute("SELECT id FROM products WHERE id = ?", (product_id,)).fetchone()
            if not row:
                return error_response(self, 404, "Товар не найден")
            conn.execute("UPDATE products SET status = 'ARCHIVED', updated_at = ? WHERE id = ?", (now_iso(), product_id))
            row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            json_response(self, 200, product_to_dict(conn, row))

    def handle_stock_action(self, product_id: str, action: str) -> None:
        try:
            data = parse_body(self)
        except ValueError as exc:
            return error_response(self, 400, str(exc))
        qty = int(data.get("qty", 0) or 0)
        if qty <= 0:
            return error_response(self, 400, "qty должен быть положительным числом")
        with connect() as conn:
            row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            if not row:
                return error_response(self, 404, "Товар не найден")
            stock = int(row["stock_qty"])
            reserved = int(row["reserved_qty"])
            if action == "reserve":
                if row["status"] != "ACTIVE":
                    return error_response(self, 409, "Нельзя резервировать неактивный товар")
                if stock - reserved < qty:
                    return error_response(self, 409, "Недостаточно товара на складе", {"available_qty": stock - reserved})
                reserved += qty
            elif action == "release":
                reserved = max(0, reserved - qty)
            elif action == "deduct":
                if stock < qty:
                    return error_response(self, 409, "Недостаточно остатка для списания", {"stock_qty": stock})
                stock -= qty
                reserved = max(0, reserved - qty)
            status = row["status"]
            if status != "ARCHIVED":
                status = "OUT_OF_STOCK" if stock - reserved <= 0 else "ACTIVE"
            conn.execute(
                "UPDATE products SET stock_qty = ?, reserved_qty = ?, status = ?, updated_at = ? WHERE id = ?",
                (stock, reserved, status, now_iso(), product_id),
            )
            updated = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            json_response(self, 200, product_to_dict(conn, updated))


def main() -> None:
    init_db()
    server = ThreadingHTTPServer((HOST, PORT), CatalogHandler)
    print(f"catalog-service запущен: http://{HOST}:{PORT}")
    print(f"База данных: {os.path.abspath(DB_PATH)}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nОстановка catalog-service")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
