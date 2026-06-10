# ================= КОНФИГУРАЦИЯ BOUNTYSYSTEM =================

# Telegram API данные (my.telegram.org)
API_ID = 27995587
API_HASH = '18b67d6be3bd13bf0ba55a8d6bdb3482'

# Telegram Bot Token (@BotFather)
BOT_TOKEN = '8748755580:AAHRNxTFNlMIyrZGLOeRXgNqH_qnUei65Ug'

# ВАШ TELEGRAM ID (узнать у @userinfobot)
OWNER_ID = 6284104677  # ← ВСТАВЬТЕ ВАШ РЕАЛЬНЫЙ ID

# Redis
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

# Параметры верификации
VERIFICATION_WINDOW = 90
MIN_CONFIRMATIONS = 2

# Скорости (км/ч)
DRONE_SPEED = 120
MISSILE_SPEED = 1000

# === ИСТОЧНИКИ (ОБНОВЛЕННЫЙ СПИСОК) ===

# Уровень 1: Официальные источники (100% достоверность)
OFFICIAL_SOURCES = [
    'mod_russia', 'mchs_official', 'mchs_rostov', 'mchs_belgorod',
    'mchs_kursk', 'mchs_voronezh', 'mchs_krasnodar', 'mchs_crimea',
    'rsks_official', 'operativny_shtab',
]

# Уровень 2: Верифицированные OSINT-паблики (85% достоверности)
VERIFIED_OSINT = [
    'radar_rostov_verify', 'radar_belgorod', 'radar_kursk', 'radar_krym',
    'military_observer_rf', 'avia_alert_russia', 'fighterbomber',
    'rybar', 'war_gonzo', 'readovkanews', 'baza_news', 'mash', 'shot_shot',
    'radar_rvk',           # ← НОВЫЙ КАНАЛ: Радар РВК (107k подписчиков)
]

# Уровень 3: Региональные каналы очевидцев (70% достоверности, требуют 3+ подтверждений)
REGIONAL_SOURCES = {
    'rostov': [
        'radar_rostov', 'rostov_monitor', 'rostov_live', 'tagil_live',
        'MonitorRostov',     # ← НОВЫЙ КАНАЛ: Монитор Ростовской области (10.7k)
    ],
    'taganrog': [
        'TaganCHP',          # ← НОВЫЙ КАНАЛ: ЧП Таганрог (55k)
    ],
    'belgorod': ['bel_radar', 'belgorod_operativ'],
    'kursk': ['kursk_radar', 'kursk_alert'],
    'bryansk': ['bryansk_radar', 'bryansk_monitor'],
    'voronezh': ['voronezh_radar', 'voronezh_operativ'],
    'krasnodar': ['kuban_alert', 'krasnodar_radar'],
    'crimea': ['crimea_alert', 'sevastopol_radar'],
}

# Собираем все источники
ALL_SOURCES = OFFICIAL_SOURCES + VERIFIED_OSINT
for sources in REGIONAL_SOURCES.values():
    ALL_SOURCES.extend(sources)

# Ключевые слова для фильтрации угроз
THREAT_KEYWORDS = [
    'бпла', 'беспилот', 'дрон', 'шахед', 'ракет', 'нептун',
    'калибр', 'искандер', 'атака', 'опасность', 'тревога', 'пуск',
    'воздушная тревога', 'сирена', 'угроза', 'влетел', 'залетел'
]

CANCEL_KEYWORDS = ['отбой', 'отмен', 'отмена', 'отменили']
