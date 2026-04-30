import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    DB_PATH: str = os.getenv("ORDER_DB_PATH", "order.sqlite3")
    HOST: str = os.getenv("ORDER_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("ORDER_PORT", "8082"))
    CATALOG_BASE_URL: str = os.getenv("CATALOG_BASE_URL", "http://localhost:8081").rstrip("/")
    SERVICE_NAME: str = "order-service"


settings = Settings()
