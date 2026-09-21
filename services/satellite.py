"""
satellite.py
Получение свежего снимка Sentinel-2 L2A через Microsoft Planetary Computer STAC.
Использует Cloud Optimized GeoTIFF (COG) + windowed read — скачивает только
нужный кусочек снимка (~200 КБ), а не весь архив (~800 МБ).
"""

import os
import shutil

# Ограничиваем потоки OpenBLAS для стабильности на Windows
os.environ["OPENBLAS_NUM_THREADS"] = "1"

# Настройка безопасного ASCII-пути для сертификатов curl на Windows (обход кириллицы в C:\Users\...)
import certifi
_temp_ca = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "Temp", "cacert.pem")
try:
    if not os.path.exists(_temp_ca):
        shutil.copy(certifi.where(), _temp_ca)
except Exception:
    _temp_ca = certifi.where()

os.environ["CURL_CA_BUNDLE"] = _temp_ca
os.environ["GDAL_CA_BUNDLE"] = _temp_ca
os.environ["GDAL_HTTP_UNSAFESSL"] = "YES"

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

import numpy as np
import planetary_computer
import pystac_client
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds

from config import (
    BBOX_DELTA,
    MAX_CLOUD_COVER,
    PIXEL_SIZE,
    STAC_COLLECTION,
    STAC_URL,
)

logger = logging.getLogger(__name__)


def _build_bbox(
    lat: float, lon: float, delta: float = BBOX_DELTA
) -> Tuple[float, float, float, float]:
    """Строит bbox (minx, miny, maxx, maxy) в WGS84 вокруг точки с учётом масштаба."""
    return (
        lon - delta,
        lat - delta,
        lon + delta,
        lat + delta,
    )


def _fetch_bands_sync(
    signed_item,
    bbox_4326: Tuple[float, float, float, float],
) -> Optional[Tuple[np.ndarray, np.ndarray, np.ndarray, str]]:
    """
    Синхронное чтение каналов B04, B08, B11 через rasterio windowed read.
    Возвращает (b04, b08, b11, date_str) или None при ошибке.
    """
    band_names = {"B04": None, "B08": None, "B11": None}

    # Настройки GDAL для быстрого чтения по HTTPS и обхода проблем с SSL/путями
    env_options = {
        "CURL_CA_BUNDLE": _temp_ca,
        "GDAL_CA_BUNDLE": _temp_ca,
        "GDAL_HTTP_UNSAFESSL": "YES",
        "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
        "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif,.tiff,.xml",
    }

    with rasterio.Env(**env_options):
        for band_key in band_names:
            try:
                href = signed_item.assets[band_key].href
                with rasterio.open(href) as src:
                    # Преобразуем координаты bbox из WGS84 (градусы) в систему координат снимка (метры UTM)
                    proj_bounds = transform_bounds(
                        "EPSG:4326", src.crs,
                        bbox_4326[0], bbox_4326[1], bbox_4326[2], bbox_4326[3]
                    )

                    # Вычисляем пиксельное окно
                    window = from_bounds(*proj_bounds, transform=src.transform)

                    # Читаем только нужные пиксели и масштабируем до PIXEL_SIZE x PIXEL_SIZE
                    data = src.read(
                        1,
                        window=window,
                        out_shape=(PIXEL_SIZE, PIXEL_SIZE),
                        resampling=Resampling.bilinear,
                    )
                    band_names[band_key] = data.astype(np.float32)
            except Exception as exc:
                logger.error("Ошибка чтения канала %s: %s", band_key, exc)
                return None

    date_str = signed_item.datetime.strftime("%Y-%m-%d") if signed_item.datetime else "Неизвестно"
    return band_names["B04"], band_names["B08"], band_names["B11"], date_str


async def fetch_sentinel2(
    lat: float,
    lon: float,
    delta: float = BBOX_DELTA,
) -> Optional[Tuple[np.ndarray, np.ndarray, np.ndarray, str]]:
    """
    Асинхронная обёртка: ищет самый свежий снимок Sentinel-2 L2A
    без лишней облачности и возвращает массивы каналов B04, B08, B11.

    Args:
        lat: Широта.
        lon: Долгота.
        delta: Полуразмер окна в градусах (масштаб поля).

    Returns:
        (b04, b08, b11, date_str) или None если снимок не найден.
    """
    bbox = _build_bbox(lat, lon, delta=delta)
    date_end = datetime.utcnow()
    date_start = date_end - timedelta(days=90)  # ищем за последние 90 дней для надёжности
    date_range = f"{date_start.strftime('%Y-%m-%dT%H:%M:%SZ')}/{date_end.strftime('%Y-%m-%dT%H:%M:%SZ')}"

    try:
        catalog = pystac_client.Client.open(
            STAC_URL,
            modifier=planetary_computer.sign_inplace,
        )

        search = catalog.search(
            collections=[STAC_COLLECTION],
            bbox=bbox,
            datetime=date_range,
            query={"eo:cloud_cover": {"lt": MAX_CLOUD_COVER}},
            sortby=["-datetime"],  # сначала самый свежий
            max_items=5,
        )

        items = list(search.items())

        # Если снимков с облачностью < 20% нет, пробуем до 40% (лучше снимок с небольшим облаком, чем ничего)
        if not items:
            search_fallback = catalog.search(
                collections=[STAC_COLLECTION],
                bbox=bbox,
                datetime=date_range,
                query={"eo:cloud_cover": {"lt": 40}},
                sortby=["-datetime"],
                max_items=3,
            )
            items = list(search_fallback.items())

        if not items:
            logger.warning(
                "Снимок не найден для координат (%.4f, %.4f) за 90 дней.", lat, lon
            )
            return None

        # Берём первый подходящий снимок и подписываем SAS-токен
        best_item = items[0]
        signed_item = planetary_computer.sign(best_item)

        logger.info(
            "Найден снимок: %s, облачность: %.1f%%",
            signed_item.datetime,
            signed_item.properties.get("eo:cloud_cover", -1),
        )

        # Читаем каналы в отдельном потоке
        result = await asyncio.get_event_loop().run_in_executor(
            None, _fetch_bands_sync, signed_item, bbox
        )
        return result

    except Exception as exc:
        logger.exception("Ошибка при поиске/загрузке Sentinel-2: %s", exc)
        return None
