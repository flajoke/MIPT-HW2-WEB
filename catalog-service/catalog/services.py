import sqlite3
from .database import connect
from .errors import ConflictError, NotFoundError, ValidationError
from .repositories import ProductRepository
from .utils import new_uuid, now_iso

VALID_STATUSES = {"ACTIVE", "ARCHIVED", "OUT_OF_STOCK"}
PRODUCT_REQUIRED_FIELDS = ["sku", "name", "category_id", "price", "stock_qty", "socket_type", "wattage", "color_temperature"]
PATCH_ALLOWED_FIELDS = {
    "sku", "name", "description", "category_id", "price", "currency", "stock_qty",
    "reserved_qty", "socket_type", "wattage", "color_temperature", "voltage", "status",
}


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


def normalize_status_from_stock(status: str, stock_qty: int, reserved_qty: int) -> str:
    if status == "ARCHIVED":
        return status
    if stock_qty - reserved_qty <= 0:
        return "OUT_OF_STOCK"
    return status if status in VALID_STATUSES else "ACTIVE"


def normalize_images(images: list[dict] | None) -> list[dict]:
    normalized = []
    for idx, image in enumerate(images or [], start=1):
        if not isinstance(image, dict) or not image.get("url"):
            raise ValidationError("Каждое изображение должно содержать url")
        normalized.append(
            {
                "id": image.get("id") or new_uuid(),
                "url": image["url"],
                "alt_text": image.get("alt_text"),
                "sort_order": to_int(image.get("sort_order", idx), "images.sort_order", 0),
                "is_primary": bool(image.get("is_primary", idx == 1)),
            }
        )
    return normalized


class ProductService:
    def list_products(self, args: dict) -> dict:
        page = max(1, to_int(args.get("page", 1), "page", 1))
        limit = min(100, max(1, to_int(args.get("limit", 20), "limit", 1)))
        filters: list[str] = []
        params: list[object] = []
        for field in ["status", "category_id", "socket_type", "wattage", "color_temperature"]:
            value = args.get(field)
            if value not in (None, ""):
                filters.append(f"{field} = ?")
                params.append(value)
        if args.get("price_min") not in (None, ""):
            filters.append("price >= ?")
            params.append(to_float(args.get("price_min"), "price_min", 0))
        if args.get("price_max") not in (None, ""):
            filters.append("price <= ?")
            params.append(to_float(args.get("price_max"), "price_max", 0))
        if args.get("q"):
            filters.append("(LOWER(name) LIKE ? OR LOWER(sku) LIKE ?)")
            value = f"%{str(args['q']).strip().lower()}%"
            params.extend([value, value])
        sort_by = str(args.get("sort_by") or "created_at")
        sort_order = str(args.get("sort_order") or "desc").lower()
        with connect() as conn:
            repo = ProductRepository(conn)
            result = repo.list_products(filters, params, page, limit, sort_by, sort_order)
            return {
                "items": [repo.product_to_dict(row) for row in result["rows"]],
                "page": page,
                "limit": limit,
                "total": result["total"],
            }

    def get_product(self, product_id: str) -> dict:
        with connect() as conn:
            repo = ProductRepository(conn)
            row = repo.get_product_row(product_id)
            if not row:
                raise NotFoundError("Товар не найден")
            return repo.product_to_dict(row)

    def create_product(self, data: dict) -> dict:
        require_fields(data, PRODUCT_REQUIRED_FIELDS)
        status = data.get("status", "ACTIVE")
        if status not in VALID_STATUSES:
            raise ValidationError("Недопустимый статус товара", {"allowed": sorted(VALID_STATUSES)})
        stock_qty = to_int(data["stock_qty"], "stock_qty", 0)
        reserved_qty = to_int(data.get("reserved_qty", 0) or 0, "reserved_qty", 0)
        payload = {
            "id": data.get("id") or new_uuid(),
            "sku": data["sku"],
            "name": data["name"],
            "description": data.get("description"),
            "category_id": data["category_id"],
            "price": to_float(data["price"], "price", 0),
            "currency": data.get("currency", "RUB"),
            "stock_qty": stock_qty,
            "reserved_qty": reserved_qty,
            "socket_type": data["socket_type"],
            "wattage": to_int(data["wattage"], "wattage", 1),
            "color_temperature": to_int(data["color_temperature"], "color_temperature", 1),
            "voltage": None if data.get("voltage") in (None, "") else to_int(data.get("voltage"), "voltage", 0),
            "status": normalize_status_from_stock(status, stock_qty, reserved_qty),
        }
        images = normalize_images(data.get("images"))
        ts = now_iso()
        payload.update({"created_at": ts, "updated_at": ts})
        with connect() as conn:
            repo = ProductRepository(conn)
            if not repo.category_is_active(payload["category_id"]):
                raise NotFoundError("Категория не найдена или неактивна")
            payload["slug"] = repo.unique_slug(payload["name"])
            try:
                repo.insert_product(payload)
                repo.add_images(payload["id"], images)
            except sqlite3.IntegrityError as exc:
                raise ConflictError("Товар с таким id, sku или slug уже существует", {"sqlite": str(exc)})
            return repo.product_to_dict(repo.get_product_row(payload["id"]))

    def update_product(self, product_id: str, data: dict) -> dict:
        updates = {key: value for key, value in data.items() if key in PATCH_ALLOWED_FIELDS}
        if not updates:
            raise ValidationError("Нет полей для обновления")
        if "status" in updates and updates["status"] not in VALID_STATUSES:
            raise ValidationError("Недопустимый статус товара", {"allowed": sorted(VALID_STATUSES)})
        with connect() as conn:
            repo = ProductRepository(conn)
            current = repo.get_product_row(product_id)
            if not current:
                raise NotFoundError("Товар не найден")
            if "category_id" in updates and not repo.category_is_active(str(updates["category_id"])):
                raise NotFoundError("Категория не найдена или неактивна")
            if "name" in updates:
                updates["slug"] = repo.unique_slug(str(updates["name"]), product_id)
            if "price" in updates:
                updates["price"] = to_float(updates["price"], "price", 0)
            for field in ["stock_qty", "reserved_qty", "wattage", "color_temperature", "voltage"]:
                if field in updates and updates[field] not in (None, ""):
                    updates[field] = to_int(updates[field], field, 0 if field != "wattage" and field != "color_temperature" else 1)
            updates["updated_at"] = now_iso()
            try:
                repo.update_product(product_id, updates)
            except sqlite3.IntegrityError as exc:
                raise ConflictError("Нарушение уникальности или ограничения БД", {"sqlite": str(exc)})
            return repo.product_to_dict(repo.get_product_row(product_id))

    def archive_product(self, product_id: str) -> dict:
        with connect() as conn:
            repo = ProductRepository(conn)
            if not repo.get_product_row(product_id):
                raise NotFoundError("Товар не найден")
            repo.update_product(product_id, {"status": "ARCHIVED", "updated_at": now_iso()})
            return repo.product_to_dict(repo.get_product_row(product_id))

    def stock_action(self, product_id: str, action: str, data: dict) -> dict:
        qty = to_int(data.get("qty", 0) or 0, "qty", 1)
        if action not in {"reserve", "release", "deduct"}:
            raise NotFoundError("Операция не найдена")
        with connect() as conn:
            repo = ProductRepository(conn)
            row = repo.get_product_row(product_id)
            if not row:
                raise NotFoundError("Товар не найден")
            stock = int(row["stock_qty"])
            reserved = int(row["reserved_qty"])
            if action == "reserve":
                if row["status"] != "ACTIVE":
                    raise ConflictError("Нельзя резервировать неактивный товар")
                if stock - reserved < qty:
                    raise ConflictError("Недостаточно товара на складе", {"available_qty": stock - reserved})
                reserved += qty
            elif action == "release":
                reserved = max(0, reserved - qty)
            elif action == "deduct":
                if stock < qty:
                    raise ConflictError("Недостаточно остатка для списания", {"stock_qty": stock})
                stock -= qty
                reserved = max(0, reserved - qty)
            status = row["status"]
            if status != "ARCHIVED":
                status = "OUT_OF_STOCK" if stock - reserved <= 0 else "ACTIVE"
            repo.update_product(product_id, {"stock_qty": stock, "reserved_qty": reserved, "status": status, "updated_at": now_iso()})
            return repo.product_to_dict(repo.get_product_row(product_id))
