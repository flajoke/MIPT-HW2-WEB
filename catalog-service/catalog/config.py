import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    DB_PATH: str = os.getenv("CATALOG_DB_PATH", "catalog.sqlite3")
    HOST: str = os.getenv("CATALOG_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("CATALOG_PORT", "8081"))
    SERVICE_NAME: str = "catalog-service"


settings = Settings()
