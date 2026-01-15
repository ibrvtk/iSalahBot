from pytz import timezone, utc
from datetime import datetime
from aiosqlite import connect
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT, DB_DB
from database import db_update_user
from app.data import salah_emojis
from app.utils import get_pray_times
from app.keyboards import kb_check_salah
from app.localization import phrases


SCHEDULER = AsyncIOScheduler(timezone="Europe/Moscow")



async def update_daily_timings():
    '''
    Daily Refresh
    '''
    async with connect(DB_DB) as db:
        async with db.execute("""
            SELECT g.lat, g.lng, s.madhab 
            FROM general g
            JOIN settings s ON g.user_id = s.user_id
            GROUP BY g.lat, g.lng, s.madhab
        """) as cursor:
            unique_groups = await cursor.fetchall()

        for lat, lng, madhab in unique_groups:
            async with db.execute("""
                SELECT g.user_id FROM general g 
                JOIN settings s ON g.user_id = s.user_id
                WHERE g.lat = ? AND g.lng = ? AND s.madhab = ?
                LIMIT 1
            """, (lat, lng, madhab)) as user_cursor:
                reference_user = await user_cursor.fetchone()
                if not reference_user: continue

                times = await get_pray_times(reference_user[0], lng, lat)
                if times:
                    await db.execute("""
                        INSERT OR REPLACE INTO timings (user_id, fajr, shuruq, ishraq, zuhr, asr, maghrib, isha)
                        SELECT g.user_id, ?, ?, ?, ?, ?, ?, ?
                        FROM general g
                        JOIN settings s ON g.user_id = s.user_id
                        WHERE g.lat = ? AND g.lng = ? AND s.madhab = ?
                    """, (times['fajr'], times['shuruq'], times['ishraq'], 
                          times['zuhr'], times['asr'], times['maghrib'], times['isha'],
                          lat, lng, madhab))

        await db.execute("UPDATE salah SET fajr=0, shuruq=0, ishraq=0, zuhr=0, asr=0, maghrib=0, isha=0, jumuah=0")
        await db.commit()

async def check_and_notify():
    '''
    Ticker
    '''
    utc_time_now = datetime.now(utc)
    bot = await BOT.get_me()
    bot_username = f"@{bot.username}"

    async with connect(DB_DB) as db:
        async with db.execute("""
            SELECT g.user_id, g.timezone_str, g.missed, g.missed_jumuah, t.fajr, t.shuruq, t.ishraq, t.zuhr, t.asr, t.maghrib, t.isha,
                   s.ishraq as hide_ishraq, s.shuruq as rus_shuruq, s.statistics, s.salah, s.language
            FROM general g
            JOIN timings t ON g.user_id = t.user_id
            JOIN settings s ON g.user_id = s.user_id
        """) as cursor:
            rows = await cursor.fetchall()

        for row in rows:
            uid, user_timezone_str, old_missed, old_missed_jumuah, fajr, shuruq, ishraq, zuhr, asr, maghrib, isha, settings_ishraq, settings_shuruq, settings_statistics, settings_salah, l_code = row

            try:
                user_timezone = timezone(user_timezone_str)
                user_time_now = utc_time_now.astimezone(user_timezone).strftime("%H:%M")
            except: continue

            prayers = [
                ("fajr", fajr), ("shuruq", shuruq), ("ishraq", ishraq),
                ("zuhr", zuhr), ("asr", asr), ("maghrib", maghrib), ("isha", isha)
            ]

            for salah_key, salah_time in prayers:
                if user_time_now == salah_time:
                    salah_name = phrases.get(f'{salah_key}-{l_code}')
                    salah_emoji = salah_emojis.get(salah_key)

                    text_salah = phrases[f'salah-{l_code}'] if settings_salah == 0 else phrases[f'salahLocal-{l_code}']

                    if datetime.now().weekday() == 4 and salah_key == "zuhr":
                        # Если пятница, то переименовать Зухр, в Джума.
                        salah_key = "jumuah"
                        salah_name = phrases.get(f'{salah_key}-{l_code}')
                        salah_emoji = salah_emojis.get(salah_key)

                    if salah_key == "shuruq" and settings_shuruq == 1:
                        # Переименование Шурука в Восход (если нужно).
                        salah_name = phrases[f'shuruqLocal-{l_code}']

                    if salah_key == "ishraq" and settings_ishraq == 1:
                        # Не писать про Ишрак.
                        continue

                    # Вывод.
                    text = ""
                    if settings_statistics == 0:
                        reply_markup = await kb_check_salah(l_code, salah_key)
                    else:
                        reply_markup = None

                    match salah_key:
                        case "fajr":
                            text = (
                                f"{salah_emoji} <b>{phrases[f'salam-{l_code}']}.</b> "
                                f"{phrases[f'time-{l_code}']} {text_salah}{phrases[f'endRuA-{l_code}']} <b>{salah_name}</b> {phrases[f'hasCome-{l_code}']}.\n<b>{bot_username}</b>"
                            )
                        case "shuruq":
                            text = (
                                f"{salah_emoji} {phrases[f'time-{l_code}']} <b>{salah_name}</b> {phrases[f'hasCome-{l_code}']}. "
                                f"{phrases[f'perform-{l_code}'].title()} {text_salah} {phrases[f'before-{l_code}']} {phrases[f'ishraq-{l_code}']}{phrases[f'endRuA-{l_code}']} {phrases[f'enIs-{l_code}']} <b>{phrases[f'prohibited-{l_code}']}</b>.\n<b>{bot_username}</b>"
                            )
                            reply_markup = None
                        case "ishraq":
                            text = (
                                f"{salah_emoji} {phrases[f'time-{l_code}']} {text_salah}{phrases[f'endRuA-{l_code}']} <b>{salah_name}</b> {phrases[f'hasCome-{l_code}']}. "
                                f"{phrases[f'notNecessaryButHalal-{l_code}']}\n<b>{bot_username}</b>"
                            )
                        case "jumuah":
                            text = (
                                f"{salah_emoji} <b>{phrases[f'today-{l_code}'].title()} {phrases[f'enIs-{l_code}']} {phrases[f'friday-{l_code}']}.</b> "
                                f"{phrases[f'needToGoMosqueAndDoThe-{l_code}']} <b>{salah_name}-{text_salah}</b>.\n<b>{bot_username}</b>"
                            )
                            if settings_statistics == 0:
                                new_missed_jumuah = old_missed_jumuah + 1
                                await db_update_user(
                                    arr_set=new_missed_jumuah,
                                    arr_where=uid,
                                    sql_update="general",
                                    sql_set="missed_jumuah"
                                )
                            else:
                                pass
                        case "isha":
                            text = (
                                f"{salah_emoji} <b>{phrases[f'salam-{l_code}']}.</b> "
                                f"{phrases[f'time-{l_code}']} {text_salah}{phrases[f'endRuA-{l_code}']} <b>{salah_name}</b> {phrases[f'hasCome-{l_code}']}.\n<b>{bot_username}</b>"
                            )
                        case _:
                            text = f"{salah_emoji} {phrases[f'time-{l_code}']} {text_salah}{phrases[f'endRuA-{l_code}']} <b>{salah_name}</b> {phrases[f'hasCome-{l_code}']}.\n<b>{bot_username}</b>"

                    if salah_key not in ("shuruq", "ishraq", "jumuah"):
                        if settings_statistics == 0:
                            new_missed = old_missed + 1
                            await db_update_user(
                                arr_set=new_missed,
                                arr_where=uid,
                                sql_update="general",
                                sql_set="missed"
                            )
                        else:
                            pass

                    try:
                        await BOT.send_message(
                            chat_id=uid,
                            text=text,
                            reply_markup=reply_markup
                        )

                    except:
                        pass

def start_scheduler():
    SCHEDULER.add_job(check_and_notify, "cron", second=1)    
    SCHEDULER.add_job(update_daily_timings, "cron", hour=0, minute=1)
    SCHEDULER.start()