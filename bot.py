"""
bot.py
Главный файл Telegram-бота «DalaSat».
Фреймворк: aiogram 3.x (асинхронный).
Поддерживает выбор языка (каз/рус) и масштаба поля (1x1 км, 2x2 км, 4x4 км).
"""

import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"

import asyncio
import logging
import io
import re
from typing import Dict

from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatAction, ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BufferedInputFile,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import TELEGRAM_BOT_TOKEN, SCALE_PROFILES, DEFAULT_SCALE
from services.satellite import fetch_sentinel2
from services.indices import calculate_indices
from services.visualizer import generate_ndvi_map
from services.ai_advisor import get_agronomic_advice
from services.pdf_generator import generate_field_passport

# ── Логгирование ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# Регулярка для быстрого перехвата координат в тексте (например: 53.2514, 69.1845)
COORD_PATTERN = re.compile(r"^\s*([0-9]{2}(?:\.[0-9]+)?)[,\s;]+([0-9]{2}(?:\.[0-9]+)?)\s*$")

# ── Кэш и настройки пользователей ───────────────────────────────────────────
_analysis_cache: Dict[int, Dict] = {}
_user_prefs: Dict[int, Dict] = {}


def get_user_pref(user_id: int) -> Dict:
    """Возвращает настройки пользователя (язык и масштаб)."""
    if user_id not in _user_prefs:
        _user_prefs[user_id] = {
            "lang": "ru",
            "scale": DEFAULT_SCALE,
        }
    return _user_prefs[user_id]


# ── FSM состояния ─────────────────────────────────────────────────────────────
class FieldForm(StatesGroup):
    waiting_for_coordinates = State()


router = Router()


# ── Клавиатуры ───────────────────────────────────────────────────────────────

def get_main_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    """Главная клавиатура на выбранном языке."""
    if lang == "kz":
        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(
                        text="📍 Алқабымды тексеру (GPS)",
                        request_location=True,
                    )
                ],
                [
                    KeyboardButton(text="🌾 Сынақ алқабы (Зеренді)"),
                    KeyboardButton(text="✏️ Координаттарды енгізу"),
                ],
                [
                    KeyboardButton(text="🔍 Масштабты таңдау"),
                    KeyboardButton(text="🌐 Тілді өзгерту / Сменить язык"),
                ],
                [
                    KeyboardButton(text="ℹ️ Анықтама")
                ],
            ],
            resize_keyboard=True,
            one_time_keyboard=False,
        )
    else:
        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(
                        text="📍 Проверить моё поле (GPS)",
                        request_location=True,
                    )
                ],
                [
                    KeyboardButton(text="🌾 Тестовое поле (Зеренда)"),
                    KeyboardButton(text="✏️ Ввести координаты вручную"),
                ],
                [
                    KeyboardButton(text="🔍 Выбрать масштаб поля"),
                    KeyboardButton(text="🌐 Сменить язык / Тілді өзгерту"),
                ],
                [
                    KeyboardButton(text="ℹ️ Справка / Инструкция")
                ],
            ],
            resize_keyboard=True,
            one_time_keyboard=False,
        )


def get_lang_inline_keyboard() -> InlineKeyboardMarkup:
    """Inline-кнопки выбора языка."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="lang:kz"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
            ]
        ]
    )


def get_scale_inline_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Inline-кнопки выбора масштаба поля."""
    buttons = []
    for key, val in SCALE_PROFILES.items():
        text = val["label_kz"] if lang == "kz" else val["label_ru"]
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"scale:{key}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_pdf_keyboard(user_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """Inline-кнопка для скачивания PDF-паспорта."""
    btn_text = "📄 PDF-төлқұжатты жүктеу" if lang == "kz" else "📄 Скачать PDF-паспорт поля"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=btn_text, callback_data=f"pdf:{user_id}")]
        ]
    )


# ── Хендлеры стартовых команд ───────────────────────────────────────────────

@router.message(CommandStart())
async def handle_start(message: Message, state: FSMContext) -> None:
    """Приветствие и выбор языка."""
    await state.clear()
    prefs = get_user_pref(message.from_user.id)
    lang = prefs["lang"]

    if lang == "kz":
        text = (
            "🌾 <b>DalaSat Bot</b> — ЖИ негізіндегі спутниктік агроном\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Алқаптарды Sentinel-2 спутнигінен жедел мониторингтеу және топырақтың егуге дайындығын бағалау қызметіне қош келдіңіз!\n\n"
            "📡 <b>Бот мүмкіндіктері:</b>\n"
            "• 🌱 Топырақтың егуге дайындығы мен ылғал қорын бағалау (0–100%)\n"
            "• 🟢 NDVI және NDMI вегетациялық индекстерін есептеу\n"
            "• 🗺 Жоғары ажыратымдылықтағы жылу картасы\n"
            "• 🤖 Gemini ЖИ-агрономынан нақты кеңестер\n"
            "• 📄 Ресми PDF-төлқұжат\n\n"
            "💡 <i>Компьютерден кірсеңіз: «🌾 Сынақ алқабы» түймесін басыңыз немесе координаттарды жазыңыз (мысалы: <code>53.2514, 69.1845</code>).</i>"
        )
    else:
        text = (
            "🌾 <b>DalaSat Bot</b> — Спутниковый ИИ-агроном\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Добро пожаловать в систему экспресс-мониторинга полей по снимкам Sentinel-2 и оценки готовности почвы к посадке!\n\n"
            "📡 <b>Что умеет сервис:</b>\n"
            "• 🌱 Оценка влагозарядки и пригодности почвы к севу (0–100%)\n"
            "• 🟢 Расчёт индексов биомассы NDVI и влажности NDMI\n"
            "• 🗺 Спутниковая теплокарта проблемных зон поля\n"
            "• 🤖 Персональные рекомендации от ИИ-агронома\n"
            "• 📄 Официальный PDF-паспорт мониторинга поля\n\n"
            "💡 <i>Если вы с компьютера: нажмите «🌾 Тестовое поле» или отправьте координаты текстом (например: <code>53.2514, 69.1845</code>).</i>"
        )

    await message.answer(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_keyboard(lang),
    )


# ── Смена языка ─────────────────────────────────────────────────────────────

@router.message(Command("lang"))
@router.message(Command("language"))
@router.message(F.text.in_(["🌐 Сменить язык / Тілді өзгерту", "🌐 Тілді өзгерту / Сменить язык"]))
async def handle_lang_prompt(message: Message) -> None:
    """Показывает меню смены языка."""
    await message.answer(
        "🌐 <b>Тілді таңдаңыз / Выберите язык интерфейса:</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=get_lang_inline_keyboard(),
    )


@router.callback_query(F.data.startswith("lang:"))
async def handle_lang_callback(callback: CallbackQuery) -> None:
    """Сохраняет выбранный язык."""
    lang = callback.data.split(":")[1]
    user_id = callback.from_user.id
    prefs = get_user_pref(user_id)
    prefs["lang"] = lang

    await callback.answer()
    if lang == "kz":
        await callback.message.answer(
            "✅ <b>Тіл қазақшаға ауыстырылды!</b>\nЕнді барлық есептер мен ЖИ кеңестері қазақ тілінде беріледі.",
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_keyboard("kz"),
        )
    else:
        await callback.message.answer(
            "✅ <b>Язык переключён на русский!</b>\nТеперь все отчёты и советы ИИ будут выдаваться на русском языке.",
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_keyboard("ru"),
        )


# ── Выбор масштаба ──────────────────────────────────────────────────────────

@router.message(Command("scale"))
@router.message(F.text.in_(["🔍 Выбрать масштаб поля", "🔍 Масштабты таңдау"]))
async def handle_scale_prompt(message: Message) -> None:
    """Показывает меню выбора масштаба поля."""
    prefs = get_user_pref(message.from_user.id)
    lang = prefs["lang"]
    current = prefs["scale"]
    label = SCALE_PROFILES[current]["label_kz"] if lang == "kz" else SCALE_PROFILES[current]["label_ru"]

    if lang == "kz":
        text = (
            f"🔍 <b>Алқап масштабын таңдаңыз:</b>\n"
            f"Қазіргі масштаб: <b>{label}</b>\n\n"
            "Спутниктік сканерлеу аумағының өлшемін көрсетіңіз:"
        )
    else:
        text = (
            f"🔍 <b>Выберите масштаб поля:</b>\n"
            f"Текущий масштаб: <b>{label}</b>\n\n"
            "Укажите размер площади для спутникового снимка:"
        )

    await message.answer(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_scale_inline_keyboard(lang),
    )


@router.callback_query(F.data.startswith("scale:"))
async def handle_scale_callback(callback: CallbackQuery) -> None:
    """Сохраняет выбранный масштаб."""
    scale = callback.data.split(":")[1]
    if scale not in SCALE_PROFILES:
        return
    user_id = callback.from_user.id
    prefs = get_user_pref(user_id)
    prefs["scale"] = scale
    lang = prefs["lang"]
    label = SCALE_PROFILES[scale]["label_kz"] if lang == "kz" else SCALE_PROFILES[scale]["label_ru"]

    await callback.answer()
    if lang == "kz":
        await callback.message.answer(
            f"✅ <b>Масштаб орнатылды:</b> {label}\nКелесі талдауда осы аумақ қамтылады.",
            parse_mode=ParseMode.HTML,
        )
    else:
        await callback.message.answer(
            f"✅ <b>Масштаб установлен:</b> {label}\nПри следующем анализе спутник охватит эту площадь.",
            parse_mode=ParseMode.HTML,
        )


# ── Справка ──────────────────────────────────────────────────────────────────

@router.message(Command("help"))
@router.message(F.text.in_(["ℹ️ Справка / Инструкция", "ℹ️ Анықтама", "ℹ️ Справка / Анықтама"]))
async def handle_help(message: Message) -> None:
    """Справочная информация."""
    prefs = get_user_pref(message.from_user.id)
    lang = prefs["lang"]

    if lang == "kz":
        help_text = (
            "ℹ️ <b>DalaSat сервисін қалай пайдалану керек:</b>\n\n"
            "1️⃣ <b>Телефоннан:</b> Төмендегі <b>«📍 Алқабымды тексеру (GPS)»</b> батырмасын басыңыз.\n\n"
            "2️⃣ <b>Жылдам сынақ:</b> <b>«🌾 Сынақ алқабы (Зеренді)»</b> түймесін басыңыз — нақты бидай алқабы бірден талданады.\n\n"
            "3️⃣ <b>Қолмен енгізу:</b> Чатқа координаттарды жіберіңіз:\n"
            "   <code>53.2514, 69.1845</code>\n\n"
            "4️⃣ <b>Масштаб:</b> <b>«🔍 Масштабты таңдау»</b> мәзірінен 1×1 км, 2×2 км немесе 4×4 км көлемін таңдаңыз.\n\n"
            "📍 <b>Ақмола облысындағы дайын сынақ нүктелері:</b>\n"
            "• Зеренді: <code>53.2514, 69.1845</code>\n"
            "• Атбасар: <code>51.7820, 68.4150</code>\n"
            "• Бараев ин-ты: <code>51.6840, 71.0540</code>\n"
            "• Родина агрофирмасы: <code>51.3420, 70.8250</code>"
        )
    else:
        help_text = (
            "ℹ️ <b>Как пользоваться сервисом DalaSat:</b>\n\n"
            "1️⃣ <b>Со смартфона:</b> Нажмите кнопку <b>«📍 Проверить моё поле (GPS)»</b> внизу экрана.\n\n"
            "2️⃣ <b>Быстрый тест:</b> Нажмите <b>«🌾 Тестовое поле (Зеренда)»</b> — бот моментально покажет реальное поле в Акмолинской области.\n\n"
            "3️⃣ <b>Вручную:</b> Просто отправьте координаты текстом в чат:\n"
            "   <code>53.2514, 69.1845</code>\n\n"
            "4️⃣ <b>Масштаб:</b> Через кнопку <b>«🔍 Выбрать масштаб»</b> переключайте охват: 1×1 км (поле), 2×2 км (севооборот) или 4×4 км (массив).\n\n"
            "💡 <b>Если вы с компьютера (Telegram Desktop):</b>\n"
            "В Telegram на ПК кнопка геолокации аппаратно заблокирована. Используйте скрепку 📎 ➔ «Геолокация» или кнопку тестового поля!\n\n"
            "📍 <b>Поля Акмолинской области для теста:</b>\n"
            "• Зеренда: <code>53.2514, 69.1845</code>\n"
            "• Атбасар: <code>51.7820, 68.4150</code>\n"
            "• Поля им. Бараева: <code>51.6840, 71.0540</code>\n"
            "• Агрофирма «Родина»: <code>51.3420, 70.8250</code>"
        )

    await message.answer(help_text, parse_mode=ParseMode.HTML)


# ── Тестовое поле ───────────────────────────────────────────────────────────

@router.message(F.text.in_(["🌾 Тестовое поле (Зеренда)", "🌾 Сынақ алқабы (Зеренді)", "🌾 Тестовое поле (Зеренда, Акмола)"]))
async def handle_test_field(message: Message, state: FSMContext) -> None:
    """Быстрый запуск анализа на реальном пшеничном поле в Акмолинской области."""
    await state.clear()
    lat, lon = 53.2514, 69.1845
    prefs = get_user_pref(message.from_user.id)
    lang = prefs["lang"]

    if lang == "kz":
        text = (
            "🌾 <b>Сынақ алқабы таңдалды: Зеренді ауданы, Ақмола облысы</b>\n"
            f"📍 Координаттары: <code>{lat:.4f}°N, {lon:.4f}°E</code>\n"
            "🛰 Sentinel-2 спутниктік деректерін жүктеу басталды..."
        )
    else:
        text = (
            "🌾 <b>Выбрано реальное поле: Зерендинский район, Акмолинская область</b>\n"
            f"📍 Координаты: <code>{lat:.4f}°N, {lon:.4f}°E</code>\n"
            "🛰 Запрашиваем спутниковый снимок Sentinel-2..."
        )

    await message.answer(text, parse_mode=ParseMode.HTML)
    await _run_field_analysis(message, lat, lon)


# ── Ручной ввод координат ───────────────────────────────────────────────────

@router.message(F.text.in_(["✏️ Ввести координаты вручную", "✏️ Координаттарды енгізу"]))
async def handle_manual_coords_prompt(message: Message, state: FSMContext) -> None:
    """Просим пользователя ввести координаты."""
    await state.set_state(FieldForm.waiting_for_coordinates)
    prefs = get_user_pref(message.from_user.id)
    lang = prefs["lang"]

    if lang == "kz":
        text = (
            "✏️ Алқаптың координаттарын келесі түрде енгізіңіз:\n"
            "<code>ендік, бойлық</code>\n\n"
            "Мысал: <code>53.2514, 69.1845</code>\n\n"
            "<i>Сондай-ақ қыстырғыш 📎 арқылы геолокацияны жібере аласыз.</i>"
        )
    else:
        text = (
            "✏️ Введите координаты поля в формате:\n"
            "<code>широта, долгота</code>\n\n"
            "Пример: <code>53.2514, 69.1845</code>\n\n"
            "<i>Или отправьте геолокацию через скрепку 📎</i>"
        )

    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardRemove())


# ── Обработка геолокации ────────────────────────────────────────────────────

@router.message(F.location)
@router.message(F.venue)
async def handle_location(message: Message, state: FSMContext) -> None:
    """Обрабатываем геолокацию из кнопки или скрепки."""
    await state.clear()
    loc = message.location or (message.venue.location if message.venue else None)
    if not loc:
        await message.answer("Не удалось определить координаты из сообщения.")
        return

    lat = loc.latitude
    lon = loc.longitude
    prefs = get_user_pref(message.from_user.id)
    lang = prefs["lang"]

    ack_text = (
        f"📍 <b>Геолокация қабылданды:</b> <code>{lat:.4f}°N, {lon:.4f}°E</code>\n"
        "Спутниктік талдау басталуда..."
        if lang == "kz" else
        f"📍 <b>Геолокация получена:</b> <code>{lat:.4f}°N, {lon:.4f}°E</code>\n"
        "Запускаем спутниковый анализ..."
    )
    await message.answer(ack_text, parse_mode=ParseMode.HTML, reply_markup=get_main_keyboard(lang))
    await _run_field_analysis(message, lat, lon)


# ── Текстовые координаты в FSM ──────────────────────────────────────────────

@router.message(FieldForm.waiting_for_coordinates)
async def handle_text_coordinates(message: Message, state: FSMContext) -> None:
    """Обрабатываем текстовый ввод координат."""
    if message.location or message.venue:
        await handle_location(message, state)
        return

    if not message.text:
        await message.answer("Пожалуйста, отправьте координаты текстом или геолокацию.")
        return

    prefs = get_user_pref(message.from_user.id)
    lang = prefs["lang"]

    # Если пользователь передумал и нажал кнопку меню
    if "Сынақ алқабы" in message.text or "Тестовое поле" in message.text:
        await handle_test_field(message, state)
        return
    if "Анықтама" in message.text or "Справка" in message.text:
        await state.clear()
        await handle_help(message)
        return

    text = message.text.strip().replace(",", " ").split()
    try:
        lat = float(text[0])
        lon = float(text[1])
    except (ValueError, IndexError):
        err = "❌ Қате формат. Мысалы: <code>53.2514, 69.1845</code>" if lang == "kz" else "❌ Неверный формат. Введите два числа через запятую:\n<code>53.2514, 69.1845</code>"
        await message.answer(err, parse_mode=ParseMode.HTML)
        return

    if not (35.0 <= lat <= 56.0 and 46.0 <= lon <= 88.0):
        err_kz = "⚠️ Координаттар Қазақстан аумағынан тыс. Қайта тексеріңіз (алдымен ендік, кейін бойлық)."
        err_ru = "⚠️ Координаты вне территории Казахстана. Проверьте правильность ввода (сначала широта, потом долгота)."
        await message.answer(err_kz if lang == "kz" else err_ru)
        return

    await state.clear()
    ok_text = "✅ Координаттар қабылданды!" if lang == "kz" else "✅ Координаты приняты!"
    await message.answer(ok_text, reply_markup=get_main_keyboard(lang))
    await _run_field_analysis(message, lat, lon)


# ── Автоматический перехват координат в обычном тексте ───────────────────────

@router.message(F.text.regexp(COORD_PATTERN))
async def handle_direct_coordinates(message: Message, state: FSMContext) -> None:
    """Парсит координаты, если пользователь просто вставил их в чат без нажатия кнопок."""
    await state.clear()
    match = COORD_PATTERN.match(message.text.strip())
    if match:
        lat = float(match.group(1))
        lon = float(match.group(2))
        if 35.0 <= lat <= 56.0 and 46.0 <= lon <= 88.0:
            prefs = get_user_pref(message.from_user.id)
            lang = prefs["lang"]
            txt = (
                f"📍 <b>Координаттар танылды:</b> <code>{lat:.4f}, {lon:.4f}</code>\nСпутниктік талдау басталды..."
                if lang == "kz" else
                f"📍 <b>Распознаны координаты:</b> <code>{lat:.4f}, {lon:.4f}</code>\nЗапускаем спутниковый анализ..."
            )
            await message.answer(txt, parse_mode=ParseMode.HTML, reply_markup=get_main_keyboard(lang))
            await _run_field_analysis(message, lat, lon)


# ── Главный пайплайн анализа поля ───────────────────────────────────────────

async def _run_field_analysis(message: Message, lat: float, lon: float) -> None:
    """
    Основной конвейер анализа:
    1. Sentinel-2 L2A COG скачивание по выбранному масштабу
    2. Расчёт NDVI, NDMI, индекса пригодности почвы
    3. Построение карты NDVI
    4. Запрос рекомендаций у Gemini AI на выбранном языке
    5. Отправка результата и сохранение для PDF
    """
    user_id = message.from_user.id
    prefs = get_user_pref(user_id)
    lang = prefs["lang"]
    scale_key = prefs["scale"]
    scale_info = SCALE_PROFILES.get(scale_key, SCALE_PROFILES[DEFAULT_SCALE])
    delta = scale_info["delta"]
    scale_label = scale_info["label_kz"] if lang == "kz" else scale_info["label_ru"]

    start_text = (
        f"🛰 <b>Sentinel-2 спутнигінен мәлімет сұралуда...</b>\n\n"
        f"📍 Координаттар: <code>{lat:.5f}, {lon:.5f}</code>\n"
        f"🔍 Масштаб: <b>{scale_label}</b>\n"
        "⏳ Күте тұрыңыз (3–8 секунд)..."
        if lang == "kz" else
        f"🛰 <b>Запрашиваем спутниковый снимок Sentinel-2...</b>\n\n"
        f"📍 Координаты: <code>{lat:.5f}, {lon:.5f}</code>\n"
        f"🔍 Масштаб: <b>{scale_label}</b>\n"
        "⏳ Это займёт 3–8 секунд. Пожалуйста, подождите..."
    )

    status_msg = await message.answer(start_text, parse_mode=ParseMode.HTML)

    try:
        await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        satellite_data = await fetch_sentinel2(lat, lon, delta=delta)

        if satellite_data is None:
            not_found_text = (
                "😔 <b>Спутниктік снимок табылмады</b>\n\n"
                "Соңғы 90 күнде бұл аймақ үшін ашық (бұлтсыз) Sentinel-2 снимкалары жоқ.\n\n"
                "Ұсыныстар:\n"
                "• Координаттарды тексеріңіз (қала немесе көлге түсіп қалмағанына көз жеткізіңіз)\n"
                "• Масштабты өзгертіп көріңіз (4×4 км)\n"
                "• Немесе «🌾 Сынақ алқабы» түймесін басыңыз"
                if lang == "kz" else
                "😔 <b>Снимок не найден</b>\n\n"
                "За последние 90 дней нет безоблачных снимков Sentinel-2 для этого района.\n\n"
                "Попробуйте:\n"
                "• Проверить координаты (возможно, попало в водоём или город)\n"
                "• Изменить масштаб на 4×4 км\n"
                "• Или нажать «🌾 Тестовое поле»"
            )
            await status_msg.edit_text(not_found_text, parse_mode=ParseMode.HTML)
            return

        b04, b08, b11, date_str = satellite_data

        # Расчёт индексов
        calc_text = (
            f"📊 Индекстер есептелуде...\n📅 Снимок күні: <b>{date_str}</b>"
            if lang == "kz" else
            f"📊 Рассчитываем NDVI, NDMI и качество почвы...\n📅 Снимок от: <b>{date_str}</b>"
        )
        await status_msg.edit_text(calc_text, parse_mode=ParseMode.HTML)
        stats = calculate_indices(b04, b08, b11)

        # Построение карты
        map_text = (
            f"🎨 Жылу картасы сызылуда...\n📅 Снимок күні: <b>{date_str}</b>"
            if lang == "kz" else
            f"🎨 Строим тепловую карту поля...\n📅 Снимок от: <b>{date_str}</b>"
        )
        await status_msg.edit_text(map_text, parse_mode=ParseMode.HTML)
        await message.bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)

        loop = asyncio.get_event_loop()
        ndvi_image_bytes = await loop.run_in_executor(
            None,
            generate_ndvi_map,
            stats["ndvi_array"], lat, lon, date_str,
        )

        # Консультация Gemini AI на выбранном языке
        ai_text = (
            f"🤖 ЖИ-агроном талдау жүргізуде...\n📅 Снимок күні: <b>{date_str}</b>"
            if lang == "kz" else
            f"🤖 ИИ-агроном формирует рекомендации...\n📅 Снимок от: <b>{date_str}</b>"
        )
        await status_msg.edit_text(ai_text, parse_mode=ParseMode.HTML)
        ai_advice = await get_agronomic_advice(stats, lat, lon, date_str, lang=lang)

        # Кэш для PDF
        _analysis_cache[user_id] = {
            "stats": stats,
            "ai_advice": ai_advice,
            "ndvi_image_bytes": ndvi_image_bytes,
            "lat": lat,
            "lon": lon,
            "date_str": date_str,
            "scale_label": scale_label,
            "lang": lang,
        }

        await status_msg.delete()

        # Формирование карточки результата
        ndvi_emoji = (
            "🔴" if stats["mean_ndvi"] < 0.25 else
            "🟡" if stats["mean_ndvi"] < 0.45 else "🟢"
        )
        ndmi_emoji = (
            "🔴" if stats["mean_ndmi"] < 0.0 else
            "🟡" if stats["mean_ndmi"] < 0.2 else "🟢"
        )
        soil_score = stats.get("soil_score", 50)
        soil_status_ru = stats.get("soil_status_ru", "Хорошая")
        soil_status_kz = stats.get("soil_status_kz", "Жақсы")
        soil_emoji = stats.get("soil_emoji", "🟡")
        b_status_ru = stats.get("building_status_ru", "Построек не обнаружено (чистое поле)")
        b_status_kz = stats.get("building_status_kz", "Құрылыстар байқалмады (таза егістік)")
        b_emoji = stats.get("building_emoji", "🌾")

        if lang == "kz":
            caption = (
                f"🛰 <b>DalaSat — Алқапты экспресс-талдау</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"📍 <b>{lat:.4f}°N, {lon:.4f}°E</b>  |  📅 {date_str}\n"
                f"🔍 Масштаб: <b>{scale_label}</b>\n\n"
                f"🌱 <b>Топырақтың егуге дайындығы:</b> {soil_emoji} <b>{soil_score}%</b>\n"
                f"   ↳ <i>{soil_status_kz}</i>\n\n"
                f"🏛 <b>Құрылыстар / Инфрақұрылым:</b> {b_emoji} <b>{b_status_kz}</b>\n\n"
                f"📊 <b>Өсімдік метрикалары:</b>\n"
                f"{ndvi_emoji} NDVI (биомасса): <b>{stats['mean_ndvi']}</b> (мин: {stats['min_ndvi']} / макс: {stats['max_ndvi']})\n"
                f"{ndmi_emoji} NDMI (топырақ ылғалдылығы): <b>{stats['mean_ndmi']}</b>\n\n"
                f"📈 <b>Алқап жағдайы:</b>\n"
                f"🔴 Стресс аймағы (NDVI&lt;0.25): <b>{stats['stressed_percent']}%</b>\n"
                f"🟡 Орташа: <b>{stats['moderate_percent']}%</b>\n"
                f"🟢 Жақсы: <b>{stats['healthy_percent']}%</b>\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🤖 <b>ЖИ-агроном кеңесі:</b>\n\n"
                f"{ai_advice}"
            )
            short_caption = (
                f"🛰 <b>DalaSat</b> · {date_str}\n"
                f"📍 {lat:.4f}°N, {lon:.4f}°E  |  🔍 {scale_label}\n"
                f"🌱 Егуге дайындық: {soil_emoji} <b>{soil_score}%</b>\n"
                f"🏛 Құрылыстар: {b_emoji} {b_status_kz}\n"
                f"🟢 NDVI: {stats['mean_ndvi']} | 💧 NDMI: {stats['mean_ndmi']}"
            )
            advice_header = "🤖 <b>ЖИ-агроном талдауы мен кеңесі:</b>"
        else:
            caption = (
                f"🛰 <b>DalaSat — Экспресс-анализ поля</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"📍 <b>{lat:.4f}°N, {lon:.4f}°E</b>  |  📅 {date_str}\n"
                f"🔍 Масштаб: <b>{scale_label}</b>\n\n"
                f"🌱 <b>Пригодность почвы для посадки:</b> {soil_emoji} <b>{soil_score}%</b>\n"
                f"   ↳ <i>{soil_status_ru}</i>\n\n"
                f"🏛 <b>Постройки / Инфраструктура:</b> {b_emoji} <b>{b_status_ru}</b>\n\n"
                f"📊 <b>Метрики вегетации:</b>\n"
                f"{ndvi_emoji} NDVI (биомасса): <b>{stats['mean_ndvi']}</b> (мин: {stats['min_ndvi']} / макс: {stats['max_ndvi']})\n"
                f"{ndmi_emoji} NDMI (влажность почвы): <b>{stats['mean_ndmi']}</b>\n\n"
                f"📈 <b>Классификация поля:</b>\n"
                f"🔴 Стресс (NDVI&lt;0.25): <b>{stats['stressed_percent']}%</b>\n"
                f"🟡 Умеренно: <b>{stats['moderate_percent']}%</b>\n"
                f"🟢 Отлично: <b>{stats['healthy_percent']}%</b>\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🤖 <b>ИИ-агроном:</b>\n\n"
                f"{ai_advice}"
            )
            short_caption = (
                f"🛰 <b>DalaSat</b> · {date_str}\n"
                f"📍 {lat:.4f}°N, {lon:.4f}°E  |  🔍 {scale_label}\n"
                f"🌱 Почва к севу: {soil_emoji} <b>{soil_score}%</b> ({soil_status_ru.split()[0]})\n"
                f"🏛 Постройки: {b_emoji} {b_status_ru}\n"
                f"🟢 NDVI: {stats['mean_ndvi']} | 💧 NDMI: {stats['mean_ndmi']}"
            )
            advice_header = "🤖 <b>Рекомендации ИИ-агронома:</b>"

        # Лимит подписи фото в Telegram 1024 символа
        if len(caption) > 1024:
            await message.answer_photo(
                photo=BufferedInputFile(ndvi_image_bytes, filename="dala_sat_ndvi.png"),
                caption=short_caption,
                parse_mode=ParseMode.HTML,
            )
            await message.answer(
                f"{advice_header}\n\n{ai_advice}",
                parse_mode=ParseMode.HTML,
                reply_markup=get_pdf_keyboard(user_id, lang),
            )
        else:
            await message.answer_photo(
                photo=BufferedInputFile(ndvi_image_bytes, filename="dala_sat_ndvi.png"),
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=get_pdf_keyboard(user_id, lang),
            )

    except Exception as exc:
        logger.exception("Ошибка в _run_field_analysis: %s", exc)
        try:
            err_msg = (
                f"❌ <b>Талдау кезінде қате орын алды.</b>\nСебебі: <code>{str(exc)[:200]}</code>"
                if lang == "kz" else
                f"❌ <b>Произошла ошибка при анализе поля.</b>\nПричина: <code>{str(exc)[:200]}</code>"
            )
            await status_msg.edit_text(err_msg, parse_mode=ParseMode.HTML)
        except Exception:
            pass


# ── Скачивание PDF-паспорта ──────────────────────────────────────────────────

@router.callback_query(F.data.startswith("pdf:"))
async def handle_pdf_request(callback: CallbackQuery) -> None:
    """Генерирует и отправляет PDF-паспорт поля."""
    user_id = int(callback.data.split(":")[1])

    if user_id not in _analysis_cache:
        await callback.answer(
            "⚠️ Деректер ескірді / Данные устарели. Қайта талдау жасаңыз.",
            show_alert=True,
        )
        return

    cached = _analysis_cache[user_id]
    lang = cached.get("lang", "ru")
    loading_text = "⏳ PDF-төлқұжат дайындалуда..." if lang == "kz" else "⏳ Генерируем официальный PDF-паспорт поля..."
    await callback.answer(loading_text)
    await callback.message.bot.send_chat_action(
        callback.message.chat.id, ChatAction.UPLOAD_DOCUMENT
    )

    try:
        loop = asyncio.get_event_loop()
        pdf_bytes = await loop.run_in_executor(
            None,
            generate_field_passport,
            cached["stats"],
            cached["ai_advice"],
            cached["ndvi_image_bytes"],
            cached["lat"],
            cached["lon"],
            cached["date_str"],
        )

        filename = (
            f"DalaSat_Field_Report_{cached['lat']:.3f}_{cached['lon']:.3f}"
            f"_{cached['date_str']}.pdf"
        )

        caption = (
            f"📄 <b>DalaSat: Алқаптың ресми төлқұжаты</b>\n"
            f"📍 Координаттары: {cached['lat']:.4f}°N, {cached['lon']:.4f}°E\n"
            f"📅 Снимок күні: {cached['date_str']}"
            if lang == "kz" else
            f"📄 <b>DalaSat: Официальный паспорт поля</b>\n"
            f"📍 Координаты: {cached['lat']:.4f}°N, {cached['lon']:.4f}°E\n"
            f"📅 Дата снимка: {cached['date_str']}"
        )

        await callback.message.answer_document(
            document=BufferedInputFile(pdf_bytes, filename=filename),
            caption=caption,
            parse_mode=ParseMode.HTML,
        )

    except Exception as exc:
        logger.exception("Ошибка генерации PDF: %s", exc)
        await callback.message.answer(
            f"❌ Не удалось сгенерировать PDF: <code>{str(exc)[:200]}</code>",
            parse_mode=ParseMode.HTML,
        )


# ── Запуск бота ───────────────────────────────────────────────────────────────
async def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN не задан! Проверьте файл .env."
        )

    bot = Bot(
        token=TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    logger.info("🚀 DalaSat Bot запущен!")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())
