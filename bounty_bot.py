import asyncio
import json
import re
import hashlib
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
from typing import Dict, Tuple, List, Optional

import redis.asyncio as redis
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from telethon import TelegramClient, events

from config import *

# ================= ИНИЦИАЛИЗАЦИЯ =================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
tg_client = TelegramClient('bounty_session', API_ID, API_HASH)

# === ВСЕ РЕГИОНЫ РФ ===
REGIONS = {
    "Москва": {"lat": 55.7558, "lon": 37.6176, "okrug": "ЦФО"},
    "Московская область": {"lat": 55.7558, "lon": 37.6176, "okrug": "ЦФО"},
    "Белгородская область": {"lat": 50.5975, "lon": 36.5858, "okrug": "ЦФО"},
    "Брянская область": {"lat": 53.2420, "lon": 34.3653, "okrug": "ЦФО"},
    "Воронежская область": {"lat": 51.6608, "lon": 39.2003, "okrug": "ЦФО"},
    "Курская область": {"lat": 51.7304, "lon": 36.1926, "okrug": "ЦФО"},
    "Липецкая область": {"lat": 52.6031, "lon": 39.5708, "okrug": "ЦФО"},
    "Орловская область": {"lat": 52.9703, "lon": 36.0635, "okrug": "ЦФО"},
    "Рязанская область": {"lat": 54.6295, "lon": 39.7427, "okrug": "ЦФО"},
    "Смоленская область": {"lat": 54.7826, "lon": 32.0453, "okrug": "ЦФО"},
    "Тамбовская область": {"lat": 52.7210, "lon": 41.4523, "okrug": "ЦФО"},
    "Тульская область": {"lat": 54.1931, "lon": 37.6175, "okrug": "ЦФО"},
    "Крым": {"lat": 44.9521, "lon": 34.1024, "okrug": "ЮФО"},
    "Краснодарский край": {"lat": 45.0355, "lon": 38.9753, "okrug": "ЮФО"},
    "Астраханская область": {"lat": 46.3477, "lon": 48.0338, "okrug": "ЮФО"},
    "Волгоградская область": {"lat": 48.7080, "lon": 44.5133, "okrug": "ЮФО"},
    "Ростовская область": {"lat": 47.2357, "lon": 39.7015, "okrug": "ЮФО"},
    "Севастополь": {"lat": 44.6167, "lon": 33.5254, "okrug": "ЮФО"},
    "Санкт-Петербург": {"lat": 59.9343, "lon": 30.3351, "okrug": "СЗФО"},
    "Ленинградская область": {"lat": 59.9311, "lon": 30.3609, "okrug": "СЗФО"},
    "Калининградская область": {"lat": 54.7104, "lon": 20.4522, "okrug": "СЗФО"},
    "Дагестан": {"lat": 42.9831, "lon": 47.5049, "okrug": "СКФО"},
    "Чечня": {"lat": 43.3180, "lon": 45.6987, "okrug": "СКФО"},
    "Ставропольский край": {"lat": 45.0448, "lon": 41.9691, "okrug": "СКФО"},
    "Татарстан": {"lat": 55.7961, "lon": 49.1064, "okrug": "ПФО"},
    "Башкортостан": {"lat": 54.7351, "lon": 55.9587, "okrug": "ПФО"},
    "Пермский край": {"lat": 58.0104, "lon": 56.2484, "okrug": "ПФО"},
    "Нижегородская область": {"lat": 56.2965, "lon": 43.9361, "okrug": "ПФО"},
    "Самарская область": {"lat": 53.1959, "lon": 50.1002, "okrug": "ПФО"},
    "Саратовская область": {"lat": 51.5336, "lon": 46.0342, "okrug": "ПФО"},
    "Свердловская область": {"lat": 56.8389, "lon": 60.6057, "okrug": "УрФО"},
    "Челябинская область": {"lat": 55.1644, "lon": 61.4368, "okrug": "УрФО"},
    "Тюменская область": {"lat": 57.1535, "lon": 65.5342, "okrug": "УрФО"},
    "Новосибирская область": {"lat": 55.0302, "lon": 82.9204, "okrug": "СФО"},
    "Омская область": {"lat": 54.9914, "lon": 73.3715, "okrug": "СФО"},
    "Красноярский край": {"lat": 56.0084, "lon": 92.8670, "okrug": "СФО"},
    "Иркутская область": {"lat": 52.2843, "lon": 104.3030, "okrug": "СФО"},
    "Приморский край": {"lat": 43.1153, "lon": 131.8855, "okrug": "ДФО"},
    "Хабаровский край": {"lat": 48.4802, "lon": 135.0719, "okrug": "ДФО"},
}

# Карта уровней источников
SOURCE_LEVEL_MAP = {}
for src in OFFICIAL_SOURCES:
    SOURCE_LEVEL_MAP[src] = 1
for src in VERIFIED_OSINT:
    SOURCE_LEVEL_MAP[src] = 2
for src_list in REGIONAL_SOURCES.values():
    for src in src_list:
        SOURCE_LEVEL_MAP[src] = 3


# ================= ГЕО-ФУНКЦИИ =================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def find_region_by_coords(lat, lon):
    closest = None
    min_dist = float('inf')
    for region, data in REGIONS.items():
        dist = haversine(lat, lon, data["lat"], data["lon"])
        if dist < min_dist and dist < 200:
            min_dist = dist
            closest = region
    return closest

def extract_coordinates(text):
    patterns = [
        r'(\d{1,2}\.\d{4,6})[, ]+(\d{1,3}\.\d{4,6})',
        r'(\d{1,2})°(\d{1,2})[\'′](\d{1,2})["″]?[, ]+(\d{1,3})°(\d{1,2})[\'′](\d{1,2})["″]?',
        r'coord(?:s)?[: ]+(\d{1,2}\.\d+)[, ]+(\d{1,3}\.\d+)',
        r'координаты?[: ]+(\d{1,2}\.\d+)[, ]+(\d{1,3}\.\d+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if len(match.groups()) == 2:
                return float(match.group(1)), float(match.group(2))
            elif len(match.groups()) == 6:
                lat = int(match.group(1)) + int(match.group(2))/60 + int(match.group(3))/3600
                lon = int(match.group(4)) + int(match.group(5))/60 + int(match.group(6))/3600
                return lat, lon
    return None

def extract_region_from_text(text):
    text_lower = text.lower()
    for region in REGIONS.keys():
        if region.lower() in text_lower:
            return region
    return None

def detect_threat_type(text):
    text_lower = text.lower()
    if any(k in text_lower for k in ['ракет', 'missile', 'нептун', 'калибр', 'искандер', 'циркон']):
        return 'missile'
    return 'drone'

def get_speed_by_type(threat_type):
    return MISSILE_SPEED if threat_type == 'missile' else DRONE_SPEED


# ================= ВЕРИФИКАЦИЯ =================
async def generate_event_id(text, source):
    normalized = re.sub(r'\d{1,2}:\d{2}', '', text.lower())
    normalized = re.sub(r'\d{1,2}\.\d{2}\.\d{4}', '', normalized)
    content_hash = hashlib.md5(normalized.encode()).hexdigest()[:12]
    time_window = datetime.now().strftime("%Y%m%d%H")
    return f"{content_hash}_{time_window}"

async def verify_and_alert(event_id, raw_text, source_channel, source_level, coordinates=None):
    event_data = await redis_client.get(f"event:{event_id}")
    
    if event_data:
        data = json.loads(event_data)
        existing_sources = [c["source"] for c in data["confirmations"]]
        if source_channel not in existing_sources:
            data["confirmations"].append({
                "source": source_channel,
                "level": source_level,
                "timestamp": datetime.now().isoformat()
            })
        data["source_level"] = max(data["source_level"], source_level)
        if coordinates and not data.get("coordinates"):
            data["coordinates"] = coordinates
    else:
        data = {
            "event_id": event_id,
            "raw_text": raw_text,
            "first_seen": datetime.now().isoformat(),
            "confirmations": [{
                "source": source_channel,
                "level": source_level,
                "timestamp": datetime.now().isoformat()
            }],
            "source_level": source_level,
            "coordinates": coordinates,
            "alert_sent": False
        }
    
    await redis_client.setex(f"event:{event_id}", VERIFICATION_WINDOW + 30, json.dumps(data))
    
    unique_sources = set([c["source"] for c in data["confirmations"]])
    confirmations_count = len(unique_sources)
    
    should_send = False
    if not data["alert_sent"]:
        if source_level == 1 and confirmations_count >= 1:
            should_send = True
        elif source_level == 2 and confirmations_count >= 2:
            should_send = True
        elif source_level == 3 and confirmations_count >= 3:
            should_send = True
        elif confirmations_count >= MIN_CONFIRMATIONS:
            should_send = True
    
    if should_send and not data["alert_sent"]:
        data["alert_sent"] = True
        await redis_client.setex(f"event:{event_id}", VERIFICATION_WINDOW + 30, json.dumps(data))
        await send_verified_alert(data, confirmations_count)
        return True
    
    logger.info(f"[{event_id}] Подтверждений: {confirmations_count}, уровень: {source_level}")
    return False

async def send_verified_alert(event_data, confirmation_count):
    raw_text = event_data["raw_text"]
    coords = event_data.get("coordinates")
    
    threat_type = detect_threat_type(raw_text)
    speed = get_speed_by_type(threat_type)
    
    # Определение направления
    raw_lower = raw_text.lower()
    direction_map = {
        "курск": "Курской области", "белгород": "Белгородской области",
        "брянск": "Брянской области", "азов": "Азовского моря",
        "крым": "Крыма", "харьков": "Харьковской области",
        "с востока": "востока", "с запада": "запада",
        "с севера": "севера", "с юга": "юга"
    }
    direction = "неизвестного направления"
    for key, value in direction_map.items():
        if key in raw_lower:
            direction = value
            break
    
    region = extract_region_from_text(raw_text) or "уточняется"
    
    eta_text = ""
    city_text = ""
    if coords:
        lat, lon = coords
        closest_city = None
        min_dist = float('inf')
        for reg, data in REGIONS.items():
            dist = haversine(lat, lon, data["lat"], data["lon"])
            if dist < min_dist and dist < 100:
                min_dist = dist
                closest_city = reg
        
        if closest_city:
            eta_minutes = round((min_dist / speed) * 60, 1)
            eta_text = f"⏱️ **Время подлета:** {eta_minutes} мин\n"
            city_text = f"🏙️ **Ближайший город:** {closest_city}\n📏 **Дистанция:** {round(min_dist, 1)} км\n"
    
    threat_emoji = "🚀" if threat_type == "missile" else "🛸"
    threat_name = "Ракетная атака" if threat_type == "missile" else "БПЛА"
    
    alert = (
        f"🚨 **ВОЗДУШНАЯ УГРОЗА** 🚨\n\n"
        f"{threat_emoji} **Тип:** {threat_name}\n"
        f"📍 **Регион:** {region}\n"
        f"🧭 **Направление:** с {direction}\n"
        f"{city_text}{eta_text}"
        f"✅ **Верификация:** {confirmation_count} источника(ов)\n"
        f"🕐 {datetime.now().strftime('%H:%M:%S')} (MSK)\n\n"
        "⚠️ **Действие:** Пройдите в укрытие, следите за официальными сообщениями."
    )
    
    await bot.send_message(OWNER_ID, alert, parse_mode="Markdown")
    logger.info(f"✅ Оповещение! Подтверждений: {confirmation_count}, тип: {threat_name}")


# ================= МОНИТОРИНГ =================
async def monitor_sources():
    await tg_client.start()
    logger.info(f"🔍 BountySystem запущен. Источников: {len(ALL_SOURCES)}")
    
    @tg_client.on(events.NewMessage(chats=ALL_SOURCES))
    async def handler(event):
        text = event.message.text
        if not text:
            return
        
        if not any(k in text.lower() for k in THREAT_KEYWORDS):
            return
        if any(k in text.lower() for k in CANCEL_KEYWORDS):
            return
        
        source = event.chat.username or event.chat.title
        source_level = SOURCE_LEVEL_MAP.get(event.chat.username, 3)
        coordinates = extract_coordinates(text)
        event_id = await generate_event_id(text, source)
        
        await verify_and_alert(event_id, text, source, source_level, coordinates)
        logger.info(f"📨 Обработано: {source} (уровень {source_level})")


# ================= КОМАНДЫ БОТА =================
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗺️ Регионы", callback_data="regions")],
        [InlineKeyboardButton(text="📡 Источники", callback_data="sources")],
        [InlineKeyboardButton(text="⚡ О системе", callback_data="about")]
    ])
    await message.answer(
        "✅ **BountySystem активен**\n\n"
        f"🇷🇺 Регионов: {len(REGIONS)}\n"
        f"📡 Источников: {len(ALL_SOURCES)}\n"
        "⚡ Режим: мгновенное оповещение + верификация\n\n"
        "1️⃣ Обнаружение угрозы\n"
        "2️⃣ Кросс-верификация (2+ источников)\n"
        "3️⃣ Расчет ETA при координатах\n"
        "4️⃣ Мгновенная отправка",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@dp.message(Command("status"))
async def status_cmd(message: types.Message):
    await message.answer(
        "🟢 **BountySystem статус:**\n\n"
        f"• Регионов: {len(REGIONS)}\n"
        f"• Источников: {len(ALL_SOURCES)}\n"
        f"  - Ур.1 (офиц.): {len(OFFICIAL_SOURCES)}\n"
        f"  - Ур.2 (OSINT): {len(VERIFIED_OSINT)}\n"
        f"  - Ур.3 (регион.): {sum(len(v) for v in REGIONAL_SOURCES.values())}\n"
        f"• Окно верификации: {VERIFICATION_WINDOW} сек\n"
        f"• Мин. подтверждений: {MIN_CONFIRMATIONS}\n\n"
        "✅ Система активна",
        parse_mode="Markdown"
    )

@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    if callback.data == "regions":
        text = "🗺️ **Регионы мониторинга:**\n\n"
        for region, data in REGIONS.items():
            text += f"• {region} ({data['okrug']})\n"
        await callback.message.edit_text(text[:4000], parse_mode="Markdown")
        await callback.answer()
    elif callback.data == "sources":
        text = f"📡 **Источников: {len(ALL_SOURCES)}**\n\n"
        text += "**Уровень 1 (официальные):**\n"
        for s in OFFICIAL_SOURCES[:10]:
            text += f"  • @{s}\n"
        text += f"\n**Уровень 2 (OSINT):**\n"
        for s in VERIFIED_OSINT[:10]:
            text += f"  • @{s}\n"
        await callback.message.edit_text(text[:4000], parse_mode="Markdown")
        await callback.answer()
    elif callback.data == "about":
        await callback.message.edit_text(
            "⚡ **BountySystem**\n\n"
            "Система мониторинга и оповещения о воздушных угрозах.\n\n"
            "**Принцип:**\n"
            "• Мониторинг 60+ каналов\n"
            "• Кросс-верификация источников\n"
            "• Расчет ETA по координатам\n"
            "• Мгновенная отправка\n\n"
            f"🤖 @{ (await bot.get_me()).username }",
            parse_mode="Markdown"
        )
        await callback.answer()


# ================= ЗАПУСК =================
async def main():
    asyncio.create_task(monitor_sources())
    logger.info("🚀 BountySystem запущен")
    logger.info(f"📡 Мониторинг {len(ALL_SOURCES)} источников")
    logger.info(f"🗺️ {len(REGIONS)} регионов РФ")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
