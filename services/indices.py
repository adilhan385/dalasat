"""
indices.py
Расчёт вегетационных индексов NDVI и NDMI из каналов Sentinel-2.
"""

from collections import deque
from typing import Dict, Tuple

import numpy as np

from config import NDVI_MODERATE_THRESHOLD, NDVI_STRESSED_THRESHOLD



def _detect_buildings(
    b04: np.ndarray,
    b08: np.ndarray,
    b11: np.ndarray,
    ndvi: np.ndarray,
) -> Tuple[bool, int, str, str, str]:
    """
    Детекция построек и сооружений (NDBI, Urban Index, морфологический анализ связности).
    Возвращает (has_buildings: bool, count: int, status_ru: str, status_kz: str, emoji: str).
    """
    # NDBI = (SWIR - NIR) / (SWIR + NIR)
    ndbi = (b11 - b08) / (b11 + b08 + 1e-6)

    # Критерии строений/сооружений:
    # 1. Положительный NDBI (характерно для крыш, бетона, металла, шифера, асфальта)
    # 2. Низкий NDVI (на крышах и складах нет растительности)
    # 3. Высокая отражательная способность в SWIR и видимом спектре
    # 4. Исключение чистой воды/теней
    building_mask = (ndbi > 0.08) & (ndvi < 0.20) & (b11 > 0.12) & (b04 > 0.08)

    num_pixels = int(np.sum(building_mask))
    if num_pixels < 2:
        return False, 0, "Построек не обнаружено (чистое поле)", "Құрылыстар байқалмады (таза егістік)", "🌾"

    # Поиск связных областей (Connected Components) через BFS
    h, w = building_mask.shape
    visited = np.zeros((h, w), dtype=bool)
    clusters = []

    for r in range(h):
        for c in range(w):
            if building_mask[r, c] and not visited[r, c]:
                q = deque([(r, c)])
                visited[r, c] = True
                cluster_size = 0
                while q:
                    cr, cc = q.popleft()
                    cluster_size += 1
                    # 8-связность
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < h and 0 <= nc < w and building_mask[nr, nc] and not visited[nr, nc]:
                            visited[nr, nc] = True
                            q.append((nr, nc))

                # Фильтрация шумов: одиночный пиксель (10х10 м) может быть шумом или камнем
                if cluster_size >= 2:
                    clusters.append(cluster_size)

    if not clusters:
        return False, 0, "Построек не обнаружено (чистое поле)", "Құрылыстар байқалмады (таза егістік)", "🌾"

    # Оценка числа строений:
    # Сельхоз постройка (ангар, коровник, склад, дом) занимает 2..25 пикселей (200..2500 м²).
    # Большие связные кластеры (>30 пикселей) делятся на блоки зданий.
    building_count = 0
    for sz in clusters:
        if sz <= 30:
            building_count += 1
        elif sz <= 100:
            building_count += max(2, sz // 25)
        else:
            # Крупный промышленный комплекс / ток / элеватор
            building_count += max(4, sz // 30)

    if building_count == 0:
        status_ru = "Построек не обнаружено (чистое поле)"
        status_kz = "Құрылыстар байқалмады (таза егістік)"
        emoji = "🌾"
        has_b = False
    elif building_count <= 3:
        status_ru = f"~{building_count} ед. (единичные строения/стан)"
        status_kz = f"~{building_count} нысан (жеке құрылыстар/қора)"
        emoji = "🏠"
        has_b = True
    elif building_count <= 10:
        status_ru = f"~{building_count} ед. (хозпостройки/склады/ферма)"
        status_kz = f"~{building_count} нысан (шаруашылық қоймалары/база)"
        emoji = "🏛"
        has_b = True
    else:
        status_ru = f"~{building_count}+ ед. (агрокомплекс/элеватор/застройка)"
        status_kz = f"~{building_count}+ нысан (агрокешен/элеватор/құрылыс кешені)"
        emoji = "🏭"
        has_b = True

    return has_b, building_count, status_ru, status_kz, emoji


def calculate_indices(
    b04: np.ndarray,
    b08: np.ndarray,
    b11: np.ndarray,
) -> Dict:
    """
    Рассчитывает NDVI и NDMI и возвращает статистику по полю.

    Args:
        b04: Красный канал Sentinel-2 (Red, ~665 нм).
        b08: Ближний инфракрасный канал (NIR, ~842 нм).
        b11: Коротковолновый инфракрасный канал (SWIR, ~1610 нм).

    Returns:
        Словарь со статистикой:
            - ndvi_array: numpy массив NDVI для визуализации
            - ndmi_array: numpy массив NDMI
            - mean_ndvi: среднее значение NDVI
            - min_ndvi: минимальное значение NDVI
            - max_ndvi: максимальное значение NDVI
            - mean_ndmi: среднее значение NDMI
            - stressed_percent: % депрессивных зон (NDVI < порог)
            - moderate_percent: % удовлетворительных зон
            - healthy_percent: % здоровой вегетации
    """
    # Нормализуем диапазон значений (Sentinel-2 L2A отдаёт uint16 0-10000)
    b04 = b04 / 10000.0
    b08 = b08 / 10000.0
    b11 = b11 / 10000.0

    # NDVI = (NIR - Red) / (NIR + Red)
    ndvi = (b08 - b04) / (b08 + b04 + 1e-6)

    # NDMI = (NIR - SWIR) / (NIR + SWIR)
    ndmi = (b08 - b11) / (b08 + b11 + 1e-6)

    # Обрезка шумов до физически разумного диапазона
    ndvi = np.clip(ndvi, -1.0, 1.0)
    ndmi = np.clip(ndmi, -1.0, 1.0)

    # Маскируем пиксели без данных (где все каналы близки к 0 — вода/тень)
    valid_mask = (b04 + b08) > 0.02
    ndvi_valid = ndvi[valid_mask]
    ndmi_valid = ndmi[valid_mask]

    if ndvi_valid.size == 0:
        # Нет валидных пикселей (всё покрыто облаками или водой)
        return {
            "ndvi_array": ndvi,
            "ndmi_array": ndmi,
            "mean_ndvi": 0.0,
            "min_ndvi": 0.0,
            "max_ndvi": 0.0,
            "mean_ndmi": 0.0,
            "stressed_percent": 0.0,
            "moderate_percent": 0.0,
            "healthy_percent": 0.0,
            "soil_score": 0,
            "soil_status_ru": "Нет данных",
            "soil_status_kz": "Деректер жоқ",
            "soil_emoji": "⚪",
            "has_buildings": False,
            "building_count": 0,
            "building_status_ru": "Нет данных",
            "building_status_kz": "Деректер жоқ",
            "building_emoji": "⚪",
        }

    # Детекция построек и сооружений
    has_b, b_count, b_status_ru, b_status_kz, b_emoji = _detect_buildings(b04, b08, b11, ndvi)

    # Статистика NDVI
    mean_ndvi = float(np.mean(ndvi_valid))
    min_ndvi = float(np.min(ndvi_valid))
    max_ndvi = float(np.max(ndvi_valid))
    mean_ndmi = float(np.mean(ndmi_valid))

    # Классификация пикселей
    total = float(ndvi_valid.size)
    stressed_count = float(np.sum(ndvi_valid < NDVI_STRESSED_THRESHOLD))
    moderate_count = float(
        np.sum(
            (ndvi_valid >= NDVI_STRESSED_THRESHOLD)
            & (ndvi_valid < NDVI_MODERATE_THRESHOLD)
        )
    )
    healthy_count = float(np.sum(ndvi_valid >= NDVI_MODERATE_THRESHOLD))

    stressed_percent = round(stressed_count / total * 100, 1)
    moderate_percent = round(moderate_count / total * 100, 1)
    healthy_percent = round(healthy_count / total * 100, 1)

    # Оценка пригодности почвы к посеву / посадке (0-100%)
    # 1. Влагообеспеченность почвы (по индексу NDMI)
    if mean_ndmi >= 0.15:
        moisture_pts = 40
    elif mean_ndmi >= 0.0:
        moisture_pts = int(25 + (mean_ndmi / 0.15) * 15)
    elif mean_ndmi >= -0.15:
        moisture_pts = int(10 + ((mean_ndmi + 0.15) / 0.15) * 15)
    else:
        moisture_pts = 5

    # 2. Фактор здоровья почвы / отсутствие очагов деградации
    vegetation_pts = int(max(5.0, (100.0 - stressed_percent) * 0.6))
    soil_score = min(100, max(10, moisture_pts + vegetation_pts))

    if soil_score >= 80:
        soil_status_ru = "Отличная (высокая влагозарядка и готовность)"
        soil_status_kz = "Өте қолайлы (жоғары ылғалдылық пен дайындық)"
        soil_emoji = "🟢"
    elif soil_score >= 60:
        soil_status_ru = "Хорошая (умеренная влажность)"
        soil_status_kz = "Жақсы (орташа ылғалдылық)"
        soil_emoji = "🟡"
    elif soil_score >= 40:
        soil_status_ru = "Удовлетворительная (риск дефицита влаги)"
        soil_status_kz = "Қанағаттанарлық (ылғал тапшылығы қаупі)"
        soil_emoji = "🟠"
    else:
        soil_status_ru = "Низкая (критический дефицит влаги / засуха)"
        soil_status_kz = "Төмен (ылғалдың аса тапшылығы / құрғақшылық)"
        soil_emoji = "🔴"

    return {
        "ndvi_array": ndvi,
        "ndmi_array": ndmi,
        "mean_ndvi": round(mean_ndvi, 3),
        "min_ndvi": round(min_ndvi, 3),
        "max_ndvi": round(max_ndvi, 3),
        "mean_ndmi": round(mean_ndmi, 3),
        "stressed_percent": stressed_percent,
        "moderate_percent": moderate_percent,
        "healthy_percent": healthy_percent,
        "soil_score": soil_score,
        "soil_status_ru": soil_status_ru,
        "soil_status_kz": soil_status_kz,
        "soil_emoji": soil_emoji,
        "has_buildings": has_b,
        "building_count": b_count,
        "building_status_ru": b_status_ru,
        "building_status_kz": b_status_kz,
        "building_emoji": b_emoji,
    }
