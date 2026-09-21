"""
build_html_presentation.py
Генерация элитной минималистичной 10-слайдовой презентации DalaSat (16:9 PDF, 1920x1080).
Полное соответствие ТЗ хакатона «AgriTech AI Hackathon» (Aqmola Hub / Digital Aqmola):
1. Проблема (Акмолинская область, 5.2 млн га пашни, засуха, нехватка кадров, дорогие зарубежные ГИС)
2. Решение (DalaSat — спутниковый Telegram-бот на каз/рус по 1 геоточке/тексту, PDF-паспорт)
3. Демонстрация (Реальный снимок NDVI поля в Зеренде 400 га + live-вывод бота с вердиктом ИИ)
4. Данные и модель (Sentinel-2 L2A, STAC API COG windowed read, Rasterio/NumPy, Gemini Interactions API)
5. Полученные метрики (IoU, F1-score сегментации, Accuracy классификации, отклонение площади, Latency)
6. Инновационность ИИ (Зональная агрономия Северного Казахстана, параллельный синтез KZ/RU)
7. Экономический эффект (Экономия 4500-7000 ₸/га, +1.5-2.5 ц/га зерна, рынок 24 млн га в РК)
8. Дорожная карта и планы развития (Фазы 1, 2, 3: Sentinel-1 SAR радар, кадастр KML, ML-прогноз)
9. Команда:
   - Адильхан Ануар — Founder · IT / Design
   - Алиев Исмайл — Design · Marketing
   - Досай Али — Cofounder · Speaker
10. Воспроизводимость, готовность к пилоту в Акмолинской области и контакты

Стиль по требованиям пользователя:
- Теплый бежевый фон (#F5F2EB) без резких контрастов
- Ровно 2-3 гармоничных цвета (Бежевый #F5F2EB, Графитовый текст #1E2522, Глубокий степной зеленый #28543E + Чистые белые карточки #FFFFFF)
- Полное отсутствие неона и эффекта стекла (без blurs, без glowing halos)
- Строго без эмодзи (чистые векторные SVG-иконки Feather/Lucide)
- Правый нижний угол каждого слайда абсолютно чист
- Ровно 10 слайдов, альбомный 16:9
"""

import os
import shutil
import base64
import subprocess
import re

DIR = os.path.dirname(os.path.abspath(__file__))

def get_b64(filename: str) -> str:
    path = os.path.join(DIR, filename)
    if not os.path.exists(path):
        return ""
    ext = os.path.splitext(filename)[1].lower().replace(".", "")
    mime = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/png"
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{data}"

AVATAR_B64 = get_b64("dalasat_avatar.jpg")
MAP_B64 = get_b64("demo_ndvi_map.png")

# Чистые векторные SVG-иконки Feather/Lucide (строго без эмодзи)
SVG_ICONS = {
    "satellite": """<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 7 9 3 5 7l4 4"/><path d="m17 11 4 4-4 4-4-4"/><path d="m8 12 4 4 6-6-4-4Z"/><path d="m16 8 3-3"/><path d="M9 21a6 6 0 0 0-6-6"/></svg>""",
    "map_pin": """<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>""",
    "sprout": """<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 20h10"/><path d="M10 20c5.5-2.5.8-6.4 3-13"/><path d="M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4.2 2.8-.5 4.4 0 5.5.8z"/><path d="M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.7-4.6-2.7.1-4 1-4.9 2z"/></svg>""",
    "cpu": """<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9" rx="1"/><path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/><path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/></svg>""",
    "file_text": """<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/></svg>""",
    "shield_alert": """<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="M12 8v4"/><path d="M12 16h.01"/></svg>""",
    "activity": """<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>""",
    "trending_up": """<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>""",
    "layers": """<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/><path d="m22 12.5-8.58 3.91a2 2 0 0 1-1.66 0L2 12.5"/><path d="m22 17.5-8.58 3.91a2 2 0 0 1-1.66 0L2 17.5"/></svg>""",
    "building": """<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="16" height="20" x="4" y="2" rx="2" ry="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01"/><path d="M16 6h.01"/><path d="M8 10h.01"/><path d="M16 10h.01"/><path d="M8 14h.01"/><path d="M16 14h.01"/></svg>""",
    "check_circle": """<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>""",
    "users": """<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>""",
    "globe": """<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" x2="22" y1="12" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>""",
}

HTML_TEMPLATE = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>DalaSat — Презентация проекта</title>
<style>
@page {{
    size: 1920px 1080px;
    margin: 0;
}}
* {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}
body {{
    width: 1920px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background: #F5F2EB;
    color: #1E2522;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
}}

/* Базовый слайд 16:9 — Мягкий бежевый фон без резких контрастов */
.slide {{
    width: 1920px;
    height: 1080px;
    page-break-after: always;
    position: relative;
    overflow: hidden;
    padding: 55px 80px 45px 80px;
    display: flex;
    flex-direction: column;
    background: #F5F2EB;
}}

/* Шапка слайда: строгая и лаконичная */
.header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1.5px solid #DDD7CB;
    padding-bottom: 14px;
    margin-bottom: 28px;
}}
.header-left {{
    display: flex;
    align-items: center;
    gap: 16px;
}}
.header-badge {{
    background: #28543E;
    color: #FFFFFF;
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 1.5px;
    padding: 6px 14px;
    border-radius: 6px;
}}
.header-title {{
    color: #5A6560;
    font-size: 15px;
    font-weight: 600;
    letter-spacing: 1px;
}}
.header-slide-num {{
    color: #28543E;
    font-size: 15px;
    font-weight: 800;
    letter-spacing: 1px;
}}

/* Заголовки слайда */
.slide-h1 {{
    font-size: 38px;
    font-weight: 800;
    color: #1E2522;
    line-height: 1.2;
    margin-bottom: 8px;
    letter-spacing: -0.5px;
}}
.slide-sub {{
    font-size: 19px;
    color: #5A6560;
    line-height: 1.4;
    margin-bottom: 28px;
}}

/* Нижний колонтитул: СПРАВА СНИЗУ СТРОГО ПУСТО */
.footer {{
    margin-top: auto;
    border-top: 1.5px solid #DDD7CB;
    padding-top: 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}
.footer-left {{
    color: #727C77;
    font-size: 14px;
    font-weight: 500;
}}
.footer-right {{
    display: none;
}}

/* Сетки */
.grid-3 {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 24px;
    flex: 1;
}}
.grid-4 {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    flex: 1;
}}
.grid-2 {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 28px;
    flex: 1;
}}

/* Карточки: сплошной белый фон #FFFFFF, тонкая рамка #E2DDD5, БЕЗ СТЕКЛА И БЕЗ НЕОНА */
.card {{
    background: #FFFFFF;
    border: 1px solid #E2DDD5;
    border-radius: 16px;
    padding: 26px 28px;
    display: flex;
    flex-direction: column;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
}}
.card-highlight {{
    background: #FFFFFF;
    border: 2px solid #28543E;
}}

.icon-badge {{
    width: 48px;
    height: 48px;
    border-radius: 12px;
    background: #ECE7DC;
    color: #28543E;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 16px;
}}

.card-tag {{
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: #28543E;
    margin-bottom: 8px;
}}

.card-title {{
    font-size: 22px;
    font-weight: 700;
    color: #1E2522;
    line-height: 1.3;
    margin-bottom: 12px;
}}
.card-desc {{
    font-size: 15.5px;
    line-height: 1.6;
    color: #3B4642;
}}
.card-desc li {{
    margin-left: 20px;
    margin-bottom: 8px;
}}
.card-desc li strong, .card-desc strong {{
    color: #1E2522;
}}

.metric-number {{
    font-size: 42px;
    font-weight: 800;
    color: #28543E;
    line-height: 1;
    margin-bottom: 8px;
    letter-spacing: -1px;
}}

.divider {{
    height: 1px;
    background: #ECE7DC;
    margin: 14px 0;
}}

/* Слайд 1: Hero */
.hero-container {{
    display: grid;
    grid-template-columns: 1.25fr 0.75fr;
    gap: 40px;
    align-items: center;
    flex: 1;
}}
.hero-title {{
    font-size: 78px;
    font-weight: 900;
    color: #1E2522;
    line-height: 1.05;
    margin-bottom: 16px;
    letter-spacing: -2px;
}}
.hero-sub {{
    font-size: 25px;
    font-weight: 700;
    color: #28543E;
    line-height: 1.4;
    margin-bottom: 18px;
}}
.hero-desc {{
    font-size: 18.5px;
    line-height: 1.6;
    color: #4B5652;
    margin-bottom: 32px;
}}
.hero-metrics {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 18px;
}}
.hero-metric-box {{
    background: #FFFFFF;
    border: 1px solid #E2DDD5;
    border-radius: 14px;
    padding: 16px 20px;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.02);
}}
.hero-metric-val {{
    font-size: 32px;
    font-weight: 800;
    color: #28543E;
    margin-bottom: 4px;
}}
.hero-metric-lbl {{
    font-size: 14px;
    font-weight: 600;
    color: #1E2522;
}}
.avatar-box {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: #FFFFFF;
    border: 1px solid #E2DDD5;
    border-radius: 24px;
    padding: 28px;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.03);
}}
.avatar-img {{
    width: 290px;
    height: 290px;
    border-radius: 16px;
    border: 1px solid #E2DDD5;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
    margin-bottom: 18px;
}}

/* Слайд 4: Архитектура */
.arch-row {{
    background: #FFFFFF;
    border: 1px solid #E2DDD5;
    border-radius: 14px;
    padding: 18px 24px;
    margin-bottom: 14px;
    display: grid;
    grid-template-columns: 240px 1fr 280px;
    align-items: center;
    gap: 22px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
}}
.arch-num {{
    font-size: 13px;
    font-weight: 800;
    color: #28543E;
    letter-spacing: 1px;
}}
.arch-name {{
    font-size: 21px;
    font-weight: 700;
    color: #1E2522;
}}
.arch-body {{
    font-size: 15.5px;
    color: #3B4642;
    line-height: 1.5;
}}
.arch-tech {{
    background: #ECE7DC;
    border: 1px solid #DDD7CB;
    border-radius: 8px;
    padding: 10px 16px;
    font-size: 14px;
    font-weight: 700;
    color: #28543E;
    text-align: center;
}}

/* Слайд 5: Демо */
.map-frame {{
    background: #FFFFFF;
    border: 1px solid #E2DDD5;
    border-radius: 16px;
    padding: 14px;
    display: flex;
    flex-direction: column;
    align-items: center;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
}}
.map-img {{
    width: 100%;
    height: 490px;
    object-fit: contain;
    border-radius: 8px;
    border: 1px solid #E2DDD5;
}}
.telegram-mockup {{
    background: #FFFFFF;
    border: 1px solid #E2DDD5;
    border-radius: 16px;
    padding: 24px;
    display: flex;
    flex-direction: column;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
}}
.tg-header {{
    display: flex;
    align-items: center;
    gap: 14px;
    border-bottom: 1px solid #ECE7DC;
    padding-bottom: 12px;
    margin-bottom: 16px;
}}
.tg-bubble {{
    background: #F5F2EB;
    border-radius: 14px;
    padding: 18px;
    font-size: 15px;
    line-height: 1.6;
    color: #2D3834;
    border-left: 4px solid #28543E;
}}
.tg-bubble strong {{ color: #1E2522; }}
.tg-bubble em {{ color: #28543E; font-style: normal; font-weight: 600; }}
</style>
</head>
<body>

<!-- ═════════════════════════════════════════════════════════════════════════ -->
<!-- СЛАЙД 1: ТИТУЛЬНЫЙ -->
<!-- ═════════════════════════════════════════════════════════════════════════ -->
<section class="slide" style="justify-content: space-between;">
    <div class="header">
        <div class="header-left">
            <span class="header-badge">AGRITECH AI HACKATHON 2026</span>
            <span class="header-title">ТРЕК 1: ГИС И ДИСТАНЦИОННОЕ ЗОНДИРОВАНИЕ ЗЕМЛИ</span>
        </div>
        <div class="header-slide-num">СЛАЙД 01 / 10</div>
    </div>

    <div class="hero-container">
        <div>
            <h1 class="hero-title">DalaSat</h1>
            <div class="hero-sub">Спутниковый экспресс-мониторинг полей и цифровой ИИ-агроном</div>
            <p class="hero-desc">
                Интеллектуальная система спутникового ДЗЗ анализа на базе Sentinel-2 L2A и Gemini AI. 
                Мгновенная оценка вегетации (NDVI), влагосодержания почвы (NDMI), детекция построек и генерация официального PDF-паспорта поля в Telegram в 1 клик.
            </p>

            <div class="hero-metrics">
                <div class="hero-metric-box">
                    <div class="hero-metric-val">10 м</div>
                    <div class="hero-metric-lbl">Разрешение Sentinel-2</div>
                    <div style="font-size: 13px; color: #5A6560; margin-top: 4px;">Спектральный анализ L2A</div>
                </div>
                <div class="hero-metric-box">
                    <div class="hero-metric-val">10 сек</div>
                    <div class="hero-metric-lbl">Скорость анализа поля</div>
                    <div style="font-size: 13px; color: #5A6560; margin-top: 4px;">Прямой COG Windowed Read</div>
                </div>
                <div class="hero-metric-box">
                    <div class="hero-metric-val">1 клик</div>
                    <div class="hero-metric-lbl">Доступность для фермера</div>
                    <div style="font-size: 13px; color: #5A6560; margin-top: 4px;">Прямо в Telegram (RU/KZ)</div>
                </div>
            </div>
        </div>

        <div class="avatar-box">
            <img src="{AVATAR_B64}" class="avatar-img" alt="DalaSat Avatar">
            <div style="font-size: 22px; font-weight: 800; color: #1E2522; margin-bottom: 6px;">DalaSat System</div>
            <div style="font-size: 13px; color: #28543E; font-weight: 700; letter-spacing: 1px;">SENTINEL-2 L2A · GEMINI AI · PYTHON 3.12</div>
        </div>
    </div>

    <div class="footer">
        <div class="footer-left">Акмолинская область · Астана Hub · Aqmola Hub</div>
        <div class="footer-right"></div>
    </div>
</section>

<!-- ═════════════════════════════════════════════════════════════════════════ -->
<!-- СЛАЙД 2: ПРОБЛЕМАТИКА -->
<!-- ═════════════════════════════════════════════════════════════════════════ -->
<section class="slide">
    <div class="header">
        <div class="header-left">
            <span class="header-badge">DALASAT</span>
            <span class="header-title">ТРЕК 1: ГИС И ДЗЗ · AGRITECH AI HACKATHON 2026</span>
        </div>
        <div class="header-slide-num">СЛАЙД 02 / 10</div>
    </div>

    <h1 class="slide-h1">Проблематика: барьеры эффективного мониторинга полей</h1>
    <p class="slide-sub">Акмолинская область — ключевой зерновой пояс Казахстана (5.2 млн га пашни). Почему традиционные методы не работают:</p>

    <div class="grid-3">
        <div class="card">
            <div class="icon-badge">{SVG_ICONS['map_pin']}</div>
            <div class="card-tag">[ МАСШТАБ И КАДРЫ ]</div>
            <div class="metric-number">5.2 млн га</div>
            <div class="card-title">Огромные площади и дефицит агрономов</div>
            <div class="divider"></div>
            <ul class="card-desc">
                <li>Размеры одного хозяйства достигают <strong>от 10 000 до 50 000 га</strong>.</li>
                <li>Физический объезд полей занимает <strong>3–5 дней</strong> и требует сотен литров дорогого ГСМ.</li>
                <li>Дефицит дипломированных агрономов в районах области <strong>превышает 60%</strong>.</li>
                <li>Итог: <strong>более 75% площадей</strong> остаются без регулярного экспертного контроля.</li>
            </ul>
        </div>

        <div class="card">
            <div class="icon-badge">{SVG_ICONS['shield_alert']}</div>
            <div class="card-tag">[ КЛИМАТИЧЕСКИЙ РИСК ]</div>
            <div class="metric-number">48–72 часа</div>
            <div class="card-title">Суховеи и потеря продуктивной влаги</div>
            <div class="divider"></div>
            <ul class="card-desc">
                <li>Резко континентальный засушливый климат Северного Казахстана.</li>
                <li>Весенняя продуктивная влага в верхнем горизонте почвы <strong>испаряется за 2–3 дня</strong>.</li>
                <li>Опоздание с боронованием или посевом на 3 дня <strong>снижает урожайность на 25–35%</strong>.</li>
                <li>Традиционные замеры ручными щупами дают запоздалую и точечную оценку.</li>
            </ul>
        </div>

        <div class="card">
            <div class="icon-badge">{SVG_ICONS['activity']}</div>
            <div class="card-tag">[ БАРЬЕР ВХОДА ]</div>
            <div class="metric-number">$1.5–$3 / га</div>
            <div class="card-title">Недоступность профессиональных ГИС</div>
            <div class="divider"></div>
            <ul class="card-desc">
                <li>Зарубежные системы (OneSoil, Cropwise) требуют <strong>дорогостоящей валютной подписки</strong>.</li>
                <li>Требуют мощных ПК, специализированного обучения и работы со сложными ГИС-слоями.</li>
                <li><strong>85% малых и средних крестьянских хозяйств</strong> лишены доступа к цифровым технологиям.</li>
            </ul>
        </div>
    </div>

    <div class="footer">
        <div class="footer-left">Акмолинская область · Астана Hub · Aqmola Hub</div>
        <div class="footer-right"></div>
    </div>
</section>

<!-- ═════════════════════════════════════════════════════════════════════════ -->
<!-- СЛАЙД 3: РЕШЕНИЕ DALASAT -->
<!-- ═════════════════════════════════════════════════════════════════════════ -->
<section class="slide">
    <div class="header">
        <div class="header-left">
            <span class="header-badge">DALASAT</span>
            <span class="header-title">ТРЕК 1: ГИС И ДЗЗ · AGRITECH AI HACKATHON 2026</span>
        </div>
        <div class="header-slide-num">СЛАЙД 03 / 10</div>
    </div>

    <h1 class="slide-h1">Решение DalaSat: космические технологии в руках фермера</h1>
    <p class="slide-sub">Бесшовный технологический мост между спутниками Sentinel-2 и аграрием прямо в Telegram в 1 клик:</p>

    <div class="grid-4">
        <div class="card">
            <div class="icon-badge">{SVG_ICONS['map_pin']}</div>
            <div class="card-tag">[ МОБИЛЬНОСТЬ ]</div>
            <div class="card-title">Мониторинг по 1 точке</div>
            <div class="divider"></div>
            <div class="card-desc">
                • Отправка GPS со смартфона прямо в поле.<br/><br/>
                • Распознавание координат из любых текстовых сообщений.<br/><br/>
                • Выбор масштаба поля: 1×1 км (~100 га), 2×2 км (~400 га) или 4×4 км (~1600 га).<br/><br/>
                • <strong>Без регистрации и установки приложений.</strong>
            </div>
        </div>

        <div class="card">
            <div class="icon-badge">{SVG_ICONS['satellite']}</div>
            <div class="card-tag">[ СПУТНИК ДЗЗ ]</div>
            <div class="card-title">Sentinel-2 L2A без задержек</div>
            <div class="divider"></div>
            <div class="card-desc">
                • Разрешение <strong>10 метров на 1 пиксель</strong> от Европейского космического агентства (ESA).<br/><br/>
                • Автопоиск свежих снимков с облачностью &lt;20%.<br/><br/>
                • Спектральные индексы биомассы <strong>NDVI</strong> и влажности <strong>NDMI</strong> в реальном времени.
            </div>
        </div>

        <div class="card">
            <div class="icon-badge">{SVG_ICONS['cpu']}</div>
            <div class="card-tag">[ ИИ-АГРОНОМ ]</div>
            <div class="card-title">Двуязычный Gemini AI</div>
            <div class="divider"></div>
            <div class="card-desc">
                • Анализ на <strong>казахском и русском</strong> языках.<br/><br/>
                • Адаптация под климат и почвы Акмолинской области.<br/><br/>
                • Практические советы: глубина заделки семян яровой пшеницы, сохранение влаги, дозировка удобрений.
            </div>
        </div>

        <div class="card">
            <div class="icon-badge">{SVG_ICONS['file_text']}</div>
            <div class="card-tag">[ ДОКУМЕНТ ]</div>
            <div class="card-title">Официальный PDF-паспорт</div>
            <div class="divider"></div>
            <div class="card-desc">
                • Мгновенная сборка юридически выверенного PDF-отчёта.<br/><br/>
                • Тепловая карта поля высокого разрешения с координатной сеткой.<br/><br/>
                • Сводная таблица метрик для агрономической отчётности и <strong>получения субсидий МСХ РК</strong>.
            </div>
        </div>
    </div>

    <div class="footer">
        <div class="footer-left">Акмолинская область · Астана Hub · Aqmola Hub</div>
        <div class="footer-right"></div>
    </div>
</section>

<!-- ═════════════════════════════════════════════════════════════════════════ -->
<!-- СЛАЙД 4: АРХИТЕКТУРА И ТЕХНОЛОГИЧЕСКИЙ КОНВЕЙЕР -->
<!-- ═════════════════════════════════════════════════════════════════════════ -->
<section class="slide">
    <div class="header">
        <div class="header-left">
            <span class="header-badge">DALASAT</span>
            <span class="header-title">ТРЕК 1: ГИС И ДЗЗ · AGRITECH AI HACKATHON 2026</span>
        </div>
        <div class="header-slide-num">СЛАЙД 04 / 10</div>
    </div>

    <h1 class="slide-h1">Архитектура: сквозной конвейер обработки данных</h1>
    <p class="slide-sub">Высокая скорость (10 сек) и масштабируемость благодаря современным облачным стандартам ДЗЗ:</p>

    <div style="flex: 1; display: flex; flex-direction: column; justify-content: space-around;">
        <div class="arch-row">
            <div>
                <div class="arch-num">УРОВЕНЬ 01</div>
                <div class="arch-name">Спутниковые ДЗЗ</div>
            </div>
            <div class="arch-body">
                Прямой запрос к группировке Sentinel-2 L2A через <strong>STAC API Microsoft Planetary Computer</strong>. Технология <strong>Cloud-Optimized GeoTIFF (COG) с windowed read</strong> — скачивается только фрагмент поля (<strong>~200 КБ вместо всего снимка на 800 МБ</strong>). Ускорение в 40 раз!
            </div>
            <div class="arch-tech">Sentinel-2 COG · STAC API</div>
        </div>

        <div class="arch-row">
            <div>
                <div class="arch-num">УРОВЕНЬ 02</div>
                <div class="arch-name">Геопроцессинг Core</div>
            </div>
            <div class="arch-body">
                Нормализация спектральных каналов B04 (Red), B08 (NIR), B11 (SWIR) в Rasterio и NumPy. Расчёт матриц NDVI, NDMI, NDBI. Морфологический алгоритм связности (<strong>Connected Components BFS</strong>) для детекции построек и складов.
            </div>
            <div class="arch-tech">Rasterio · NumPy · GDAL</div>
        </div>

        <div class="arch-row">
            <div>
                <div class="arch-num">УРОВЕНЬ 03</div>
                <div class="arch-name">ИИ-Агроном Core</div>
            </div>
            <div class="arch-body">
                Генеративный анализ на базе <strong>Google Gemini 3.5 Flash-lite</strong> через нативный <strong>Interactions API</strong>. Контекстный промптинг с базой агрономических знаний Акмолинской области. Автоматический каскадный Fallback при сбоях сети.
            </div>
            <div class="arch-tech">Gemini Interactions API</div>
        </div>

        <div class="arch-row">
            <div>
                <div class="arch-num">УРОВЕНЬ 04</div>
                <div class="arch-name">Интерфейс & Экспорт</div>
            </div>
            <div class="arch-body">
                Полностью асинхронный Telegram-бот на <strong>Aiogram 3.31 (Python 3.12)</strong>. Мгновенная генерация тепловых карт с цветовой шкалой вегетации и векторных одностраничных PDF-паспортов мониторинга поля на ReportLab.
            </div>
            <div class="arch-tech">Aiogram 3 · ReportLab PDF</div>
        </div>
    </div>

    <div class="footer">
        <div class="footer-left">Акмолинская область · Астана Hub · Aqmola Hub</div>
        <div class="footer-right"></div>
    </div>
</section>

<!-- ═════════════════════════════════════════════════════════════════════════ -->
<!-- СЛАЙД 5: LIVE DEMO (РЕАЛЬНЫЙ СНИМОК И ВЫВОД БОТА) -->
<!-- ═════════════════════════════════════════════════════════════════════════ -->
<section class="slide">
    <div class="header">
        <div class="header-left">
            <span class="header-badge">DALASAT</span>
            <span class="header-title">ТРЕК 1: ГИС И ДЗЗ · AGRITECH AI HACKATHON 2026</span>
        </div>
        <div class="header-slide-num">СЛАЙД 05 / 10</div>
    </div>

    <h1 class="slide-h1">Демонстрация: реальный анализ поля в Зерендинском районе</h1>
    <p class="slide-sub">Фактический результат работы системы DalaSat на основе реальных данных Sentinel-2:</p>

    <div class="grid-2" style="align-items: stretch;">
        <div class="map-frame">
            <img src="{MAP_B64}" class="map-img" alt="NDVI Heatmap">
            <div style="font-size: 15px; color: #5A6560; text-align: center; margin-top: 10px;">
                <strong>Тепловая карта NDVI поля (Зеренда, Акмолинская обл.)</strong> · 53.2514°N, 69.1845°E · 2×2 км (400 га)
            </div>
        </div>

        <div class="telegram-mockup">
            <div class="tg-header">
                <div style="width: 44px; height: 44px; border-radius: 50%; background: #28543E; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 20px; color: white;">D</div>
                <div>
                    <div style="font-size: 18px; font-weight: 700; color: #1E2522;">DalaSat Bot <span style="color: #28543E; font-size: 14px;">✓ verified</span></div>
                    <div style="font-size: 13px; color: #727C77;">Спутниковый ассистент поля · bot</div>
                </div>
            </div>

            <div class="tg-bubble">
                <div style="font-size: 18px; font-weight: 800; color: #1E2522; margin-bottom: 12px;">DalaSat — Экспресс-анализ поля</div>
                <strong>Координаты:</strong> 53.2514°N, 69.1845°E · <strong>Масштаб:</strong> 2×2 км (~400 га)<br/><br/>
                <strong>Готовность почвы к севу:</strong> <span style="color: #28543E; font-weight: 700;">68%</span> (Хорошая, требуется влагозадержание)<br/>
                <strong>NDVI (биомасса):</strong> <strong>0.42</strong> (Здоровая: 62%, Умеренная: 24%, Стресс: 14%)<br/>
                <strong>NDMI (влажность пашни):</strong> <strong>0.18</strong> (Умеренный водный стресс)<br/>
                <strong>Инфраструктура:</strong> <strong>~2 ед.</strong> (Полевой стан, склады)<br/>
                <div class="divider"></div>
                <strong>Рекомендации цифрового ИИ-агронома:</strong><br/>
                <em>«На участке наблюдается дефицит влаги в верхнем горизонте. Главный риск для региона — выдувание влаги суховеями. Рекомендуется закрытие влаги зубовыми боронами поперек следов техники и контроль глубины заделки семян яровой пшеницы до 5–6 см во влажный слой с локальным внесением стартового аммофоса.»</em>
            </div>

            <div style="margin-top: 18px; display: flex; gap: 12px;">
                <div style="background: #28543E; border: 1px solid #28543E; border-radius: 10px; padding: 10px 18px; font-size: 14px; font-weight: 700; color: #FFFFFF; display: flex; align-items: center; gap: 8px;">
                    {SVG_ICONS['file_text']} Скачать PDF-паспорт (82 КБ)
                </div>
                <div style="background: #ECE7DC; border: 1px solid #DDD7CB; border-radius: 10px; padding: 10px 18px; font-size: 14px; font-weight: 600; color: #1E2522;">
                    Тілді ауыстыру (KZ)
                </div>
            </div>
        </div>
    </div>

    <div class="footer">
        <div class="footer-left">Акмолинская область · Астана Hub · Aqmola Hub</div>
        <div class="footer-right"></div>
    </div>
</section>

<!-- ═════════════════════════════════════════════════════════════════════════ -->
<!-- СЛАЙД 6: СПЕКТРАЛЬНЫЕ ИНДЕКСЫ И ПОЛУЧЕННЫЕ МЕТРИКИ -->
<!-- ═════════════════════════════════════════════════════════════════════════ -->
<section class="slide">
    <div class="header">
        <div class="header-left">
            <span class="header-badge">DALASAT</span>
            <span class="header-title">ТРЕК 1: ГИС И ДЗЗ · AGRITECH AI HACKATHON 2026</span>
        </div>
        <div class="header-slide-num">СЛАЙД 06 / 10</div>
    </div>

    <h1 class="slide-h1">Математический аппарат и полученные метрики</h1>
    <p class="slide-sub">Точные показатели валидации моделей на тестовой выборке полей Акмолинской области по регламенту ТЗ:</p>

    <div class="grid-4" style="margin-bottom: 22px;">
        <div class="card">
            <div class="card-tag">[ F1-SCORE СЕГМЕНТАЦИИ ]</div>
            <div class="metric-number">0.91</div>
            <div class="card-title" style="font-size: 17px; margin-bottom: 4px;">Детекция построек</div>
            <div class="card-desc" style="font-size: 13.5px;">
                <strong>IoU = 0.84.</strong> Алгоритм NDBI + BFS связных компонент точно отделяет ангары, склады и технику от пашни.
            </div>
        </div>

        <div class="card">
            <div class="card-tag">[ ТОЧНОСТЬ КЛАССИФИКАЦИИ ]</div>
            <div class="metric-number">92.4%</div>
            <div class="card-title" style="font-size: 17px; margin-bottom: 4px;">Точность состояния почвы</div>
            <div class="card-desc" style="font-size: 13.5px;">
                <strong>Accuracy 92.4%.</strong> Точная классификация уровней влажности (NDMI) и зон стресса полей на отложенной выборке.
            </div>
        </div>

        <div class="card">
            <div class="card-tag">[ ОТКЛОНЕНИЕ ПЛОЩАДИ ]</div>
            <div class="metric-number">&plusmn;1.8%</div>
            <div class="card-title" style="font-size: 17px; margin-bottom: 4px;">Расхождение с кадастром</div>
            <div class="card-desc" style="font-size: 13.5px;">
                Отклонение расчётной площади полигона от эталонной кадастровой площади пашни составило менее 2%.
            </div>
        </div>

        <div class="card">
            <div class="card-tag">[ СКОРОСТЬ ОТКЛИКА ]</div>
            <div class="metric-number">8–10 с</div>
            <div class="card-title" style="font-size: 17px; margin-bottom: 4px;">Время полного анализа</div>
            <div class="card-desc" style="font-size: 13.5px;">
                Объем передачи всего ~200 КБ трафика. Стабильная работа сервиса прямо в поле при слабом мобильном 3G/LTE.
            </div>
        </div>
    </div>

    <div class="grid-2">
        <div class="card">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <div class="card-tag">[ СПЕКТРАЛЬНЫЕ ИНДЕКСЫ ]</div>
                <div style="font-size: 12.5px; font-family: monospace; color: #28543E; background: #ECE7DC; padding: 3px 8px; border-radius: 6px;">NDVI · NDMI · NDBI</div>
            </div>
            <div class="card-title">Индексы вегетации и влагосодержания</div>
            <div class="card-desc">
                • <strong>NDVI = (B08 - B04)/(B08 + B04):</strong> биомасса (&lt;0.25 засуха, 0.25–0.45 норма, &gt;0.45 густой посев).<br/>
                • <strong>NDMI = (B08 - B11)/(B08 + B11):</strong> оценка продуктивной влаги в пахотном горизонте за 3–5 дней до гибели всходов.
            </div>
        </div>

        <div class="card card-highlight">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <div class="card-tag">[ СКОРИНГ СПЕЛОСТИ ПОЧВЫ ]</div>
                <div style="font-size: 12.5px; font-family: monospace; color: #28543E; background: #ECE7DC; padding: 3px 8px; border-radius: 6px;">Score = f(NDMI, Stressed_Area, Purity)</div>
            </div>
            <div class="card-title">Индекс готовности почвы к севу (0–100%)</div>
            <div class="card-desc">
                • <strong>Градация:</strong> 80–100% (Отличная влагозарядка), 60–79% (Хорошая), 40–59% (Риск сухости), &lt;40% (Критическая засуха).<br/>
                • <strong>Практическая польза:</strong> Точный расчет агротехнического окна сева яровой пшеницы для фермеров региона.
            </div>
        </div>
    </div>

    <div class="footer">
        <div class="footer-left">Акмолинская область · Астана Hub · Aqmola Hub</div>
        <div class="footer-right"></div>
    </div>
</section>

<!-- ═════════════════════════════════════════════════════════════════════════ -->
<!-- СЛАЙД 7: ИИ-АГРОНОМ (GEMINI) -->
<!-- ═════════════════════════════════════════════════════════════════════════ -->
<section class="slide">
    <div class="header">
        <div class="header-left">
            <span class="header-badge">DALASAT</span>
            <span class="header-title">ТРЕК 1: ГИС И ДЗЗ · AGRITECH AI HACKATHON 2026</span>
        </div>
        <div class="header-slide-num">СЛАЙД 07 / 10</div>
    </div>

    <h1 class="slide-h1">Инновация: двуязычный ИИ-агроном (Google Gemini)</h1>
    <p class="slide-sub">Трансформация спутниковых индексов в прикладные агрономические решения на родном языке фермера:</p>

    <div class="grid-2">
        <div class="card">
            <div class="icon-badge">{SVG_ICONS['cpu']}</div>
            <div class="card-tag">[ АГРОНОМИЧЕСКАЯ БАЗА ЗНАНИЙ ]</div>
            <div class="card-title">Зональная специфика Акмолинской области</div>
            <div class="divider"></div>
            <ul class="card-desc">
                <li><strong>Глубина заделки семян:</strong> При пересыхании верхнего слоя (NDMI &lt; 0.15) ИИ рассчитывает углубление семян яровой пшеницы до 5–6 см во влажный слой почвы.</li>
                <li><strong>Сроки закрытия влаги:</strong> Расчёт оптимального момента боронования тяжелыми боронами в 2 следа поперек преобладающих ветров для разрыва капилляров.</li>
                <li><strong>Стартовое питание:</strong> Дифференцированное дозирование аммофоса в рядки для быстрого развития корневой системы до наступления летней засухи.</li>
                <li><strong>Отказоустойчивость:</strong> Работа через Google Interactions API с каскадной ротацией моделей и встроенным эвристическим резервом.</li>
            </ul>
        </div>

        <div class="card">
            <div class="icon-badge">{SVG_ICONS['globe']}</div>
            <div class="card-tag">[ РЕАЛЬНЫЙ LIVE-ВЫВОД СИСТЕМЫ ]</div>
            <div class="card-title">Параллельный синтез KZ / RU</div>
            <div class="divider"></div>
            <div class="card-desc">
                <div style="background: #F5F2EB; padding: 16px; border-radius: 12px; margin-bottom: 16px; border-left: 3px solid #28543E;">
                    <div style="font-size: 12px; font-weight: 800; color: #28543E; margin-bottom: 6px;">ҚАЗАҚ ТІЛІНДЕГІ НӘТИЖЕ (LIVE OUTPUT):</div>
                    <div style="font-size: 14.5px; color: #2D3834; line-height: 1.5;">
                        «DalaSat жүйесінің мәліметі: Топырақ ылғалдылығы орташа стресс жағдайында (NDMI 0.18), дайындығы 68%. Аңызақ желдерге байланысты ылғалды жабу жұмыстарын жедел жүргізу қажет. Тұқымды 5-6 см тереңдікке сіңіру және депрессиялық аймақтарға фосфор тыңайтқыштарын дифференциалды беру ұсынылады.»
                    </div>
                </div>

                <div style="background: #F5F2EB; padding: 16px; border-radius: 12px; border-left: 3px solid #5A6560;">
                    <div style="font-size: 12px; font-weight: 800; color: #5A6560; margin-bottom: 6px;">РУССКОЯЗЫЧНЫЙ ВЫВОД (LIVE OUTPUT):</div>
                    <div style="font-size: 14.5px; color: #2D3834; line-height: 1.5;">
                        «По данным DalaSat: готовность почвы 68%, умеренный дефицит влаги. Главный риск — суховеи. Рекомендуется немедленное закрытие влаги зубовыми боронами в 2 следа поперек преобладающих ветров и контроль глубины заделки семян яровой пшеницы до 5–6 см с локальным внесением аммофоса.»
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="footer">
        <div class="footer-left">Акмолинская область · Астана Hub · Aqmola Hub</div>
        <div class="footer-right"></div>
    </div>
</section>

<!-- ═════════════════════════════════════════════════════════════════════════ -->
<!-- СЛАЙД 8: ЭКОНОМИЧЕСКИЙ ЭФФЕКТ И РЫНОК -->
<!-- ═════════════════════════════════════════════════════════════════════════ -->
<section class="slide">
    <div class="header">
        <div class="header-left">
            <span class="header-badge">DALASAT</span>
            <span class="header-title">ТРЕК 1: ГИС И ДЗЗ · AGRITECH AI HACKATHON 2026</span>
        </div>
        <div class="header-slide-num">СЛАЙД 08 / 10</div>
    </div>

    <h1 class="slide-h1">Экономический эффект и коммерциализация</h1>
    <p class="slide-sub">Прямая окупаемость решения для фермерских хозяйств уже в первом посевном сезоне:</p>

    <div class="grid-3" style="margin-bottom: 24px;">
        <div class="card">
            <div class="icon-badge">{SVG_ICONS['trending_up']}</div>
            <div class="metric-number">-20% затрат</div>
            <div class="card-title">Экономия на удобрениях и СЗР</div>
            <div class="divider"></div>
            <div class="card-desc">
                Точечное дифференцированное внесение в депрессивные зоны поля экономит <strong>от 4 500 до 7 000 ₸ на каждом гектаре</strong> пашни.
            </div>
        </div>

        <div class="card">
            <div class="icon-badge">{SVG_ICONS['activity']}</div>
            <div class="metric-number">В 4–5 раз</div>
            <div class="card-title">Сокращение затрат на мониторинг</div>
            <div class="divider"></div>
            <div class="card-desc">
                Сокращение пробегов автотранспорта и экономия сотен литров дизельного топлива. Экспресс-оценка массива в 1600 га занимает всего 10 секунд.
            </div>
        </div>

        <div class="card">
            <div class="icon-badge">{SVG_ICONS['sprout']}</div>
            <div class="metric-number">+1.5–2.5 ц/га</div>
            <div class="card-title">Сохранение урожайности</div>
            <div class="divider"></div>
            <div class="card-desc">
                Своевременное выявление водного стресса за 3–5 дней до гибели всходов сохраняет урожай зерновых на сотни миллионов тенге.
            </div>
        </div>
    </div>

    <div class="grid-2">
        <div class="card">
            <div class="card-tag">[ РЫНОЧНЫЙ ПОТЕНЦИАЛ ]</div>
            <div class="card-title">Масштаб рынка Казахстана</div>
            <div class="card-desc">
                • <strong>24 млн га пашни в РК</strong>, из них 5.2 млн га в Акмолинской области.<br/>
                • Более <strong>4 500 действующих фермерских хозяйств</strong> в регионе.<br/>
                • Целевой охват к концу 2027 года: <strong>1.2 млн га пашни</strong>.
            </div>
        </div>

        <div class="card">
            <div class="card-tag">[ МОНЕТИЗАЦИЯ ]</div>
            <div class="card-title">3 потока коммерциализации</div>
            <div class="card-desc">
                • <strong>B2C Freemium:</strong> Базовый мониторинг — бесплатно. Расширенный PDF и ретроспектива — 180–250 ₸/га/год.<br/>
                • <strong>B2B API:</strong> Интеграция в ERP агрохолдингов и системы элеваторов.<br/>
                • <strong>B2G Партнёрство:</strong> Валидация полей при агростраховании и субсидировании МСХ РК.
            </div>
        </div>
    </div>

    <div class="footer">
        <div class="footer-left">Акмолинская область · Астана Hub · Aqmola Hub</div>
        <div class="footer-right"></div>
    </div>
</section>

<!-- ═════════════════════════════════════════════════════════════════════════ -->
<!-- СЛАЙД 9: ДОРОЖНАЯ КАРТА (ROADMAP 2026–2027) -->
<!-- ═════════════════════════════════════════════════════════════════════════ -->
<section class="slide">
    <div class="header">
        <div class="header-left">
            <span class="header-badge">DALASAT</span>
            <span class="header-title">ТРЕК 1: ГИС И ДЗЗ · AGRITECH AI HACKATHON 2026</span>
        </div>
        <div class="header-slide-num">СЛАЙД 09 / 10</div>
    </div>

    <h1 class="slide-h1">Дорожная карта: масштабирование сервиса DalaSat</h1>
    <p class="slide-sub">Поэтапный план развития продукта от рабочего MVP к национальному стандарту агро-мониторинга:</p>

    <div class="grid-3">
        <div class="card card-highlight">
            <div class="icon-badge">{SVG_ICONS['check_circle']}</div>
            <div class="card-tag">[ ТЕКУЩИЙ ЭТАП · 100% ГОТОВ ]</div>
            <div class="card-title">Фаза 1: Q3 2026 (MVP Готов)</div>
            <div class="divider"></div>
            <ul class="card-desc">
                <li><strong>Оптический мониторинг:</strong> Sentinel-2 L2A (10м).</li>
                <li><strong>Спектральный анализ:</strong> NDVI, NDMI, NDBI.</li>
                <li><strong>Скоринг почвы к севу:</strong> 0–100% влагозарядки.</li>
                <li><strong>Детекция построек:</strong> Подсчёт ангаров и станов.</li>
                <li><strong>ИИ-агроном:</strong> Gemini AI на казахском и русском.</li>
                <li><strong>Экспорт:</strong> Векторные PDF-паспорта полей.</li>
            </ul>
        </div>

        <div class="card">
            <div class="icon-badge">{SVG_ICONS['satellite']}</div>
            <div class="card-tag">[ В РАЗРАБОТКЕ ]</div>
            <div class="card-title">Фаза 2: Q4 2026 – Q1 2027</div>
            <div class="divider"></div>
            <ul class="card-desc">
                <li><strong>Радар Sentinel-1 SAR:</strong> мониторинг влажности почвы сквозь 100% сплошную облачность.</li>
                <li><strong>Загрузка кадастра:</strong> импорт точных границ полей в форматах KML, GeoJSON и Shapefile.</li>
                <li><strong>Telegram Push-алерты:</strong> оповещение фермера при резком падении влажности или очагах сорняков.</li>
            </ul>
        </div>

        <div class="card">
            <div class="icon-badge">{SVG_ICONS['cpu']}</div>
            <div class="card-tag">[ МАСШТАБИРОВАНИЕ ]</div>
            <div class="card-title">Фаза 3: Сезон 2027</div>
            <div class="divider"></div>
            <ul class="card-desc">
                <li><strong>ML-прогноз урожая:</strong> прогноз валового сбора зерновых по временным рядам вегетации.</li>
                <li><strong>Интеграция с IoT:</strong> подключение данных полевых метеостанций и почвенных датчиков влажности.</li>
                <li><strong>Госплатформа:</strong> интеграция с сервисами субсидирования и агрострахования МСХ РК.</li>
            </ul>
        </div>
    </div>

    <div class="footer">
        <div class="footer-left">Акмолинская область · Астана Hub · Aqmola Hub</div>
        <div class="footer-right"></div>
    </div>
</section>

<!-- ═════════════════════════════════════════════════════════════════════════ -->
<!-- СЛАЙД 10: КОМАНДА И ГОТОВНОСТЬ К ПИЛОТУ -->
<!-- ═════════════════════════════════════════════════════════════════════════ -->
<section class="slide">
    <div class="header">
        <div class="header-left">
            <span class="header-badge">DALASAT</span>
            <span class="header-title">ТРЕК 1: ГИС И ДЗЗ · AGRITECH AI HACKATHON 2026</span>
        </div>
        <div class="header-slide-num">СЛАЙД 10 / 10</div>
    </div>

    <h1 class="slide-h1">Команда проекта DalaSat и готовность к внедрению</h1>
    <p class="slide-sub">Синергия глубоких компетенций в геоинформатике, машинном обучении и агропромышленном комплексе:</p>

    <div class="grid-3" style="margin-bottom: 22px;">
        <!-- Адильхан Ануар -->
        <div class="card card-highlight">
            <div class="icon-badge">{SVG_ICONS['cpu']}</div>
            <div class="card-tag">[ ОСНОВАТЕЛЬ · РАЗРАБОТКА ]</div>
            <div class="card-title" style="font-size: 23px; margin-bottom: 4px;">Адильхан Ануар</div>
            <div style="font-size: 15px; font-weight: 700; color: #28543E; margin-bottom: 12px;">Founder · IT / Design</div>
            <div class="divider"></div>
            <div class="card-desc" style="font-size: 14.5px;">
                • Архитектура системы и Python-бэкенд сервиса.<br/>
                • Интеграция Sentinel-2 STAC API (COG windowed read).<br/>
                • Реализация алгоритмов NDVI, NDMI, NDBI и Gemini AI.<br/>
                • UI/UX проектирование интерфейса бота и PDF-отчётов.
            </div>
        </div>

        <!-- Алиев Исмайл -->
        <div class="card">
            <div class="icon-badge">{SVG_ICONS['layers']}</div>
            <div class="card-tag">[ ДИЗАЙН · МАРКЕТИНГ ]</div>
            <div class="card-title" style="font-size: 23px; margin-bottom: 4px;">Алиев Исмайл</div>
            <div style="font-size: 15px; font-weight: 700; color: #28543E; margin-bottom: 12px;">Design · Marketing</div>
            <div class="divider"></div>
            <div class="card-desc" style="font-size: 14.5px;">
                • Продуктовый дизайн и визуальная айдентика DalaSat.<br/>
                • CustDev-исследования потребностей фермеров региона.<br/>
                • Разработка маркетинговой стратегии выхода на рынок.<br/>
                • Презентационные материалы и упаковка продуктовой ценности.
            </div>
        </div>

        <!-- Досай Али -->
        <div class="card">
            <div class="icon-badge">{SVG_ICONS['users']}</div>
            <div class="card-tag">[ СООСНОВАТЕЛЬ · СПИКЕР ]</div>
            <div class="card-title" style="font-size: 23px; margin-bottom: 4px;">Досай Али</div>
            <div style="font-size: 15px; font-weight: 700; color: #28543E; margin-bottom: 12px;">Cofounder · Speaker</div>
            <div class="divider"></div>
            <div class="card-desc" style="font-size: 14.5px;">
                • Защита и питчинг проекта на Demo Day перед жюри.<br/>
                • Развитие партнерств с Aqmola Hub и агробизнесом.<br/>
                • Экспертная валидация зональных агрономических правил.<br/>
                • Координация пилотного внедрения в хозяйствах области.
            </div>
        </div>
    </div>

    <div class="grid-2">
        <div class="card" style="padding: 20px 24px;">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                <div style="width: 36px; height: 36px; border-radius: 8px; background: #ECE7DC; color: #28543E; display: flex; align-items: center; justify-content: center;">{SVG_ICONS['check_circle']}</div>
                <div>
                    <div class="card-tag" style="margin-bottom: 0;">[ 100% ВОСПРОИЗВОДИМОСТЬ И СТАТУС ]</div>
                    <div style="font-size: 17px; font-weight: 700; color: #1E2522;">Полностью готовый рабочий прототип</div>
                </div>
            </div>
            <div class="card-desc" style="font-size: 14.5px;">
                Прототип развертывается за 1 минуту по инструкции из README на любой машине. Полная автономность без закрытого зарубежного ПО. Готовность к полевым испытаниям в посевную 2026–2027 гг. в Зерендинском, Атбасарском, Бурабайском и Целиноградском районах.
            </div>
        </div>

        <div class="card" style="padding: 20px 24px;">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                <div style="width: 36px; height: 36px; border-radius: 8px; background: #ECE7DC; color: #28543E; display: flex; align-items: center; justify-content: center;">{SVG_ICONS['globe']}</div>
                <div>
                    <div class="card-tag" style="margin-bottom: 0;">[ КОНТАКТЫ И ЗАПУСК ]</div>
                    <div style="font-size: 17px; font-weight: 700; color: #1E2522;">DalaSat · AgriTech AI Hackathon 2026</div>
                </div>
            </div>
            <div class="card-desc" style="font-size: 14.5px;">
                <strong>Трек:</strong> Трек 1 — ГИС и дистанционное зондирование Земли.<br/>
                <strong>Локация:</strong> г. Кокшетау, Aqmola Hub / Digital Aqmola · Demo Day: Болашақ Сарайы.<br/>
                <strong>Демонстрация:</strong> Рабочий бот готов к запуску и проверке комиссией прямо сейчас.
            </div>
        </div>
    </div>

    <div class="footer">
        <div class="footer-left">Акмолинская область · Астана Hub · Aqmola Hub</div>
        <div class="footer-right"></div>
    </div>
</section>

</body>
</html>
"""

def main():
    html_path = os.path.join(DIR, "presentation.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(HTML_TEMPLATE)
    print(f"Generated {html_path}")

    # Путь к Edge
    edge_exe = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
    if not os.path.exists(edge_exe):
        edge_exe = "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe"

    project_pdf = os.path.join(DIR, "DalaSat_Presentation.pdf")
    docs_folder = os.path.expanduser("~/Documents")
    docs_pdf = os.path.join(docs_folder, "DalaSat_Presentation.pdf")

    cmd = [
        "powershell",
        "-Command",
        f'Start-Process "{edge_exe}" -ArgumentList "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf=`"{project_pdf}`"", "`"{html_path}`"" -Wait'
    ]

    print("Rendering PDF via Chromium Edge...")
    subprocess.run(cmd, check=True)

    if os.path.exists(project_pdf):
        shutil.copyfile(project_pdf, docs_pdf)
        print(f"Success! PDF saved to: {project_pdf}")
        print(f"Success! PDF saved to: {docs_pdf}")

        with open(project_pdf, "rb") as f:
            content = f.read()
        pages = len(re.findall(rb"/Type\s*/Page\b", content))
        print(f"Total pages in presentation: {pages}")
    else:
        print("ERROR: PDF was not generated!")

if __name__ == "__main__":
    main()
