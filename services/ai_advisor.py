"""
ai_advisor.py
Генерация двуязычного агрономического анализа через Google Gemini API.
Использует актуальный SDK: google-genai (google.genai)
"""

import logging
from typing import Dict

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

# Инициализируем клиент Gemini один раз при импорте модуля
_client = genai.Client(api_key=GEMINI_API_KEY)


def _build_prompt(stats: Dict, lat: float, lon: float, date_str: str, lang: str = "ru") -> str:
    """Формирует детальный промпт для Gemini на выбранном языке."""
    ndvi_status = "критическая" if stats["stressed_percent"] > 40 else (
        "умеренная" if stats["stressed_percent"] > 20 else "хорошая"
    )
    ndmi_status = "дефицит влаги (засуха)" if stats["mean_ndmi"] < 0.1 else (
        "умеренный стресс" if stats["mean_ndmi"] < 0.3 else "оптимальная влажность"
    )

    b_count = stats.get("building_count", 0)
    b_status_ru = stats.get("building_status_ru", "Построек не обнаружено")
    b_status_kz = stats.get("building_status_kz", "Құрылыстар байқалмады")

    if lang == "kz":
        instruction = """НҰСҚАУЛЫҚ:
ЖАУАПТЫ ТЕК ҚАЗАҚ ТІЛІНДЕ ЖАЗЫҢЫЗ (3-5 сөйлем, кәсіби және нақты):
1. Топырақтың ылғалдылығы мен егуге дайындығын бағалаңыз.
2. Ақмола өңірінің климатын ескере отырып, 1-2 басты қауіпті атаңыз (аңызақ жел, құрғақшылық).
3. Фермерге 2 нақты іс-қимыл кеңесін беріңіз (ылғалды жабу, тұқым сіңіру тереңдігі, тыңайтқыш немесе себу мерзімі).
4. Егер алқапта немесе оған жақын жерде құрылыстар (қора, қойма, стан) байқалса, техниканың кіру жолы мен қауіпсіздік аймағын қысқаша ескертіңіз.
Бастапқы артық сөздерсіз бірден талдаудан бастаңыз."""
    elif lang == "both":
        instruction = """ИНСТРУКЦИЯ:
1. Напиши блок ҚАЗАҚША (3-4 предложения) с оценкой почвы, постройками, рисками и советами.
2. Напиши блок РУССКИЙ (3-4 предложения) с оценкой почвы, постройками, рисками и советами."""
    else:
        instruction = """ИНСТРУКЦИЯ:
ОТВЕТ НАПИШИ ТОЛЬКО НА РУССКОМ ЯЗЫКЕ (3-5 предложений, профессионально и по делу):
1. Оцени готовность почвы к севу/посадке и уровень влагозарядки.
2. Назови 1-2 главных риска с учётом климата Акмолинской области (суховеи, дефицит продуктивной влаги).
3. Дай 2 конкретных агрономических совета (закрытие влаги, глубина заделки семян яровой пшеницы, фосфорные удобрения).
4. Если на участке или рядом обнаружены постройки/сооружения, учти их (буферная зона, заезд сельхозтехники, логистика).
Начни сразу с анализа без лишних приветствий."""

    return f"""Ты — главный цифровой агроном Акмолинской области Казахстана (сервис DalaSat). Твоя задача — дать практичный анализ состояния поля и готовности почвы к посадке/посеву по снимку Sentinel-2.

ДАННЫЕ ПОЛЯ:
- Дата снимка: {date_str}
- Координаты: широта {lat:.4f}, долгота {lon:.4f}
- Средний NDVI: {stats['mean_ndvi']} (диапазон: {stats['min_ndvi']} — {stats['max_ndvi']})
- Индекс влажности NDMI: {stats['mean_ndmi']} (состояние: {ndmi_status})
- Пригодность почвы для посадки/сева: {stats.get('soil_score', 50)}% ({stats.get('soil_status_ru', '')})
- Постройки и сооружения на участке: {b_status_ru} (оценка: ~{b_count} ед.)
- Депрессивные зоны (NDVI < 0.25): {stats['stressed_percent']}%
- Удовлетворительная вегетация: {stats['moderate_percent']}%
- Отличная вегетация: {stats['healthy_percent']}%
- Общая оценка: {ndvi_status}

{instruction}
"""


async def get_agronomic_advice(
    stats: Dict,
    lat: float,
    lon: float,
    date_str: str,
    lang: str = "ru",
) -> str:
    """
    Запрашивает агрономический анализ у Google Gemini на выбранном языке.

    Args:
        stats: Словарь статистики с calculate_indices().
        lat: Широта поля.
        lon: Долгота поля.
        date_str: Дата снимка.
        lang: Язык ответа ("ru", "kz", "both").

    Returns:
        Текст анализа.
    """
    prompt = _build_prompt(stats, lat, lon, date_str, lang=lang)

    # Запрос через современный Interactions API (без ворнингов AFC и ошибок 404)
    for model_name in [GEMINI_MODEL, "gemini-3.1-flash-lite", "gemini-3.8-flash"]:
        try:
            interaction = await _client.aio.interactions.create(
                model=model_name,
                input=prompt,
            )
            if interaction and interaction.output_text:
                return interaction.output_text.strip()
        except Exception as exc:
            logger.warning("Попытка через %s не удалась: %s", model_name, exc)

    logger.error("Все модели Gemini недоступны, используется агрономический резерв")
    ndvi = stats["mean_ndvi"]
    stressed = stats["stressed_percent"]
    soil = stats.get("soil_score", 50)
    if lang == "kz":
        return (
            f"🇰🇿 Топырақтың егуге дайындығы: {soil}%. Орташа NDVI: {ndvi}. "
            f"Стресс аймағы: {stressed}%. "
            f"{'Алқапта ылғал жетіспеушілігі байқалады. Ылғалды жабу жұмыстары ұсынылады.' if stressed > 30 else 'Топырақ ылғалдылығы қанағаттанарлық, егуге қолайлы.'}"
        )
    elif lang == "both":
        return (
            f"🇰🇿 ҚАЗАҚША: Топырақтың дайындығы: {soil}%. Орташа NDVI: {ndvi}. Стресс: {stressed}%.\n\n"
            f"🇷🇺 РУССКИЙ: Готовность почвы: {soil}%. Средний NDVI: {ndvi}. Зона стресса: {stressed}%."
        )
    else:
        return (
            f"🇷🇺 Готовность почвы к севу: {soil}%. Средний NDVI: {ndvi}. "
            f"Зона стресса: {stressed}%. "
            f"{'Наблюдается дефицит влаги в почве. Рекомендуется закрытие влаги и контроль глубины заделки.' if stressed > 30 else 'Состояние почвы и влагозарядка удовлетворительные.'}"
        )
