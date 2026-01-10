from aiogram.types import Message

from aiohttp import ClientSession
from asyncio import get_event_loop
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim

from config import BOT
from database import db_read_user


GEOLOCATOR = Nominatim(user_agent="telegram_bot-iSalahBot")



async def get_location(city: str, return_full: bool = False) -> dict | None:
    '''
    * `city` — название искомого города;
    * `return_full` — вернёт полный список данных `geolocator.geocode()`, а не только долготу и широту.  
    *Написать функцию помог ИИ (Gemini 3 Flash Preview)*
    '''
    loop = get_event_loop()
    location = await loop.run_in_executor(
        None, 
        lambda: GEOLOCATOR.geocode(query=f"{city}, Россия", language="ru")
    )

    if location:
        return location if return_full else (location.longitude, location.latitude)
    return None


async def get_pray_times(user_id: int, lng: float, lat: float) -> dict:
    '''
    **Параметры API:**
    * `method=3` *(Всемирная мусульманская лига)*;
    * `school={madhab}`
        * `1` - Ханафи
        * `0` - Шафии, Малики, Ханбали
    '''
    madhab = await db_read_user(
        arr=user_id,
        sql_from="settings",
        sql_select="madhab"
    )
    madhab = 1 if madhab[0] == 0 else 0
    url = f"https://api.aladhan.com/v1/timings?latitude={lat}&longitude={lng}&method=3&school={madhab}"
    
    async with ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                times = data['data']['timings']
                meta = data['data']['meta']

                shuruq_str = times['Sunrise']
                shuruq_datetime = datetime.strptime(shuruq_str, "%H:%M")
                ishraq_datime = shuruq_datetime + timedelta(minutes=20)
                ishraq_str = ishraq_datime.strftime("%H:%M")
                
                return {
                    "timezone_str": meta['timezone'],
                    "fajr": times['Fajr'],
                    "shuruq": times['Sunrise'],
                    "ishraq": ishraq_str,
                    "zuhr": times['Dhuhr'],
                    "asr": times['Asr'],
                    "maghrib": times['Maghrib'],
                    "isha": times['Isha']
                }
            else:
                return None


async def reply_need_register(message: Message):
    bot = await BOT.get_me()
    await message.reply(
        text=f"Валидная команда, но сначала нужно <a href='https://t.me/{bot.username}?start=retry'>зарегистрироваться</a>.",
        disable_web_page_preview=True
    )