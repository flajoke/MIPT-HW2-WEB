import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from .config import settings
from .errors import UpstreamError


class CatalogClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or settings.CATALOG_BASE_URL).rstrip("/")

    def request(self, method: str, path: str, body: dict | None = None) -> dict:
        url = f"{self.base_url}{path}"
        payload = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = Request(url, data=payload, headers={"Content-Type": "application/json"}, method=method)
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
            raise UpstreamError(exc.code, parsed.get("error", "Ошибка catalog-service"), parsed)
        except URLError as exc:
            raise UpstreamError(503, "catalog-service недоступен", {"url": url, "reason": str(exc.reason)})

    def get_product(self, product_id: str) -> dict:
        return self.request("GET", f"/api/v1/products/{quote(product_id)}")

    def reserve_product(self, product_id: str, qty: int) -> None:
        self.request("POST", f"/api/v1/products/{quote(product_id)}/reserve", {"qty": qty})

    def release_product(self, product_id: str, qty: int) -> None:
        self.request("POST", f"/api/v1/products/{quote(product_id)}/release", {"qty": qty})

    def deduct_product(self, product_id: str, qty: int) -> None:
        self.request("POST", f"/api/v1/products/{quote(product_id)}/deduct", {"qty": qty})
