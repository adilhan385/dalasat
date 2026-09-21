import os
from dotenv import load_dotenv

load_dotenv()

# ─── Telegram ───────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

# ─── Gemini AI ──────────────────────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = "gemini-3.5-flash-lite"

# ─── Sentinel-2 параметры ───────────────────────────────────────────────────
# Размер окна вокруг точки (в градусах). 0.007 ≈ 0.78 км, итого ~1.5x1.5 км
BBOX_DELTA: float = 0.007

# Варианты масштабирования поля
SCALE_PROFILES = {
    "small": {
        "label_ru": "🔍 Детальный (1×1 км, ~100 га)",
        "label_kz": "🔍 Егжей-тегжейлі (1×1 км, ~100 га)",
        "delta": 0.005,
    },
    "medium": {
        "label_ru": "🌾 Стандартный (2×2 км, ~400 га)",
        "label_kz": "🌾 Стандартты (2×2 км, ~400 га)",
        "delta": 0.010,
    },
    "large": {
        "label_ru": "🛰 Массив полей (4×4 км, ~1600 га)",
        "label_kz": "🛰 Алқаптар массиві (4×4 км, ~1600 га)",
        "delta": 0.020,
    },
}
DEFAULT_SCALE = "medium"

# Максимальный % облачности снимка
MAX_CLOUD_COVER: int = 20

# Размер итогового массива в пикселях (downscale для скорости)
PIXEL_SIZE: int = 256

# ─── NDVI пороги классификации ──────────────────────────────────────────────
NDVI_STRESSED_THRESHOLD: float = 0.25   # ниже этого — проблемная зона
NDVI_MODERATE_THRESHOLD: float = 0.45   # ниже этого — удовлетворительно

# ─── STAC API ───────────────────────────────────────────────────────────────
STAC_URL: str = "https://planetarycomputer.microsoft.com/api/stac/v1"
STAC_COLLECTION: str = "sentinel-2-l2a"
