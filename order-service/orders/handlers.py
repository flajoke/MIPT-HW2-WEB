from flask import Blueprint, jsonify, request
from .config import settings
from .errors import ValidationError
from .services import CartService, OrderService

bp = Blueprint("orders", __name__)
cart_service = CartService()
order_service = OrderService()


def read_json() -> dict:
    if not request.data:
        return {}
    payload = request.get_json(silent=True)
    if payload is None or not isinstance(payload, dict):
        raise ValidationError("Тело запроса должно быть JSON-объектом")
    return payload


@bp.get("/health")
def health():
    return jsonify({"status": "ok", "service": settings.SERVICE_NAME, "catalog_base_url": settings.CATALOG_BASE_URL})


@bp.get("/api/v1/carts/<session_id>")
def get_cart(session_id: str):
    return jsonify(cart_service.get_cart(session_id))


@bp.post("/api/v1/carts/<session_id>/items")
def add_item(session_id: str):
    payload = cart_service.add_item(session_id, read_json())
    return jsonify(payload), 201


@bp.patch("/api/v1/carts/<session_id>/items/<item_id>")
def update_item(session_id: str, item_id: str):
    return jsonify(cart_service.update_item(session_id, item_id, read_json()))


@bp.delete("/api/v1/carts/<session_id>/items/<item_id>")
def delete_item(session_id: str, item_id: str):
    return jsonify(cart_service.delete_item(session_id, item_id))


@bp.get("/api/v1/orders")
def list_orders():
    return jsonify(order_service.list_orders(request.args.to_dict()))


@bp.post("/api/v1/orders")
def create_order():
    payload = order_service.create_order(read_json())
    return jsonify(payload), 201


@bp.get("/api/v1/orders/<identifier>/history")
def order_history(identifier: str):
    return jsonify(order_service.get_history(identifier))


@bp.get("/api/v1/orders/<identifier>")
def get_order(identifier: str):
    return jsonify(order_service.get_order(identifier))


@bp.patch("/api/v1/orders/<order_id>/status")
def change_status(order_id: str):
    return jsonify(order_service.change_status(order_id, read_json()))
