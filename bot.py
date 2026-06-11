#!/usr/bin/env python3
"""
BountySystem - ПРОСТОЙ РАБОЧИЙ БОТ для оповещения из Telegram каналов
Исправленная версия - без ошибок авторизации
"""

import asyncio
import logging
import re
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError

# ================= НАСТРОЙКИ (ЗАМЕНИТЕ НА СВОИ) =================
API_ID = 27995587
API_HASH = '18b67d6be3bd13bf0ba55a8d6bdb3482'
BOT_TOKEN = '8748755580:AAHRNxTFNlMIyrZGLOeRXgNqH_qnUei65Ug'
YOUR_USER_ID = 6284104677  # ВАШ Telegram ID (узнать у @userinfobot)

# КАНАЛЫ ДЛЯ МОНИТОРИНГА (username без @)
CHANNELS = [
    'TaganCHP',
    'MonitorRostov',
    'radar_rvk',
]

# КЛЮЧЕВЫЕ СЛОВА ДЛЯ ОПОВЕЩЕНИЯ
ALERT_KEYWORDS = [
    'бпла', 'беспилот', 'дрон', 'шахед',
    'ракет', 'ракета', 'нептун', 'калибр',
    'атака', 'прилет', 'опасность', 'тревога',
    'сирена', 'угроза', 'влетел', 'пуск', 'направлен'
]

# ================================================================

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Создаем клиентов
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ПРАВИЛЬНЫЙ СПОСОБ: используем бот-токен в Telethon
# Это позволяет читать каналы без авторизации по телефону
telegram_client = TelegramClient('bounty_bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)


async def send_alert(message_text: str, channel_name: str):
    """Отправляет оповещение пользователю"""
    # Обрезаем длинные сообщения
    if len(message_text) > 400:
        message_text = message_text[:400] + "..."
    
    alert = (
        f"🚨 **ОПАСНОСТЬ!** 🚨\n\n"
        f"📡 **Канал:** @{channel_name}\n"
        f"🕐 **Время:** {datetime.now().strftime('%H:%M:%S')}\n\n"
        f"📝 **Сообщение:**\n"
        f"_{message_text}_\n\n"
        f"⚠️ Будьте внимательны и следите за официальными сообщениями!"
    )
    
    try:
        await bot.send_message(YOUR_USER_ID, alert, parse_mode='Markdown')
        logger.info(f"✅ ОПОВЕЩЕНИЕ ОТПРАВЛЕНО! Канал: @{channel_name}")
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")


async def monitor_channels():
    """Мониторинг каналов в реальном времени"""
    try:
        logger.info("=" * 50)
        logger.info("🚀 BountySystem ЗАПУЩЕН")
        logger.info(f"📡 Мониторинг каналов: {', '.join(['@'+c for c in CHANNELS])}")
        logger.info(f"👤 Оповещения будут отправлены пользователю ID: {YOUR_USER_ID}")
        logger.info("=" * 50)
        
        @telegram_client.on(events.NewMessage(chats=CHANNELS))
        async def handler(event):
            try:
                # Получаем текст сообщения
                message_text = event.message.text
                if not message_text:
                    return
                
                # Получаем имя канала
                channel = event.chat.username or event.chat.title
                
                # Проверяем наличие ключевых слов (регистронезависимо)
                text_lower = message_text.lower()
                is_alert = any(keyword in text_lower for keyword in ALERT_KEYWORDS)
                
                # Проверяем что это не отбой
                is_cancel = 'отбой' in text_lower or 'отмен' in text_lower or 'отмена' in text_lower
                
                if is_alert and not is_cancel:
                    logger.info(f"🔔 ОБНАРУЖЕНА УГРОЗА в @{channel}")
                    logger.info(f"   Текст: {message_text[:150]}...")
                    await send_alert(message_text, channel)
                else:
                    logger.debug(f"Пропущено из @{channel}: нет ключевых слов или отбой")
                    
            except Exception as e:
                logger.error(f"Ошибка в обработчике сообщений: {e}")
        
        # Держим соединение открытым
        await telegram_client.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"Ошибка в monitor_channels: {e}")


@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "✅ **BountySystem активен!**\n\n"
        f"📡 **Мониторинг каналов:**\n" + 
        "\n".join([f"   • @{ch}" for ch in CHANNELS]) +
        "\n\n🟢 **Статус:** Работает\n"
        "⚠️ При обнаружении угрозы вы получите оповещение.",
        parse_mode="Markdown"
    )
    logger.info(f"Пользователь {message.from_user.id} отправил /start")


@dp.message(Command("status"))
async def status_cmd(message: types.Message):
    await message.answer(
        "🟢 **Статус BountySystem**\n\n"
        f"• Каналов в мониторинге: {len(CHANNELS)}\n"
        f"• Ключевых слов: {len(ALERT_KEYWORDS)}\n"
        "• Режим: реальное время\n"
        "✅ Система активна и отслеживает угрозы",
        parse_mode="Markdown"
    )


async def main():
    # Запускаем мониторинг каналов в фоне
    asyncio.create_task(monitor_channels())
    
    # Запускаем бота
    logger.info("🤖 Запуск Telegram бота...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════╗
║       BOUNTY SYSTEM v4.0              ║
║     ИСПРАВЛЕННАЯ ВЕРСИЯ               ║
║     БОТ + ЧТЕНИЕ КАНАЛОВ              ║
╚════════════════════════════════════════╝
    """)
    asyncio.run(main())
