import sqlite3
from datetime import datetime, timezone
from .database import DEMO_ITEM_ID, DEMO_PRODUCT_ID, DEMO_SESSION_ID
from .utils import new_uuid, now_iso


class CartRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get_active_by_session(self, session_id: str) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM carts WHERE session_id = ? AND status = 'ACTIVE'", (session_id,)).fetchone()

    def get_any_by_session(self, session_id: str) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM carts WHERE session_id = ?", (session_id,)).fetchone()

    def get_or_create_active(self, session_id: str) -> sqlite3.Row:
        cart = self.get_active_by_session(session_id)
        if cart:
            return cart
        ts = now_iso()
        cart_id = "10000000-0000-0000-0000-000000000002" if session_id == DEMO_SESSION_ID else new_uuid()
        self.conn.execute(
            "INSERT INTO carts (id, session_id, status, subtotal, created_at, updated_at) VALUES (?, ?, 'ACTIVE', 0, ?, ?)",
            (cart_id, session_id, ts, ts),
        )
        return self.get_by_id(cart_id)

    def get_by_id(self, cart_id: str) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM carts WHERE id = ?", (cart_id,)).fetchone()

    def get_item(self, cart_id: str, item_id: str) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM cart_items WHERE id = ? AND cart_id = ?", (item_id, cart_id)).fetchone()

    def get_item_by_product(self, cart_id: str, product_id: str) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM cart_items WHERE cart_id = ? AND product_id = ?", (cart_id, product_id)).fetchone()

    def list_items(self, cart_id: str) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM cart_items WHERE cart_id = ? ORDER BY product_name, id", (cart_id,)).fetchall()

    def add_or_increment_item(self, cart_id: str, session_id: str, product: dict, qty: int) -> None:
        item = self.get_item_by_product(cart_id, product["id"])
        unit_price = float(product["price"])
        if item:
            new_qty = int(item["qty"]) + qty
            self.conn.execute(
                "UPDATE cart_items SET qty = ?, unit_price = ?, line_total = ? WHERE id = ?",
                (new_qty, unit_price, round(unit_price * new_qty, 2), item["id"]),
            )
            return
        item_id = DEMO_ITEM_ID if session_id == DEMO_SESSION_ID and product["id"] == DEMO_PRODUCT_ID else new_uuid()
        self.conn.execute(
            """
            INSERT INTO cart_items (id, cart_id, product_id, sku, product_name, unit_price, qty, line_total)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (item_id, cart_id, product["id"], product["sku"], product["name"], unit_price, qty, round(unit_price * qty, 2)),
        )

    def update_item_qty(self, item_id: str, qty: int, unit_price: float) -> None:
        self.conn.execute(
            "UPDATE cart_items SET qty = ?, line_total = ? WHERE id = ?",
            (qty, round(unit_price * qty, 2), item_id),
        )

    def delete_item(self, item_id: str) -> None:
        self.conn.execute("DELETE FROM cart_items WHERE id = ?", (item_id,))

    def set_status(self, cart_id: str, status: str) -> None:
        self.conn.execute("UPDATE carts SET status = ?, updated_at = ? WHERE id = ?", (status, now_iso(), cart_id))

    def update_subtotal(self, cart_id: str) -> float:
        subtotal = self.conn.execute(
            "SELECT COALESCE(SUM(line_total), 0) AS subtotal FROM cart_items WHERE cart_id = ?",
            (cart_id,),
        ).fetchone()["subtotal"]
        subtotal = float(subtotal or 0)
        self.conn.execute("UPDATE carts SET subtotal = ?, updated_at = ? WHERE id = ?", (subtotal, now_iso(), cart_id))
        return subtotal

    def to_dict(self, cart: sqlite3.Row) -> dict:
        items = self.list_items(cart["id"])
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


class OrderRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def generate_order_number(self) -> str:
        date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
        prefix = f"ORD-{date_part}-"
        count = self.conn.execute(
            "SELECT COUNT(*) AS cnt FROM orders WHERE order_number LIKE ?",
            (f"{prefix}%",),
        ).fetchone()["cnt"]
        return f"{prefix}{int(count) + 1:04d}"

    def create_order(self, cart_id: str, data: dict, subtotal: float, delivery_cost: float, total: float) -> str:
        order_id = new_uuid()
        order_number = self.generate_order_number()
        ts = now_iso()
        self.conn.execute(
            """
            INSERT INTO orders (
                id, order_number, cart_id, customer_name, phone, email, city, address, comment,
                subtotal, delivery_cost, total, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'NEW', ?, ?)
            """,
            (
                order_id,
                order_number,
                cart_id,
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
        return order_id

    def add_items_from_cart(self, order_id: str, cart_items: list[sqlite3.Row]) -> None:
        for item in cart_items:
            self.conn.execute(
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

    def add_history(self, order_id: str, from_status: str | None, to_status: str, changed_by: str, comment: str | None = None) -> None:
        self.conn.execute(
            """
            INSERT INTO order_status_history (id, order_id, from_status, to_status, changed_by, changed_at, comment)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (new_uuid(), order_id, from_status, to_status, changed_by, now_iso(), comment),
        )

    def get_order(self, identifier: str) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM orders WHERE order_number = ? OR id = ?", (identifier, identifier)).fetchone()

    def list_orders(self, filters: list[str], params: list[object], page: int, limit: int) -> dict:
        where_sql = " WHERE " + " AND ".join(filters) if filters else ""
        offset = (page - 1) * limit
        total = self.conn.execute(f"SELECT COUNT(*) AS total FROM orders{where_sql}", params).fetchone()["total"]
        rows = self.conn.execute(
            f"SELECT * FROM orders{where_sql} ORDER BY created_at DESC, id LIMIT ? OFFSET ?",
            [*params, limit, offset],
        ).fetchall()
        return {"rows": rows, "total": int(total)}

    def change_status(self, order_id: str, status: str) -> None:
        self.conn.execute("UPDATE orders SET status = ?, updated_at = ? WHERE id = ?", (status, now_iso(), order_id))

    def history(self, order_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM order_status_history WHERE order_id = ? ORDER BY changed_at, id",
            (order_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def to_dict(self, order: sqlite3.Row, include_history: bool = True) -> dict:
        items = self.conn.execute("SELECT * FROM order_items WHERE order_id = ? ORDER BY product_name, id", (order["id"],)).fetchall()
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
            "history": self.history(order["id"]) if include_history else [],
        }
