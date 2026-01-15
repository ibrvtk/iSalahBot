from aiogram.fsm.state import State, StatesGroup

from dataclasses import dataclass



class UserCity(StatesGroup):
    city = State()

@dataclass
class RegistrationDataclass():
    user_id: int
    city: str = None
    timezone_str: str = None
    lng: float = None
    lat: float = None
    language: str = None

registration_data = {}


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
    "1-ru": "января", "2-ru": "февраля", "3-ru": "марта", "4-ru": "апреля",
    "5-ru": "мая", "6-ru": "июня", "7-ru": "июля", "8-ru": "августа",
    "9-ru": "сентября", "10-ru": "октября", "11-ru": "ноября", "12-ru": "декабря",

    "1-en": "January", "2-en": "February", "3-en": "March", "4-en": "April",
    "5-en": "May", "6-en": "July", "7-en": "June", "8-en": "August",
    "9-en": "September", "10-en": "October", "11-en": "November", "12-en": "December",
}