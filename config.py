# ================= КОНФИГУРАЦИЯ BOUNTYSYSTEM =================

# Telegram API данные (my.telegram.org)
API_ID = 27995587
API_HASH = '18b67d6be3bd13bf0ba55a8d6bdb3482'

# Telegram Bot Token (@BotFather)
BOT_TOKEN = '8748755580:AAHRNxTFNlMIyrZGLOeRXgNqH_qnUei65Ug'

# Ваш Telegram ID (узнать у @userinfobot)
OWNER_ID = 123456789  # ВСТАВЬТЕ ВАШ ID

# Redis (для кэша верификации)
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

# Параметры верификации
VERIFICATION_WINDOW = 90
MIN_CONFIRMATIONS = 2

# Скорость БПЛА (км/ч) для расчета ETA
DRONE_SPEED = 120
MISSILE_SPEED = 1000

# === ВСЕ ИСТОЧНИКИ ДЛЯ МОНИТОРИНГА ===

# Уровень 1: Официальные источники (100% достоверность)
OFFICIAL_SOURCES = [
    'mod_russia',              # Минобороны РФ
    'mchs_official',           # МЧС России
    'mchs_rostov',             # МЧС Ростовской области
    'mchs_belgorod',           # МЧС Белгородской области
    'mchs_kursk',              # МЧС Курской области
    'mchs_voronezh',           # МЧС Воронежской области
    'mchs_krasnodar',          # МЧС Краснодарского края
    'mchs_crimea',             # МЧС Крыма
    'rsks_official',           # РСЧС официальный
    'operativny_shtab',        # Оперативный штаб
]

# Уровень 2: Верифицированные OSINT-паблики (85% достоверности)
VERIFIED_OSINT = [
    'radar_rostov_verify',
    'radar_belgorod',
    'radar_kursk',
    'radar_krym',
    'military_observer_rf',
    'avia_alert_russia',
    'fighterbomber',
    'rybar',
    'war_gonzo',
    'readovkanews',
    'baza_news',
    'mash',
    'shot_shot',
    'svodki',
    'operline_z',
]

# Уровень 3: Региональные каналы очевидцев
REGIONAL_SOURCES = {
    'rostov': [
        'radar_rostov', 'rostov_monitor', 'rostov_live',
        'tagil_live', 'bataysk_svodki', 'novocherkassk_news', 'shahty_svodki'
    ],
    'belgorod': ['bel_radar', 'belgorod_operativ', 'belgorod_live'],
    'kursk': ['kursk_radar', 'kursk_alert', 'kursk_live'],
    'bryansk': ['bryansk_radar', 'bryansk_monitor'],
    'voronezh': ['voronezh_radar', 'voronezh_operativ'],
    'krasnodar': ['kuban_alert', 'krasnodar_radar'],
    'crimea': ['crimea_alert', 'sevastopol_radar'],
    'volgograd': ['volgograd_radar', 'volgograd_alert'],
    'lipetsk': ['lipetsk_radar'],
    'orel': ['orel_radar'],
    'tambov': ['tambov_radar'],
}

# Собираем все источники
ALL_SOURCES = OFFICIAL_SOURCES + VERIFIED_OSINT
for sources in REGIONAL_SOURCES.values():
    ALL_SOURCES.extend(sources)

# Ключевые слова для фильтрации
THREAT_KEYWORDS = [
    'бпла', 'беспилот', 'дрон', 'шахед', 'бабай',
    'ракет', 'нептун', 'калибр', 'искандер', 'циркон',
    'атака', 'опасность', 'тревога', 'пуск', 'направлен',
    'в сторону', 'влетел', 'залетел', 'обнаружен',
    'воздушная тревога', 'сирена', 'угроза'
]

CANCEL_KEYWORDS = ['отбой', 'отмен', 'отмена', 'отменили']
