import sqlite3
from .catalog_client import CatalogClient
from .database import connect
from .errors import ConflictError, NotFoundError, ValidationError
from .repositories import CartRepository, OrderRepository

ORDER_STATUSES = {"NEW", "CONFIRMED", "ASSEMBLING", "SHIPPED", "COMPLETED", "CANCELLED"}
ORDER_REQUIRED_FIELDS = ["session_id", "customer_name", "phone", "email", "city", "address"]


def require_fields(data: dict, fields: list[str]) -> None:
    missing = [field for field in fields if data.get(field) in (None, "")]
    if missing:
        raise ValidationError("Не заполнены обязательные поля", {"missing": missing})


def to_int(value: object, field: str, minimum: int | None = None) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field} должен быть целым числом")
    if minimum is not None and result < minimum:
        raise ValidationError(f"{field} должен быть не меньше {minimum}")
    return result


def to_float(value: object, field: str, minimum: float | None = None) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field} должен быть числом")
    if minimum is not None and result < minimum:
        raise ValidationError(f"{field} должен быть не меньше {minimum}")
    return result


class CartService:
    def __init__(self, catalog_client: CatalogClient | None = None):
        self.catalog = catalog_client or CatalogClient()

    def get_cart(self, session_id: str) -> dict:
        with connect() as conn:
            carts = CartRepository(conn)
            cart = carts.get_or_create_active(session_id)
            carts.update_subtotal(cart["id"])
            return carts.to_dict(carts.get_by_id(cart["id"]))

    def add_item(self, session_id: str, data: dict) -> dict:
        product_id = data.get("product_id")
        qty = to_int(data.get("qty", 0) or 0, "qty", 1)
        if not product_id:
            raise ValidationError("Нужно передать product_id и положительный qty")
        product = self.catalog.get_product(product_id)
        if product.get("status") != "ACTIVE":
            raise ConflictError("Товар не активен", {"product_id": product_id, "status": product.get("status")})
        self.catalog.reserve_product(product_id, qty)
        try:
            with connect() as conn:
                carts = CartRepository(conn)
                cart = carts.get_or_create_active(session_id)
                carts.add_or_increment_item(cart["id"], session_id, product, qty)
                carts.update_subtotal(cart["id"])
                return carts.to_dict(carts.get_by_id(cart["id"]))
        except sqlite3.IntegrityError as exc:
            try:
                self.catalog.release_product(product_id, qty)
            finally:
                raise ConflictError("Нарушение ограничения БД", {"sqlite": str(exc)})

    def update_item(self, session_id: str, item_id: str, data: dict) -> dict:
        new_qty = to_int(data.get("qty", 0) or 0, "qty", 0)
        with connect() as conn:
            carts = CartRepository(conn)
            cart = carts.get_active_by_session(session_id)
            if not cart:
                raise NotFoundError("Активная корзина не найдена")
            item = carts.get_item(cart["id"], item_id)
            if not item:
                raise NotFoundError("Позиция корзины не найдена")
            delta = new_qty - int(item["qty"])
            if delta > 0:
                self.catalog.reserve_product(item["product_id"], delta)
            elif delta < 0:
                self.catalog.release_product(item["product_id"], abs(delta))
            if new_qty == 0:
                carts.delete_item(item_id)
            else:
                carts.update_item_qty(item_id, new_qty, float(item["unit_price"]))
            carts.update_subtotal(cart["id"])
            return carts.to_dict(carts.get_by_id(cart["id"]))

    def delete_item(self, session_id: str, item_id: str) -> dict:
        with connect() as conn:
            carts = CartRepository(conn)
            cart = carts.get_active_by_session(session_id)
            if not cart:
                raise NotFoundError("Активная корзина не найдена")
            item = carts.get_item(cart["id"], item_id)
            if not item:
                raise NotFoundError("Позиция корзины не найдена")
            self.catalog.release_product(item["product_id"], int(item["qty"]))
            carts.delete_item(item_id)
            carts.update_subtotal(cart["id"])
            return {"deleted": True, "item_id": item_id}


class OrderService:
    def __init__(self, catalog_client: CatalogClient | None = None):
        self.catalog = catalog_client or CatalogClient()

    def create_order(self, data: dict) -> dict:
        require_fields(data, ORDER_REQUIRED_FIELDS)
        with connect() as conn:
            carts = CartRepository(conn)
            orders = OrderRepository(conn)
            cart = carts.get_active_by_session(data["session_id"])
            if not cart:
                raise NotFoundError("Активная корзина не найдена")
            items = carts.list_items(cart["id"])
            if not items:
                raise ValidationError("Нельзя оформить пустую корзину")
            subtotal = carts.update_subtotal(cart["id"])
            delivery_cost = to_float(data.get("delivery_cost", 0) or 0, "delivery_cost", 0)
            total = round(subtotal + delivery_cost, 2)
            for item in items:
                self.catalog.deduct_product(item["product_id"], int(item["qty"]))
            order_id = orders.create_order(cart["id"], data, subtotal, delivery_cost, total)
            orders.add_items_from_cart(order_id, items)
            carts.set_status(cart["id"], "ORDERED")
            orders.add_history(order_id, None, "NEW", "order-service", "Заказ создан")
            return orders.to_dict(orders.get_order(order_id))

    def get_order(self, identifier: str) -> dict:
        with connect() as conn:
            orders = OrderRepository(conn)
            order = orders.get_order(identifier)
            if not order:
                raise NotFoundError("Заказ не найден")
            return orders.to_dict(order)

    def list_orders(self, args: dict) -> dict:
        page = max(1, to_int(args.get("page", 1), "page", 1))
        limit = min(100, max(1, to_int(args.get("limit", 20), "limit", 1)))
        filters: list[str] = []
        params: list[object] = []
        if args.get("status"):
            if args["status"] not in ORDER_STATUSES:
                raise ValidationError("Недопустимый статус заказа", {"allowed": sorted(ORDER_STATUSES)})
            filters.append("status = ?")
            params.append(args["status"])
        with connect() as conn:
            orders = OrderRepository(conn)
            result = orders.list_orders(filters, params, page, limit)
            return {
                "items": [orders.to_dict(row, include_history=False) for row in result["rows"]],
                "page": page,
                "limit": limit,
                "total": result["total"],
            }

    def get_history(self, identifier: str) -> dict:
        with connect() as conn:
            orders = OrderRepository(conn)
            order = orders.get_order(identifier)
            if not order:
                raise NotFoundError("Заказ не найден")
            items = orders.history(order["id"])
            return {"items": items, "total": len(items)}

    def change_status(self, order_id: str, data: dict) -> dict:
        status = data.get("status")
        if status not in ORDER_STATUSES:
            raise ValidationError("Недопустимый статус заказа", {"allowed": sorted(ORDER_STATUSES)})
        with connect() as conn:
            orders = OrderRepository(conn)
            order = orders.get_order(order_id)
            if not order:
                raise NotFoundError("Заказ не найден")
            if order["status"] == status:
                return orders.to_dict(order)
            orders.change_status(order["id"], status)
            orders.add_history(order["id"], order["status"], status, data.get("changed_by") or "admin", data.get("comment"))
            return orders.to_dict(orders.get_order(order["id"]))
