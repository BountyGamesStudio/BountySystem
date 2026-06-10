#!/usr/bin/env python3
"""
BountySystem - система оповещения о воздушных угрозах
Мониторинг только указанных каналов: TaganCHP, MonitorRostov, radar_rvk
"""

import asyncio
import re
import logging
import sys
import json
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2

import redis.asyncio as redis
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from telethon import TelegramClient, events

from config import *

# ================= ИНИЦИАЛИЗАЦИЯ =================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Проверка OWNER_ID
if OWNER_ID == 123456789:
    logger.error("❌ OWNER_ID не настроен! Укажите ваш Telegram ID в config.py")
    print("\n⚠️ ПОЛУЧИТЕ ВАШ ID У @userinfobot и вставьте в config.py\n")
    sys.exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
tg_client = TelegramClient('bounty_session', API_ID, API_HASH)


# ================= ГЕО-ФУНКЦИИ =================
def haversine(lat1, lon1, lat2, lon2):
    """Расстояние между точками в км"""
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def extract_coordinates(text):
    """Извлечение координат из текста"""
    patterns = [
        r'(\d{1,2}\.\d{3,6})[, ]+(\d{1,3}\.\d{3,6})',
        r'(\d{1,2})°(\d{1,2})[\'′](\d{1,2})["″]?[, ]+(\d{1,3})°(\d{1,2})[\'′](\d{1,2})["″]?',
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

def find_closest_city(lat, lon):
    """Находит ближайший город из списка"""
    closest = None
    min_dist = float('inf')
    for city, coords in CITIES.items():
        dist = haversine(lat, lon, coords["lat"], coords["lon"])
        if dist < min_dist:
            min_dist = dist
            closest = city
    return closest, min_dist

def extract_direction(text):
    """Извлекает направление атаки из текста"""
    text_lower = text.lower()
    directions = {
        'море': 'Азовского моря',
        'азов': 'Азовского моря',
        'курск': 'Курской области',
        'белгород': 'Белгородской области',
        'харьков': 'Харьковской области',
        'с востока': 'востока',
        'с запада': 'запада',
        'с севера': 'севера',
        'с юга': 'юга',
        'крым': 'Крыма',
    }
    for key, value in directions.items():
        if key in text_lower:
            return value
    return 'неизвестного направления'

def detect_threat_type(text):
    """Определяет тип угрозы"""
    text_lower = text.lower()
    if any(k in text_lower for k in ['ракет', 'missile', 'нептун', 'калибр', 'искандер']):
        return 'missile'
    return 'drone'


# ================= ОПОВЕЩЕНИЕ =================
async def send_alert(raw_text, source_channel, coordinates=None):
    """Отправка оповещения"""
    threat_type = detect_threat_type(raw_text)
    direction = extract_direction(raw_text)
    threat_emoji = "🚀" if threat_type == "missile" else "🛸"
    threat_name = "Ракетная атака" if threat_type == "missile" else "БПЛА"
    
    # Базовое сообщение
    alert = (
        f"🚨 **ВОЗДУШНАЯ УГРОЗА** 🚨\n\n"
        f"{threat_emoji} **Тип:** {threat_name}\n"
        f"🧭 **Направление:** с {direction}\n"
        f"📡 **Источник:** @{source_channel}\n"
        f"🕐 {datetime.now().strftime('%H:%M:%S')} (MSK)\n\n"
    )
    
    # Если есть координаты - добавляем расчёт времени
    if coordinates:
        lat, lon = coordinates
        closest_city, distance = find_closest_city(lat, lon)
        speed = DRONE_SPEED if threat_type == 'drone' else 1000
        eta_minutes = round((distance / speed) * 60, 1)
        
        alert += (
            f"📍 **Координаты:** {lat:.4f}, {lon:.4f}\n"
            f"🏙️ **Ближайший город:** {closest_city}\n"
            f"📏 **Дистанция:** {round(distance, 1)} км\n"
            f"⏱️ **Расчетное время подлета:** {eta_minutes} мин\n\n"
        )
    else:
        # Если координат нет - отправляем предупреждение о необходимости уточнения
        alert += (
            f"📍 **Регион:** Ростовская область\n"
            f"🔄 **Детали уточняются...**\n\n"
        )
    
    alert += "⚠️ **Действие:** Пройдите в укрытие, следите за официальными сообщениями."
    
    # Отправка владельцу
    await bot.send_message(OWNER_ID, alert, parse_mode="Markdown")
    logger.info(f"✅ ОПОВЕЩЕНИЕ ОТПРАВЛЕНО! Источник: @{source_channel}, тип: {threat_name}")


# ================= МОНИТОРИНГ КАНАЛОВ =================
async def monitor_channels():
    """Мониторинг только указанных каналов"""
    await tg_client.start()
    logger.info(f"🔍 BountySystem запущен. Мониторинг каналов: {len(MONITORED_CHANNELS)}")
    for ch in MONITORED_CHANNELS:
        logger.info(f"   📡 @{ch}")
    
    # Хранилище отправленных событий (чтобы не дублировать)
    sent_events = set()
    
    @tg_client.on(events.NewMessage(chats=MONITORED_CHANNELS))
    async def handler(event):
        text = event.message.text
        if not text:
            return
        
        source = event.chat.username
        if not source:
            source = event.chat.title
        
        logger.info(f"📨 Новое сообщение из @{source}: {text[:100]}...")
        
        # Проверка на ключевые слова угрозы
        is_threat = any(k in text.lower() for k in THREAT_KEYWORDS)
        is_cancel = any(k in text.lower() for k in CANCEL_KEYWORDS)
        
        if is_cancel:
            logger.info(f"   → Отбой (игнорируем)")
            return
        
        if not is_threat:
            logger.info(f"   → Не угроза (пропущено)")
            return
        
        # Генерация ID события (на основе текста)
        text_hash = re.sub(r'\d{1,2}:\d{2}', '', text.lower())
        text_hash = re.sub(r'\d{1,2}\.\d{2}\.\d{4}', '', text_hash)
        import hashlib
        event_id = hashlib.md5(text_hash.encode()).hexdigest()[:16]
        
        # Проверка на дубликат (в течение 5 минут)
        if event_id in sent_events:
            logger.info(f"   → Дубликат, пропущен")
            return
        
        # Добавляем в отправленные
        sent_events.add(event_id)
        # Очищаем старые ID (каждые 5 минут)
        asyncio.create_task(cleanup_events(sent_events, event_id))
        
        # Извлекаем координаты
        coords = extract_coordinates(text)
        
        # ОТПРАВЛЯЕМ ОПОВЕЩЕНИЕ
        await send_alert(text, source, coords)
        
        # Дополнительно логируем
        if coords:
            logger.info(f"   → Координаты найдены: {coords}")
        else:
            logger.info(f"   → Координаты не найдены, отправлено базовое оповещение")

async def cleanup_events(sent_events, event_id):
    """Удаляет ID события из памяти через 5 минут"""
    await asyncio.sleep(300)  # 5 минут
    if event_id in sent_events:
        sent_events.remove(event_id)


# ================= КОМАНДЫ БОТА =================
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "✅ **BountySystem активен**\n\n"
        f"📡 **Мониторинг каналов:**\n" +
        "\n".join([f"   • @{ch}" for ch in MONITORED_CHANNELS]) +
        "\n\n⚡ **Режим:** Реальное время\n"
        "🚨 **Оповещения:** Мгновенные\n\n"
        "При обнаружении угрозы вы получите уведомление.",
        parse_mode="Markdown"
    )

@dp.message(Command("status"))
async def status_cmd(message: types.Message):
    await message.answer(
        "🟢 **BountySystem статус:**\n\n"
        f"• Мониторинг каналов: {len(MONITORED_CHANNELS)}\n"
        + "\n".join([f"  - @{ch}" for ch in MONITORED_CHANNELS]) +
        f"\n\n• Городов в базе: {len(CITIES)}\n"
        "• Режим: реальное время\n"
        "✅ Система активна и ожидает угрозы",
        parse_mode="Markdown"
    )


# ================= ЗАПУСК =================
async def main():
    # Запускаем мониторинг
    asyncio.create_task(monitor_channels())
    
    logger.info("🚀 BountySystem запущен")
    logger.info(f"📡 Мониторинг {len(MONITORED_CHANNELS)} каналов:")
    for ch in MONITORED_CHANNELS:
        logger.info(f"   → @{ch}")
    
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════╗
║        BountySystem v2.0              ║
║    Мониторинг: TaganCHP               ║
║                MonitorRostov          ║
║                radar_rvk              ║
╚═══════════════════════════════════════╝
    """)
    asyncio.run(main())
