"""
visualizer.py
Отрисовка тепловой карты NDVI с использованием Matplotlib.
Возвращает PNG-изображение в байтах (без записи на диск).
"""

import io

import matplotlib
matplotlib.use("Agg")  # headless backend, без GUI
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from config import NDVI_MODERATE_THRESHOLD, NDVI_STRESSED_THRESHOLD


def generate_ndvi_map(
    ndvi_array: np.ndarray,
    lat: float,
    lon: float,
    date_str: str,
) -> bytes:
    """
    Генерирует тепловую карту NDVI и возвращает PNG-изображение в байтах.

    Args:
        ndvi_array: 2D numpy массив со значениями NDVI.
        lat: Широта центра поля.
        lon: Долгота центра поля.
        date_str: Дата снимка в формате строки.

    Returns:
        PNG-изображение в байтах.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), facecolor="#0f1117")

    # ── Левая панель: тепловая карта NDVI ────────────────────────────────────
    ax_map = axes[0]
    ax_map.set_facecolor("#0f1117")

    im = ax_map.imshow(
        ndvi_array,
        cmap="RdYlGn",
        vmin=0.0,
        vmax=0.8,
        interpolation="bilinear",
    )

    cbar = fig.colorbar(im, ax=ax_map, fraction=0.046, pad=0.04)
    cbar.ax.yaxis.set_tick_params(color="white")
    cbar.outline.set_edgecolor("white")
    plt.setp(plt.getp(cbar.ax.axes, "yticklabels"), color="white", fontsize=8)
    cbar.set_label("NDVI", color="white", fontsize=9)

    # Подписи на цветовой шкале
    cbar.ax.text(
        2.0, 0.05, "Засуха / Кепкен жер", transform=cbar.ax.transAxes,
        color="#ff6b6b", fontsize=7, va="bottom",
    )
    cbar.ax.text(
        2.0, 0.95, "Гүлдену / Сочная растительность", transform=cbar.ax.transAxes,
        color="#69db7c", fontsize=7, va="top",
    )

    ax_map.set_title(
        f"NDVI · {lat:.4f}°N {lon:.4f}°E · {date_str}",
        color="white", fontsize=11, pad=10, fontweight="bold",
    )
    ax_map.axis("off")

    # Водяной знак
    ax_map.text(
        0.01, 0.01, "DalaSat · Sentinel-2 L2A",
        transform=ax_map.transAxes, color="white",
        fontsize=7, alpha=0.6, va="bottom",
    )

    # ── Правая панель: круговая диаграмма классификации ──────────────────────
    ax_pie = axes[1]
    ax_pie.set_facecolor("#0f1117")

    # Вычисляем классы
    flat = ndvi_array.flatten()
    valid = flat[(flat > -0.5) & (flat < 1.0)]  # убираем nodata

    if valid.size > 0:
        stressed = float(np.sum(valid < NDVI_STRESSED_THRESHOLD)) / valid.size * 100
        moderate = float(
            np.sum(
                (valid >= NDVI_STRESSED_THRESHOLD) & (valid < NDVI_MODERATE_THRESHOLD)
            )
        ) / valid.size * 100
        healthy = float(np.sum(valid >= NDVI_MODERATE_THRESHOLD)) / valid.size * 100
    else:
        stressed, moderate, healthy = 33.3, 33.3, 33.3

    sizes = [stressed, moderate, healthy]
    colors = ["#ff6b6b", "#ffd43b", "#51cf66"]
    labels = [
        f"Стресс / Стресс\n{stressed:.1f}%",
        f"Норма / Орташа\n{moderate:.1f}%",
        f"Сочные / Гүлденген\n{healthy:.1f}%",
    ]
    explode = (0.05, 0.05, 0.05)

    wedges, texts = ax_pie.pie(
        sizes,
        labels=None,
        colors=colors,
        explode=explode,
        startangle=90,
        wedgeprops={"edgecolor": "#0f1117", "linewidth": 2},
    )

    legend_patches = [
        mpatches.Patch(color=c, label=l)
        for c, l in zip(colors, labels)
    ]
    ax_pie.legend(
        handles=legend_patches,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.15),
        fontsize=8,
        labelcolor="white",
        facecolor="#1a1d24",
        edgecolor="gray",
        framealpha=0.8,
    )

    ax_pie.set_title(
        "Классификация пикселей / Пиксель жіктелуі",
        color="white", fontsize=10, pad=15, fontweight="bold",
    )

    # Общий заголовок
    fig.suptitle(
        "DalaSat — Экспресс-анализ поля / Алқапты жедел талдау",
        color="white", fontsize=13, fontweight="bold", y=1.01,
    )

    plt.tight_layout()

    # Сохраняем в буфер памяти
    buf = io.BytesIO()
    fig.savefig(
        buf, format="png", dpi=150,
        facecolor=fig.get_facecolor(),
        bbox_inches="tight",
    )
    plt.close(fig)
    buf.seek(0)
    return buf.read()
