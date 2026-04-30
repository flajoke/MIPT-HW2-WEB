import logging
import sqlite3
import time
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException
from .database import init_db
from .errors import AppError
from .handlers import bp


def create_app() -> Flask:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    app = Flask(__name__)
    init_db()
    app.register_blueprint(bp)

    @app.before_request
    def start_timer():
        request._started_at = time.perf_counter()

    @app.after_request
    def after_request(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        elapsed_ms = (time.perf_counter() - getattr(request, "_started_at", time.perf_counter())) * 1000
        app.logger.info("%s %s -> %s %.1fms", request.method, request.path, response.status_code, elapsed_ms)
        return response

    @app.errorhandler(AppError)
    def handle_app_error(exc: AppError):
        payload = {"error": exc.message}
        if exc.details:
            payload["details"] = exc.details
        return jsonify(payload), exc.status

    @app.errorhandler(sqlite3.IntegrityError)
    def handle_integrity_error(exc: sqlite3.IntegrityError):
        return jsonify({"error": "Нарушение ограничения БД", "details": {"sqlite": str(exc)}}), 409

    @app.errorhandler(HTTPException)
    def handle_http_error(exc: HTTPException):
        return jsonify({"error": exc.description or "HTTP error"}), exc.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc: Exception):
        app.logger.exception("Unexpected order-service error")
        return jsonify({"error": "Внутренняя ошибка сервиса"}), 500

    return app
