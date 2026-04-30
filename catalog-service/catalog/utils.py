import re
import uuid
from datetime import datetime, timezone

TRANSLIT = str.maketrans({
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh", "з": "z",
    "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
    "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "c", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
})


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_uuid() -> str:
    return str(uuid.uuid4())


def slugify(value: str) -> str:
    raw = (value or "").lower().translate(TRANSLIT)
    raw = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")
    return raw or f"product-{uuid.uuid4().hex[:8]}"
