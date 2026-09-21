"""
pdf_generator.py
Генерация официального PDF-паспорта мониторинга поля через ReportLab.
"""

import io
import logging
import tempfile
import os
from datetime import datetime
from typing import Dict

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

# Цветовая палитра
COLOR_GREEN = colors.HexColor("#2d9e5d")
COLOR_DARK = colors.HexColor("#1a1d2e")
COLOR_LIGHT_GRAY = colors.HexColor("#f4f6f9")
COLOR_RED = colors.HexColor("#e63946")
COLOR_YELLOW = colors.HexColor("#f4a261")


def _get_status_color(stressed_percent: float):
    if stressed_percent > 40:
        return COLOR_RED, "🔴 Критическое / Критикалық"
    elif stressed_percent > 20:
        return COLOR_YELLOW, "🟡 Умеренное / Орташа"
    else:
        return COLOR_GREEN, "🟢 Хорошее / Жақсы"


def generate_field_passport(
    stats: Dict,
    ai_advice: str,
    ndvi_image_bytes: bytes,
    lat: float,
    lon: float,
    date_str: str,
) -> bytes:
    """
    Генерирует одностраничный PDF-паспорт мониторинга поля.

    Args:
        stats: Словарь со статистикой NDVI/NDMI.
        ai_advice: Текст рекомендаций от AI-агронома.
        ndvi_image_bytes: PNG тепловой карты в байтах.
        lat: Широта.
        lon: Долгота.
        date_str: Дата снимка.

    Returns:
        PDF-документ в байтах.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()

    style_title = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=16,
        textColor=colors.white,
        backColor=COLOR_DARK,
        alignment=TA_CENTER,
        spaceAfter=4,
        spaceBefore=4,
        leading=22,
        borderPad=8,
    )
    style_subtitle = ParagraphStyle(
        "CustomSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.white,
        backColor=COLOR_GREEN,
        alignment=TA_CENTER,
        spaceAfter=2,
        spaceBefore=2,
        leading=14,
        borderPad=5,
    )
    style_heading = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=11,
        textColor=COLOR_DARK,
        spaceAfter=4,
        spaceBefore=8,
        borderPad=2,
        leading=14,
    )
    style_body = ParagraphStyle(
        "CustomBody",
        parent=styles["Normal"],
        fontSize=8.5,
        textColor=colors.HexColor("#333333"),
        spaceAfter=3,
        leading=13,
    )
    style_footer = ParagraphStyle(
        "CustomFooter",
        parent=styles["Normal"],
        fontSize=7,
        textColor=colors.gray,
        alignment=TA_CENTER,
    )

    story = []

    # ── ЗАГОЛОВОК ─────────────────────────────────────────────────────────────
    story.append(
        Paragraph(
            "🌾 DalaSat<br/>"
            "<font size='12'>Паспорт мониторинга поля / Алқаптың мониторинг төлқұжаты</font>",
            style_title,
        )
    )
    story.append(
        Paragraph(
            f"Sentinel-2 L2A · {date_str} · Акмолинская область / Ақмола облысы",
            style_subtitle,
        )
    )
    story.append(Spacer(1, 0.3 * cm))

    # ── ИНФОРМАЦИЯ О ПОЛЕ ─────────────────────────────────────────────────────
    status_color, status_text = _get_status_color(stats["stressed_percent"])

    meta_data = [
        ["📍 Координаты / Координаттар", f"{lat:.5f}°N,  {lon:.5f}°E"],
        ["📅 Дата снимка / Снимок күні", date_str],
        ["🕐 Дата отчёта / Есеп күні", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")],
        ["🛰  Спутник / Жер серігі", "Sentinel-2 L2A (ESA Copernicus)"],
        ["📊 Общий статус / Жалпы жағдай", status_text],
    ]

    meta_table = Table(
        meta_data,
        colWidths=[7 * cm, 10.5 * cm],
        hAlign="LEFT",
    )
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), COLOR_LIGHT_GRAY),
        ("BACKGROUND", (1, 0), (1, -1), colors.white),
        ("TEXTCOLOR", (0, 0), (-1, -1), COLOR_DARK),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (1, 4), (1, 4), status_color),
        ("FONTNAME", (1, 4), (1, 4), "Helvetica-Bold"),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.4 * cm))

    # ── ТЕПЛОВАЯ КАРТА NDVI ───────────────────────────────────────────────────
    story.append(Paragraph("📡 Тепловая карта NDVI / NDVI жылу картасы", style_heading))
    try:
        ndvi_img = Image(io.BytesIO(ndvi_image_bytes), width=17.5 * cm, height=7.5 * cm)
        story.append(ndvi_img)
    except Exception as exc:
        logger.error("Не удалось вставить карту в PDF: %s", exc)

    story.append(Spacer(1, 0.4 * cm))

    # ── ТАБЛИЦА МЕТРИК ────────────────────────────────────────────────────────
    story.append(Paragraph("📊 Метрики вегетации / Өсімдік метрикалары", style_heading))

    metrics_header = [
        ["Показатель / Көрсеткіш", "Значение / Мәні", "Норма / Норма", "Интерпретация / Түсіндірме"]
    ]
    metrics_data = [
        [
            "NDVI (среднее)",
            str(stats["mean_ndvi"]),
            "0.45 – 0.75",
            "Отлично" if stats["mean_ndvi"] >= 0.45 else ("Умеренно" if stats["mean_ndvi"] >= 0.25 else "Стресс")
        ],
        [
            "NDVI (мин / макс)",
            f"{stats['min_ndvi']} / {stats['max_ndvi']}",
            "—",
            "Диапазон значений"
        ],
        [
            "NDMI (влажность)",
            str(stats["mean_ndmi"]),
            "> 0.20",
            "Норма" if stats["mean_ndmi"] >= 0.2 else ("Стресс" if stats["mean_ndmi"] >= 0.0 else "Засуха")
        ],
        [
            "🔴 Стресс / Стресс",
            f"{stats['stressed_percent']}%",
            "< 15%",
            "NDVI < 0.25 — засуха, проплешины"
        ],
        [
            "🟡 Умеренно / Орташа",
            f"{stats['moderate_percent']}%",
            "—",
            "NDVI 0.25–0.45"
        ],
        [
            "🟢 Отлично / Жақсы",
            f"{stats['healthy_percent']}%",
            "> 60%",
            "NDVI ≥ 0.45 — густая вегетация"
        ],
        [
            "🌱 Почва для посадки",
            f"{stats.get('soil_score', 50)}%",
            "> 65%",
            stats.get('soil_status_ru', 'Оценка почвы')[:32]
        ],
        [
            "🏛 Постройки / Құрылыс",
            f"~{stats.get('building_count', 0)} ед." if stats.get('has_buildings') else "0 ед.",
            "—",
            stats.get('building_status_ru', 'Чистое поле')[:32]
        ],
    ]

    metrics_table = Table(
        metrics_header + metrics_data,
        colWidths=[5.0 * cm, 2.8 * cm, 2.8 * cm, 6.9 * cm],
        hAlign="LEFT",
    )
    metrics_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_GRAY]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ALIGN", (1, 0), (2, -1), "CENTER"),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 0.5 * cm))

    # ── ЗАКЛЮЧЕНИЕ AI-АГРОНОМА ────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_GREEN))
    story.append(Spacer(1, 0.2 * cm))
    story.append(
        Paragraph("🤖 Заключение ИИ-агронома / ЖИ агрономының қорытындысы", style_heading)
    )

    # Разбиваем текст AI на параграфы
    for line in ai_advice.split("\n"):
        line = line.strip()
        if line:
            story.append(Paragraph(line, style_body))

    story.append(Spacer(1, 0.5 * cm))

    # ── FOOTER ────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 0.15 * cm))
    story.append(
        Paragraph(
            "DalaSat · AgriTech AI Hackathon · Aqmola Hub / Astana Hub · "
            "Данные: ESA Copernicus Sentinel-2 L2A · Microsoft Planetary Computer",
            style_footer,
        )
    )

    doc.build(story)
    buf.seek(0)
    return buf.read()
