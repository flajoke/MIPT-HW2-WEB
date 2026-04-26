import json
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

DB_PATH = os.getenv("ORDER_DB_PATH", "order.sqlite3")
HOST = os.getenv("ORDER_HOST", "0.0.0.0")
PORT = int(os.getenv("ORDER_PORT", "8082"))
CATALOG_BASE_URL = os.getenv("CATALOG_BASE_URL", "http://localhost:8081").rstrip("/")

DEMO_SESSION_ID = "session-demo-001"
DEMO_PRODUCT_ID = "00000000-0000-0000-0000-000000000001"
DEMO_ITEM_ID = "20000000-0000-0000-0000-000000000001"
DEMO_ORDER_ID = "30000000-0000-0000-0000-000000000001"
DEMO_ORDER_NUMBER = "ORD-20260412-0001"

CART_STATUSES = {"ACTIVE", "ORDERED", "EXPIRED"}
ORDER_STATUSES = {"NEW", "CONFIRMED", "ASSEMBLING", "SHIPPED", "COMPLETED", "CANCELLED"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_uuid() -> str:
    return str(uuid.uuid4())


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS carts (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL CHECK (status IN ('ACTIVE', 'ORDERED', 'EXPIRED')),
                subtotal REAL NOT NULL DEFAULT 0,
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


class ServiceError(Exception):
    def __init__(self, status: int, message: str, details: dict | None = None):
        super().__init__(message)
        self.status = status
        self.message = message
        self.details = details


def catalog_request(method: str, path: str, body: dict | None = None) -> dict:
    url = f"{CATALOG_BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    payload = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = Request(url, data=payload, headers=headers, method=method)
    try:
        with urlopen(req, timeout=5) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"error": raw}
        raise ServiceError(exc.code, parsed.get("error", "Ошибка catalog-service"), parsed)
    except URLError as exc:
        raise ServiceError(503, "catalog-service недоступен", {"url": url, "reason": str(exc.reason)})


def get_catalog_product(product_id: str) -> dict:
    product = catalog_request("GET", f"/api/v1/products/{product_id}")
    if product.get("status") != "ACTIVE":
        raise ServiceError(409, "Товар не активен", {"product_id": product_id, "status": product.get("status")})
    return product


def reserve_product(product_id: str, qty: int) -> None:
    catalog_request("POST", f"/api/v1/products/{product_id}/reserve", {"qty": qty})


def release_product(product_id: str, qty: int) -> None:
    catalog_request("POST", f"/api/v1/products/{product_id}/release", {"qty": qty})


def deduct_product(product_id: str, qty: int) -> None:
    catalog_request("POST", f"/api/v1/products/{product_id}/deduct", {"qty": qty})


def get_or_create_active_cart(conn: sqlite3.Connection, session_id: str) -> sqlite3.Row:
    cart = conn.execute("SELECT * FROM carts WHERE session_id = ? AND status = 'ACTIVE'", (session_id,)).fetchone()
    if cart:
        return cart
    locked = conn.execute("SELECT * FROM carts WHERE session_id = ?", (session_id,)).fetchone()
    if locked:
        raise ServiceError(409, "Для этой сессии уже есть неактивная корзина", {"status": locked["status"]})
    ts = now_iso()
    cart_id = "10000000-0000-0000-0000-000000000002" if session_id == DEMO_SESSION_ID else new_uuid()
    conn.execute(
        "INSERT INTO carts (id, session_id, status, subtotal, created_at, updated_at) VALUES (?, ?, 'ACTIVE', 0, ?, ?)",
        (cart_id, session_id, ts, ts),
    )
    return conn.execute("SELECT * FROM carts WHERE id = ?", (cart_id,)).fetchone()


def update_cart_subtotal(conn: sqlite3.Connection, cart_id: str) -> float:
    subtotal = conn.execute("SELECT COALESCE(SUM(line_total), 0) AS subtotal FROM cart_items WHERE cart_id = ?", (cart_id,)).fetchone()["subtotal"]
    subtotal = float(subtotal or 0)
    conn.execute("UPDATE carts SET subtotal = ?, updated_at = ? WHERE id = ?", (subtotal, now_iso(), cart_id))
    return subtotal


def cart_to_dict(conn: sqlite3.Connection, cart: sqlite3.Row) -> dict:
    items = conn.execute("SELECT * FROM cart_items WHERE cart_id = ? ORDER BY product_name, id", (cart["id"],)).fetchall()
    subtotal = float(cart["subtotal"] or 0)
    return {
        "id": cart["id"],
        "session_id": cart["session_id"],
        "status": cart["status"],
        "subtotal": subtotal,
        "created_at": cart["created_at"],
        "updated_at": cart["updated_at"],
        "items": [
            {
                "id": item["id"],
                "cart_id": item["cart_id"],
                "product_id": item["product_id"],
                "sku": item["sku"],
                "product_name": item["product_name"],
                "unit_price": float(item["unit_price"]),
                "qty": int(item["qty"]),
                "line_total": float(item["line_total"]),
            }
            for item in items
        ],
    }


def order_to_dict(conn: sqlite3.Connection, order: sqlite3.Row, include_history: bool = True) -> dict:
    items = conn.execute("SELECT * FROM order_items WHERE order_id = ? ORDER BY product_name, id", (order["id"],)).fetchall()
    history = []
    if include_history:
        history_rows = conn.execute(
            "SELECT * FROM order_status_history WHERE order_id = ? ORDER BY changed_at, id",
            (order["id"],),
        ).fetchall()
        history = [
            {
                "id": row["id"],
                "order_id": row["order_id"],
                "from_status": row["from_status"],
                "to_status": row["to_status"],
                "changed_by": row["changed_by"],
                "changed_at": row["changed_at"],
                "comment": row["comment"],
            }
            for row in history_rows
        ]
    return {
        "id": order["id"],
        "order_number": order["order_number"],
        "cart_id": order["cart_id"],
        "customer_name": order["customer_name"],
        "phone": order["phone"],
        "email": order["email"],
        "city": order["city"],
        "address": order["address"],
        "comment": order["comment"],
        "subtotal": float(order["subtotal"]),
        "delivery_cost": float(order["delivery_cost"]),
        "total": float(order["total"]),
        "status": order["status"],
        "created_at": order["created_at"],
        "updated_at": order["updated_at"],
        "items": [
            {
                "id": item["id"],
                "order_id": item["order_id"],
                "product_id": item["product_id"],
                "sku": item["sku"],
                "product_name": item["product_name"],
                "unit_price": float(item["unit_price"]),
                "qty": int(item["qty"]),
                "line_total": float(item["line_total"]),
            }
            for item in items
        ],
        "history": history,
    }


def generate_order_number(conn: sqlite3.Connection) -> str:
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"ORD-{date_part}-"
    count = conn.execute("SELECT COUNT(*) AS cnt FROM orders WHERE order_number LIKE ?", (f"{prefix}%",)).fetchone()["cnt"]
    return f"{prefix}{int(count) + 1:04d}"


def required_missing(data: dict, fields: list[str]) -> list[str]:
    return [field for field in fields if data.get(field) in (None, "")]


class OrderHandler(BaseHTTPRequestHandler):
    server_version = "order-service/1.0"

    def log_message(self, fmt: str, *args) -> None:
        print(f"[{now_iso()}] {self.address_string()} - {fmt % args}")

    def do_OPTIONS(self) -> None:
        json_response(self, 204, None)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)
        if path == "/health":
            return json_response(self, 200, {"status": "ok", "service": "order-service", "catalog_base_url": CATALOG_BASE_URL})
        match = re.fullmatch(r"/api/v1/carts/([^/]+)", path)
        if match:
            return self.handle_get_cart(match.group(1))
        if path == "/api/v1/orders":
            return self.handle_list_orders(query)
        match = re.fullmatch(r"/api/v1/orders/([^/]+)/history", path)
        if match:
            return self.handle_order_history(match.group(1))
        match = re.fullmatch(r"/api/v1/orders/([^/]+)", path)
        if match:
            return self.handle_get_order(match.group(1))
        return error_response(self, 404, "Маршрут не найден")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        match = re.fullmatch(r"/api/v1/carts/([^/]+)/items", path)
        if match:
            return self.handle_add_item(match.group(1))
        if path == "/api/v1/orders":
            return self.handle_create_order()
        return error_response(self, 404, "Маршрут не найден")

    def do_PATCH(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        match = re.fullmatch(r"/api/v1/carts/([^/]+)/items/([^/]+)", path)
        if match:
            return self.handle_patch_item(match.group(1), match.group(2))
        match = re.fullmatch(r"/api/v1/orders/([^/]+)/status", path)
        if match:
            return self.handle_change_status(match.group(1))
        return error_response(self, 404, "Маршрут не найден")

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        match = re.fullmatch(r"/api/v1/carts/([^/]+)/items/([^/]+)", path)
        if match:
            return self.handle_delete_item(match.group(1), match.group(2))
        return error_response(self, 404, "Маршрут не найден")

    def handle_get_cart(self, session_id: str) -> None:
        try:
            with connect() as conn:
                cart = get_or_create_active_cart(conn, session_id)
                update_cart_subtotal(conn, cart["id"])
                cart = conn.execute("SELECT * FROM carts WHERE id = ?", (cart["id"],)).fetchone()
                json_response(self, 200, cart_to_dict(conn, cart))
        except ServiceError as exc:
            error_response(self, exc.status, exc.message, exc.details)

    def handle_add_item(self, session_id: str) -> None:
        try:
            data = parse_body(self)
        except ValueError as exc:
            return error_response(self, 400, str(exc))
        product_id = data.get("product_id")
        qty = int(data.get("qty", 0) or 0)
        if not product_id or qty <= 0:
            return error_response(self, 400, "Нужно передать product_id и положительный qty")
        try:
            product = get_catalog_product(product_id)
            reserve_product(product_id, qty)
            with connect() as conn:
                cart = get_or_create_active_cart(conn, session_id)
                item = conn.execute("SELECT * FROM cart_items WHERE cart_id = ? AND product_id = ?", (cart["id"], product_id)).fetchone()
                unit_price = float(product["price"])
                if item:
                    new_qty = int(item["qty"]) + qty
                    conn.execute(
                        "UPDATE cart_items SET qty = ?, unit_price = ?, line_total = ? WHERE id = ?",
                        (new_qty, unit_price, round(unit_price * new_qty, 2), item["id"]),
                    )
                else:
                    item_id = DEMO_ITEM_ID if session_id == DEMO_SESSION_ID and product_id == DEMO_PRODUCT_ID else new_uuid()
                    conn.execute(
                        """
                        INSERT INTO cart_items (id, cart_id, product_id, sku, product_name, unit_price, qty, line_total)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            item_id,
                            cart["id"],
                            product_id,
                            product["sku"],
                            product["name"],
                            unit_price,
                            qty,
                            round(unit_price * qty, 2),
                        ),
                    )
                update_cart_subtotal(conn, cart["id"])
                cart = conn.execute("SELECT * FROM carts WHERE id = ?", (cart["id"],)).fetchone()
                json_response(self, 201, cart_to_dict(conn, cart))
        except sqlite3.IntegrityError as exc:
            try:
                release_product(product_id, qty)
            except ServiceError:
                pass
            error_response(self, 409, "Нарушение ограничения БД", {"sqlite": str(exc)})
        except ServiceError as exc:
            error_response(self, exc.status, exc.message, exc.details)

    def handle_patch_item(self, session_id: str, item_id: str) -> None:
        try:
            data = parse_body(self)
        except ValueError as exc:
            return error_response(self, 400, str(exc))
        new_qty = int(data.get("qty", 0) or 0)
        if new_qty < 0:
            return error_response(self, 400, "qty не может быть отрицательным")
        try:
            with connect() as conn:
                cart = conn.execute("SELECT * FROM carts WHERE session_id = ? AND status = 'ACTIVE'", (session_id,)).fetchone()
                if not cart:
                    return error_response(self, 404, "Активная корзина не найдена")
                item = conn.execute("SELECT * FROM cart_items WHERE id = ? AND cart_id = ?", (item_id, cart["id"])).fetchone()
                if not item:
                    return error_response(self, 404, "Позиция корзины не найдена")
                delta = new_qty - int(item["qty"])
                if delta > 0:
                    reserve_product(item["product_id"], delta)
                elif delta < 0:
                    release_product(item["product_id"], abs(delta))
                if new_qty == 0:
                    conn.execute("DELETE FROM cart_items WHERE id = ?", (item_id,))
                else:
                    line_total = round(float(item["unit_price"]) * new_qty, 2)
                    conn.execute("UPDATE cart_items SET qty = ?, line_total = ? WHERE id = ?", (new_qty, line_total, item_id))
                update_cart_subtotal(conn, cart["id"])
                cart = conn.execute("SELECT * FROM carts WHERE id = ?", (cart["id"],)).fetchone()
                json_response(self, 200, cart_to_dict(conn, cart))
        except ServiceError as exc:
            error_response(self, exc.status, exc.message, exc.details)

    def handle_delete_item(self, session_id: str, item_id: str) -> None:
        try:
            with connect() as conn:
                cart = conn.execute("SELECT * FROM carts WHERE session_id = ? AND status = 'ACTIVE'", (session_id,)).fetchone()
                if not cart:
                    return error_response(self, 404, "Активная корзина не найдена")
                item = conn.execute("SELECT * FROM cart_items WHERE id = ? AND cart_id = ?", (item_id, cart["id"])).fetchone()
                if not item:
                    return error_response(self, 404, "Позиция корзины не найдена")
                release_product(item["product_id"], int(item["qty"]))
                conn.execute("DELETE FROM cart_items WHERE id = ?", (item_id,))
                update_cart_subtotal(conn, cart["id"])
                json_response(self, 200, {"deleted": True, "item_id": item_id})
        except ServiceError as exc:
            error_response(self, exc.status, exc.message, exc.details)

    def handle_create_order(self) -> None:
        try:
            data = parse_body(self)
        except ValueError as exc:
            return error_response(self, 400, str(exc))
        missing = required_missing(data, ["session_id", "customer_name", "phone", "email", "city", "address"])
        if missing:
            return error_response(self, 400, "Не заполнены обязательные поля", {"missing": missing})
        try:
            with connect() as conn:
                cart = conn.execute("SELECT * FROM carts WHERE session_id = ? AND status = 'ACTIVE'", (data["session_id"],)).fetchone()
                if not cart:
                    return error_response(self, 404, "Активная корзина не найдена")
                items = conn.execute("SELECT * FROM cart_items WHERE cart_id = ?", (cart["id"],)).fetchall()
                if not items:
                    return error_response(self, 400, "Нельзя оформить пустую корзину")
                subtotal = update_cart_subtotal(conn, cart["id"])
                delivery_cost = float(data.get("delivery_cost", 0) or 0)
                total = round(subtotal + delivery_cost, 2)
                order_id = new_uuid()
                order_number = generate_order_number(conn)
                ts = now_iso()
                for item in items:
                    deduct_product(item["product_id"], int(item["qty"]))
                conn.execute(
                    """
                    INSERT INTO orders (
                        id, order_number, cart_id, customer_name, phone, email, city, address, comment,
                        subtotal, delivery_cost, total, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'NEW', ?, ?)
                    """,
                    (
                        order_id,
                        order_number,
                        cart["id"],
                        data["customer_name"],
                        data["phone"],
                        data["email"],
                        data["city"],
                        data["address"],
                        data.get("comment"),
                        subtotal,
                        delivery_cost,
                        total,
                        ts,
                        ts,
                    ),
                )
                for item in items:
                    conn.execute(
                        """
                        INSERT INTO order_items (id, order_id, product_id, sku, product_name, unit_price, qty, line_total)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            new_uuid(),
                            order_id,
                            item["product_id"],
                            item["sku"],
                            item["product_name"],
                            float(item["unit_price"]),
                            int(item["qty"]),
                            float(item["line_total"]),
                        ),
                    )
                conn.execute("UPDATE carts SET status = 'ORDERED', updated_at = ? WHERE id = ?", (ts, cart["id"]))
                conn.execute(
                    """
                    INSERT INTO order_status_history (id, order_id, from_status, to_status, changed_by, changed_at, comment)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (new_uuid(), order_id, None, "NEW", "order-service", ts, "Заказ создан"),
                )
                order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
                json_response(self, 201, order_to_dict(conn, order))
        except ServiceError as exc:
            error_response(self, exc.status, exc.message, exc.details)
        except sqlite3.IntegrityError as exc:
            error_response(self, 409, "Нарушение ограничения БД", {"sqlite": str(exc)})

    def handle_get_order(self, identifier: str) -> None:
        with connect() as conn:
            order = conn.execute("SELECT * FROM orders WHERE order_number = ? OR id = ?", (identifier, identifier)).fetchone()
            if not order:
                return error_response(self, 404, "Заказ не найден")
            json_response(self, 200, order_to_dict(conn, order))

    def handle_list_orders(self, query: dict) -> None:
        page = max(1, int(query.get("page", ["1"])[0] or 1))
        limit = min(100, max(1, int(query.get("limit", ["20"])[0] or 20)))
        filters = []
        params: list[object] = []
        if "status" in query and query["status"][0]:
            filters.append("status = ?")
            params.append(query["status"][0])
        where_sql = " WHERE " + " AND ".join(filters) if filters else ""
        offset = (page - 1) * limit
        with connect() as conn:
            total = conn.execute(f"SELECT COUNT(*) AS total FROM orders{where_sql}", params).fetchone()["total"]
            rows = conn.execute(
                f"SELECT * FROM orders{where_sql} ORDER BY created_at DESC, id LIMIT ? OFFSET ?",
                [*params, limit, offset],
            ).fetchall()
            items = [order_to_dict(conn, row, include_history=False) for row in rows]
        json_response(self, 200, {"items": items, "page": page, "limit": limit, "total": int(total)})

    def handle_order_history(self, identifier: str) -> None:
        with connect() as conn:
            order = conn.execute("SELECT * FROM orders WHERE order_number = ? OR id = ?", (identifier, identifier)).fetchone()
            if not order:
                return error_response(self, 404, "Заказ не найден")
            rows = conn.execute("SELECT * FROM order_status_history WHERE order_id = ? ORDER BY changed_at, id", (order["id"],)).fetchall()
            json_response(self, 200, {"items": [dict(row) for row in rows], "total": len(rows)})

    def handle_change_status(self, order_id: str) -> None:
        try:
            data = parse_body(self)
        except ValueError as exc:
            return error_response(self, 400, str(exc))
        status = data.get("status")
        if status not in ORDER_STATUSES:
            return error_response(self, 400, "Недопустимый статус заказа", {"allowed": sorted(ORDER_STATUSES)})
        with connect() as conn:
            order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
            if not order:
                return error_response(self, 404, "Заказ не найден")
            if order["status"] == status:
                return json_response(self, 200, order_to_dict(conn, order))
            ts = now_iso()
            conn.execute("UPDATE orders SET status = ?, updated_at = ? WHERE id = ?", (status, ts, order_id))
            conn.execute(
                """
                INSERT INTO order_status_history (id, order_id, from_status, to_status, changed_by, changed_at, comment)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_uuid(),
                    order_id,
                    order["status"],
                    status,
                    data.get("changed_by") or "admin",
                    ts,
                    data.get("comment"),
                ),
            )
            updated = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
            json_response(self, 200, order_to_dict(conn, updated))


def main() -> None:
    init_db()
    server = ThreadingHTTPServer((HOST, PORT), OrderHandler)
    print(f"order-service запущен: http://{HOST}:{PORT}")
    print(f"База данных: {os.path.abspath(DB_PATH)}")
    print(f"catalog-service: {CATALOG_BASE_URL}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nОстановка order-service")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
