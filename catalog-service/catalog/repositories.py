import sqlite3
from .utils import slugify


class ProductRepository:
    SORT_COLUMNS = {
        "name": "name",
        "price": "price",
        "created_at": "created_at",
        "stock_qty": "stock_qty",
    }

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def category_is_active(self, category_id: str) -> bool:
        row = self.conn.execute(
            "SELECT id FROM categories WHERE id = ? AND is_active = 1",
            (category_id,),
        ).fetchone()
        return row is not None

    def unique_slug(self, name: str, product_id: str | None = None) -> str:
        base = slugify(name)
        slug = base
        idx = 2
        while True:
            if product_id:
                row = self.conn.execute("SELECT id FROM products WHERE slug = ? AND id <> ?", (slug, product_id)).fetchone()
            else:
                row = self.conn.execute("SELECT id FROM products WHERE slug = ?", (slug,)).fetchone()
            if not row:
                return slug
            slug = f"{base}-{idx}"
            idx += 1

    def get_product_row(self, product_id: str) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()

    def list_products(self, filters: list[str], params: list[object], page: int, limit: int, sort_by: str, sort_order: str) -> dict:
        where_sql = " WHERE " + " AND ".join(filters) if filters else ""
        sort_col = self.SORT_COLUMNS.get(sort_by, "created_at")
        direction = "ASC" if sort_order == "asc" else "DESC"
        offset = (page - 1) * limit
        total = self.conn.execute(f"SELECT COUNT(*) AS total FROM products{where_sql}", params).fetchone()["total"]
        rows = self.conn.execute(
            f"SELECT * FROM products{where_sql} ORDER BY {sort_col} {direction}, id LIMIT ? OFFSET ?",
            [*params, limit, offset],
        ).fetchall()
        return {"rows": rows, "total": int(total)}

    def insert_product(self, payload: dict) -> None:
        self.conn.execute(
            """
            INSERT INTO products (
                id, sku, name, slug, description, category_id, price, currency,
                stock_qty, reserved_qty, socket_type, wattage, color_temperature,
                voltage, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["id"], payload["sku"], payload["name"], payload["slug"], payload.get("description"),
                payload["category_id"], payload["price"], payload["currency"], payload["stock_qty"],
                payload["reserved_qty"], payload["socket_type"], payload["wattage"], payload["color_temperature"],
                payload.get("voltage"), payload["status"], payload["created_at"], payload["updated_at"],
            ),
        )

    def replace_images(self, product_id: str, images: list[dict]) -> None:
        self.conn.execute("DELETE FROM product_images WHERE product_id = ?", (product_id,))
        self.add_images(product_id, images)

    def add_images(self, product_id: str, images: list[dict]) -> None:
        for image in images:
            self.conn.execute(
                """
                INSERT INTO product_images (id, product_id, url, alt_text, sort_order, is_primary)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    image["id"], product_id, image["url"], image.get("alt_text"),
                    image["sort_order"], 1 if image.get("is_primary") else 0,
                ),
            )

    def update_product(self, product_id: str, updates: dict) -> None:
        set_sql = ", ".join(f"{field} = ?" for field in updates.keys())
        self.conn.execute(f"UPDATE products SET {set_sql} WHERE id = ?", [*updates.values(), product_id])

    def product_to_dict(self, row: sqlite3.Row) -> dict:
        category = self.conn.execute(
            "SELECT id, code, name, is_active FROM categories WHERE id = ?",
            (row["category_id"],),
        ).fetchone()
        images = self.conn.execute(
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
            "images": [dict(img) | {"is_primary": bool(img["is_primary"])} for img in images],
        }
