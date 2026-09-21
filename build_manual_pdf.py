"""
build_manual_pdf.py
Генерация официальной инструкции по локальному запуску DalaSat в формате PDF (A4).
Для экспертной комиссии хакатона «AgriTech AI Hackathon» (Aqmola Hub / Digital Aqmola).
Рендеринг через движок Chromium (Edge headless) для безупречной векторной верстки.
"""

import os
import shutil
import subprocess
import re

DIR = os.path.dirname(os.path.abspath(__file__))

HTML_CONTENT = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>DalaSat — Инструкция по локальному запуску</title>
<style>
@page {
    size: A4 portrait;
    margin: 18mm 18mm 18mm 18mm;
    @bottom-right {
        content: counter(page);
    }
}
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #1E2522;
    background: #FFFFFF;
    line-height: 1.5;
    font-size: 13.5px;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
}

/* Верхняя шапка документа */
.doc-header {
    background: #F5F2EB;
    border: 1.5px solid #DDD7CB;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 24px;
}
.badge {
    display: inline-block;
    background: #28543E;
    color: #FFFFFF;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1px;
    padding: 4px 10px;
    border-radius: 5px;
    margin-bottom: 8px;
    text-transform: uppercase;
}
.doc-title {
    font-size: 22px;
    font-weight: 800;
    color: #1E2522;
    line-height: 1.25;
    margin-bottom: 6px;
}
.doc-sub {
    font-size: 13px;
    color: #5A6560;
}

/* Заголовки разделов */
h2 {
    font-size: 16px;
    font-weight: 800;
    color: #28543E;
    border-bottom: 1.5px solid #EAE5D9;
    padding-bottom: 6px;
    margin-top: 22px;
    margin-bottom: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
h3 {
    font-size: 14px;
    font-weight: 700;
    color: #1E2522;
    margin-top: 14px;
    margin-bottom: 6px;
}

p, li {
    color: #2D3834;
    font-size: 13px;
    line-height: 1.55;
}
ul, ol {
    margin-left: 20px;
    margin-bottom: 10px;
}
li {
    margin-bottom: 4px;
}
strong {
    color: #1E2522;
}

/* Таблицы */
table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 16px;
    font-size: 12.5px;
}
th, td {
    border: 1px solid #DDD7CB;
    padding: 8px 12px;
    text-align: left;
    vertical-align: top;
}
th {
    background: #F5F2EB;
    color: #28543E;
    font-weight: 700;
}
tr:nth-child(even) td {
    background: #FAF9F6;
}

/* Кодовые блоки */
pre, code {
    font-family: "Consolas", "Courier New", monospace;
}
pre {
    background: #F5F2EB;
    border: 1px solid #DDD7CB;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 12px;
    line-height: 1.45;
    color: #1E2522;
    margin: 8px 0 12px 0;
    white-space: pre-wrap;
    word-break: break-all;
}
p code {
    background: #F5F2EB;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 12px;
    color: #28543E;
    border: 1px solid #DDD7CB;
}

/* Информационные плашки */
.callout {
    background: #F5F2EB;
    border-left: 4px solid #28543E;
    padding: 10px 14px;
    border-radius: 0 8px 8px 0;
    margin: 10px 0 14px 0;
    font-size: 12.5px;
}
.callout strong {
    color: #28543E;
}

.page-break {
    page-break-before: always;
}
</style>
</head>
<body>

<div class="doc-header">
    <div class="badge">AgriTech AI Hackathon 2026 · Aqmola Hub · Digital Aqmola</div>
    <div class="doc-title">DalaSat — Инструкция по локальному запуску прототипа</div>
    <div class="doc-sub">Официальное руководство для экспертной комиссии по проверке воспроизводимости решения на чистой машине</div>
</div>

<h2>1. Общие сведения о проекте и команде</h2>
<table>
    <tr>
        <th style="width: 28%;">Параметр</th>
        <th>Значение</th>
    </tr>
    <tr>
        <td><strong>Название проекта</strong></td>
        <td><strong>DalaSat</strong> (Спутниковый экспресс-мониторинг полей и цифровой ИИ-агроном)</td>
    </tr>
    <tr>
        <td><strong>Выбранный трек</strong></td>
        <td><strong>Трек 1. GIS и дистанционное зондирование Земли</strong></td>
    </tr>
    <tr>
        <td><strong>Хакатон и организатор</strong></td>
        <td>AI-хакатон «AgriTech AI Hackathon», г. Кокшетау · Акмолинский филиал АКФ «Астана Хаб» (Aqmola Hub) при поддержке Управления цифровизации и архивов Акмолинской области (Digital Aqmola)</td>
    </tr>
    <tr>
        <td><strong>Состав команды</strong></td>
        <td>
            • <strong>Адильхан Ануар</strong> — Founder · IT / Design<br/>
            • <strong>Алиев Исмайл</strong> — Design · Marketing<br/>
            • <strong>Досай Али</strong> — Cofounder · Speaker
        </td>
    </tr>
    <tr>
        <td><strong>Ожидаемый результат по ТЗ</strong></td>
        <td>Telegram-бот со слоями спутниковых индексов Sentinel-2 L2A (NDVI, NDMI), историей поля, детекцией объектов инфраструктуры (NDBI) и выгрузкой отчёта в PDF</td>
    </tr>
</table>

<h2>2. Системные требования</h2>
<ul>
    <li><strong>Операционная система:</strong> Windows 10/11, macOS (Intel / Apple Silicon) или Linux (Ubuntu 20.04+).</li>
    <li><strong>Интерпретатор Python:</strong> версия 3.10, 3.11 или 3.12 (рекомендуется Python 3.11/3.12).</li>
    <li><strong>Оперативная память:</strong> от 2 ГБ RAM (система крайне легковесна благодаря технологии оконного чтения COG — скачивается всего ~200 КБ вместо 800 МБ).</li>
    <li><strong>Дисковое пространство:</strong> ~350 МБ для виртуального окружения и зависимостей.</li>
    <li><strong>Сетевое подключение:</strong> доступ в интернет для взаимодействия с Microsoft Planetary Computer STAC API, Telegram API и Google Gemini API.</li>
</ul>

<h2>3. Пошаговая инструкция запуска «с нуля»</h2>

<h3>Шаг 1. Клонирование репозитория</h3>
<pre>git clone https://github.com/adilhan385/dalasat.git
cd dalasat</pre>

<h3>Шаг 2. Создание и активация виртуального окружения</h3>
<pre># Создание окружения:
python -m venv .venv

# Активация на Windows (PowerShell / CMD):
.venv\Scripts\activate

# Активация на macOS / Linux:
source .venv/bin/activate</pre>

<h3>Шаг 3. Установка библиотек</h3>
<pre>pip install --upgrade pip
pip install -r requirements.txt</pre>

<div class="callout">
    <strong>Примечание:</strong> Все библиотеки (aiogram, pystac-client, planetary-computer, rasterio, reportlab, shapely, google-genai) имеют готовые скомпилированные бинарные пакеты (wheels) под Windows, macOS и Linux, поэтому установка проходит без необходимости ручной сборки C++ компилятором.
</div>

<div class="page-break"></div>

<h2>3. Пошаговая инструкция запуска (продолжение)</h2>

<h3>Шаг 4. Настройка переменных окружения (.env)</h3>
<p>В корне проекта создайте файл <code>.env</code> (или скопируйте шаблон <code>.env.example</code>):</p>
<pre>TELEGRAM_BOT_TOKEN=8800586784:AAH...ваш_токен_бота...
GEMINI_API_KEY=AIzaSy...ваш_api_ключ_gemini...</pre>

<p><strong>Пояснения по ключам:</strong></p>
<ol>
    <li><strong>Telegram Bot Token:</strong> Получается за 30 секунд в Telegram у официального бота <code>@BotFather</code> командой <code>/newbot</code>.</li>
    <li><strong>Gemini API Key:</strong> Бесплатно создается в Google AI Studio (<code>aistudio.google.com</code>) по кнопке «Get API key». В проекте реализован отказоустойчивый нативный Interactions API с каскадной ротацией моделей (<code>gemini-3.5-flash-lite</code>). При временном отсутствии ключа бот автоматически переходит на встроенный экспертный агрономический резерв.</li>
    <li><strong>Спутниковые данные Sentinel-2 L2A:</strong> Не требуют ключей или платных подписок. Доступ осуществляется напрямую через открытый каталог Microsoft Planetary Computer STAC API.</li>
</ol>

<h3>Шаг 5. Запуск Telegram-бота</h3>
<pre>python bot.py</pre>
<p>В терминале появится подтверждающий лог успешного старта:</p>
<pre>INFO | __main__ | 🌾 DalaSat Bot успешно запущен и готов к приёму координат!</pre>

<h2>4. Контрольный сквозной сценарий тестирования для эксперта</h2>
<p>Члены экспертной комиссии могут проверить работоспособность решения за 1 минуту по следующему чек-листу:</p>
<ol>
    <li>Откройте Telegram и запустите бота командой <code>/start</code>.</li>
    <li>Выберите язык: <strong>Русский (RU)</strong> или <strong>Казахский (KZ)</strong>.</li>
    <li>Выберите масштаб участка: например, <strong>«🌾 Стандартный (2×2 км, ~400 га)»</strong>.</li>
    <li>Отправьте координаты реального зернового поля в Акмолинской области. Нажмите кнопку «📍 Отправить геопозицию» со смартфона или просто отправьте текстом:
        <pre style="margin: 6px 0; padding: 6px 12px; font-weight: bold; color: #28543E;">53.2514, 69.1845</pre>
        <em>(Это реальный массив пашни в Зерендинском районе Акмолинской области).</em>
    </li>
    <li><strong>Обработка (8–10 секунд):</strong> Бот связывается с группировкой Sentinel-2, нормализует спектральные каналы B04, B08, B11, рассчитывает матрицы NDVI и NDMI, находит постройки алгоритмом NDBI + BFS и формирует вердикт Gemini AI.</li>
    <li><strong>Оценка ответа:</strong> В чат поступает цветная тепловая карта поля со шкалой вегетации, готовность почвы к севу (68%), степень влажности, количество построек (~2 ед.) и зональные агрономические советы (глубина заделки семян 5–6 см, боронование в 2 следа поперек ветра).</li>
    <li><strong>Проверка PDF:</strong> Нажмите инлайн-кнопку <strong>«📄 Скачать PDF-паспорт»</strong>. Бот мгновенно отправит официальный PDF-отчет с картой и таблицей метрик.</li>
</ol>

<h2>5. Архитектура модулей проекта</h2>
<table>
    <tr>
        <th style="width: 32%;">Файл / Модуль</th>
        <th>Назначение</th>
    </tr>
    <tr>
        <td><code>bot.py</code></td>
        <td>Главный файл Telegram-бота на Aiogram 3 (маршрутизация команд, геолокация, мультиязычность).</td>
    </tr>
    <tr>
        <td><code>config.py</code></td>
        <td>Конфигурация системы: дельты масштабов полей (1×1, 2×2, 4×4 км), пороги спектральных индексов.</td>
    </tr>
    <tr>
        <td><code>services/satellite_service.py</code></td>
        <td>Клиент STAC API Microsoft Planetary Computer. Скачивание тайлов Sentinel-2 L2A через COG windowed read.</td>
    </tr>
    <tr>
        <td><code>services/gis_service.py</code></td>
        <td>Расчет матриц NDVI, NDMI, скоринга влагозарядки почвы и генерация цветных растровых карт.</td>
    </tr>
    <tr>
        <td><code>services/building_detector.py</code></td>
        <td>Детекция инфраструктуры (полевые станы, склады, ангары) на базе NDBI и алгоритма связности BFS.</td>
    </tr>
    <tr>
        <td><code>services/ai_advisor.py</code></td>
        <td>Интеллектуальный агроном на Google Gemini Interactions API с зональной базой знаний Акмолинской области.</td>
    </tr>
    <tr>
        <td><code>services/pdf_generator.py</code></td>
        <td>Генератор векторных официальных PDF-паспортов полей на ReportLab.</td>
    </tr>
</table>

<h2>6. Диагностика неполадок (Troubleshooting)</h2>
<ul>
    <li><strong>Ошибка «TelegramUnauthorizedError»:</strong> Проверьте правильность токена в файле <code>.env</code>. Убедитесь, что токен скопирован полностью из <code>@BotFather</code> без лишних пробелов.</li>
    <li><strong>Лимиты Gemini API:</strong> В модуле <code>ai_advisor.py</code> встроен автоматический fallback. При исчерпании квоты бот не прерывает работу, а выдает точные экспертные зональные правила из внутренней базы.</li>
    <li><strong>Обновление SAS-токенов Planetary Computer:</strong> Ссылки на снимки Sentinel-2 автоматически подписываются функцией <code>planetary_computer.sign_url()</code>. Достаточно стабильного интернет-соединения.</li>
</ul>

<div style="margin-top: 30px; border-top: 1px solid #DDD7CB; padding-top: 12px; font-size: 11.5px; color: #727C77; display: flex; justify-content: space-between;">
    <span>DalaSat · AgriTech AI Hackathon 2026 · Aqmola Hub / Digital Aqmola</span>
    <span>г. Кокшетау, 17–23 сентября 2026 г.</span>
</div>

</body>
</html>
"""

def main():
    html_path = os.path.join(DIR, "manual.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(HTML_CONTENT)
    print(f"Generated {html_path}")

    edge_exe = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
    if not os.path.exists(edge_exe):
        edge_exe = "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe"

    project_pdf = os.path.join(DIR, "DalaSat_Инструкция_по_запуску.pdf")
    docs_folder = os.path.expanduser("~/Documents")
    docs_pdf = os.path.join(docs_folder, "DalaSat_Инструкция_по_запуску.pdf")

    cmd = [
        "powershell",
        "-Command",
        f'Start-Process "{edge_exe}" -ArgumentList "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf=`"{project_pdf}`"", "`"{html_path}`"" -Wait'
    ]

    print("Rendering manual PDF via Chromium Edge...")
    subprocess.run(cmd, check=True)

    if os.path.exists(project_pdf):
        shutil.copyfile(project_pdf, docs_pdf)
        print(f"Success! Manual PDF saved to:")
        print(f"1. Project: {project_pdf}")
        print(f"2. Documents: {docs_pdf}")
    else:
        print("ERROR: PDF was not generated!")

if __name__ == "__main__":
    main()
