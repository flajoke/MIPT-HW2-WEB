from flask import Blueprint, jsonify, request
from .config import settings
from .errors import ValidationError
from .services import ProductService

bp = Blueprint("catalog", __name__)
service = ProductService()


def read_json() -> dict:
    if not request.data:
        return {}
    payload = request.get_json(silent=True)
    if payload is None or not isinstance(payload, dict):
        raise ValidationError("Тело запроса должно быть JSON-объектом")
    return payload


@bp.get("/health")
def health():
    return jsonify({"status": "ok", "service": settings.SERVICE_NAME})


@bp.get("/api/v1/products")
def list_products():
    return jsonify(service.list_products(request.args.to_dict()))


@bp.get("/api/v1/products/<product_id>")
def get_product(product_id: str):
    return jsonify(service.get_product(product_id))


@bp.post("/api/v1/products")
def create_product():
    payload = service.create_product(read_json())
    return jsonify(payload), 201


@bp.patch("/api/v1/products/<product_id>")
def update_product(product_id: str):
    return jsonify(service.update_product(product_id, read_json()))


@bp.post("/api/v1/products/<product_id>/archive")
def archive_product(product_id: str):
    return jsonify(service.archive_product(product_id))


@bp.post("/api/v1/products/<product_id>/<action>")
def stock_action(product_id: str, action: str):
    return jsonify(service.stock_action(product_id, action, read_json()))
