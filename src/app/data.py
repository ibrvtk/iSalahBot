from aiogram.fsm.state import State, StatesGroup

from dataclasses import dataclass



stages = {
    "none": 0,
    "registration": 1,
    "settings_rmstat": 2,
    "settings_rmrf": 3
}


class UserCity(StatesGroup):
    city = State()

@dataclass
class Registration():
    user_id: int
    city: str = None
    timezone_str: str = None
    lng: float = None
    lat: float = None

registration_data = {}


# @dataclass
# class TodaySalah():
#     fajr: 


salah_names = {
    "fajr": "Фаджр",
    "shuruq": "Шурук",
    "ishraq": "Ишрак",
    "zuhr": "Зухр",
    "asr": "Аср",
    "maghrib": "Магриб",
    "isha": "Иша",
    "jumuah": "Джума",
    "shuruqru": "Восход",
}

salah_emojis = {
    "fajr": "🌅",
    "shuruq": "⛔️",
    "ishraq": "📿",
    "zuhr": "🕌",
    "asr": "🌇",
    "maghrib": "🌃",
    "isha": "🎑",
    "jumuah": "🌟"
}


month_map = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
    1488: "Агарта"
}