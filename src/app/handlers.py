from aiogram import Router, F
from aiogram.types import Message, LinkPreviewOptions
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import CommandObject

from pytz import timezone
from datetime import datetime
from timezonefinder import TimezoneFinder

from config import BOT, DEVELOPER_ID
from database import db_read, db_get_all_users, db_get_language, db_set_stage
from app.data import UserCity, RegistrationDataclass, registration_data, salah_emojis, month_map
from app.utils import get_location, get_pray_times, reply_need_register
from app.keyboards import kb_yesno, kb_language, kb_menu, kb_settings_pg1
from app.localization import phrases


RT = Router()
TZF = TimezoneFinder()



@RT.message(Command("start"))
async def cmd_start(message: Message) -> None:
    user_id = message.from_user.id

    user_data = await db_read(
        arr=user_id,
        sql_from="general",
        return_boolean=True
    )

    if user_data:
        l_code = await db_get_language(user_id)
        return await message.reply(phrases[f'cmdStartAlready-{l_code}'])
    if user_id in registration_data:
        return await message.delete()

    await db_set_stage(
        user_id=user_id,
        stage=1
    )

    await message.answer(
        text="Выберите язык\nWich language do your prefer?",
        reply_markup=await kb_language()
    )

@RT.message(UserCity.city)
async def fsm_confirm_city(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    city = message.text
    data = await state.get_data()
    l_code = data['language']
    
    city_data = await get_location(
        city=city,
        return_full=True
    )

    if not city_data:
        return await message.answer(phrases[f'cityNotFound-{l_code}'])

    if "," in city:
        city = city.split(",")[0]
    lat = round(city_data.latitude, 4)
    lng = round(city_data.longitude, 4)

    timezone_str = TZF.timezone_at(lng=lng, lat=lat)
    if not timezone_str:
        timezone_str = "Europe/Moscow"

    registration_data[user_id] = RegistrationDataclass(
        user_id=user_id,
        city=city,
        timezone_str=timezone_str,
        lng=lng,
        lat=lat,
        language=l_code,
    )

    await message.answer(
        text=f"<b>{city_data}</b>. {phrases[f'timezone-{l_code}'].title()}: <b>{timezone_str}</b>. {phrases[f'isThatRight-{l_code}']}",
        reply_markup=await kb_yesno(l_code)
    )


@RT.message(F.text == "🕋 Расписание на сегодня")
@RT.message(F.text == "🕋 Schedule for today")
async def cmd_chart(message: Message) -> None:
    user_id = message.from_user.id
    l_code = await db_get_language(user_id)

    try:
        user_data = await db_read(
            arr=user_id,
            sql_from="general",
            sql_select="city, timezone_str, lng, lat"
        )

        if not user_data:
            return await reply_need_register(message)

        user_settings = await db_read(
            arr=user_id,
            sql_from="settings",
            sql_select="ishraq, shuruq"
        )

        pray_times = await get_pray_times(user_id=user_id, lng=user_data[2], lat=user_data[3])

        user_timezone = timezone(user_data[1])
        now = datetime.now(user_timezone)

        shuruq_name = phrases[f'shuruq-{l_code}'] if user_settings[1] == 0 else phrases[f'shuruqLocal-{l_code}']
        text_ishraq = f"{salah_emojis['ishraq']} {phrases[f"ishraq-{l_code}"]} <i>({phrases[f'nafl-{l_code}']})</i>: <code>{pray_times['ishraq']}</code>\n" if user_settings[0] == 0 else ""
        zuhr_name = f"{salah_emojis['jumuah']} {phrases[f'jumuah-{l_code}']}" if now.weekday() == 4 else f"{salah_emojis['zuhr']} {phrases[f'zuhr-{l_code}']}"
        madhab = await db_read(
            arr=user_id,
            sql_from="settings",
            sql_select="madhab"
        )
        madhab = phrases[f'hanafi-{l_code}'] if madhab[0] == 0 else phrases[f'shafii-{l_code}']

        if pray_times:
            bot = await BOT.get_me()
            text = (
                f"🕋 <b>{phrases[f'scheduleFor-{l_code}']} {now.day} {month_map[f'{now.month}-{l_code}']} {now.year} {phrases[f'year-{l_code}']}</b>\n"
                f"<i>{phrases[f'city-{l_code}'].title()} {user_data[0]}, {phrases[f'timezone-{l_code}']} {pray_times['timezone_str']}</i>\n\n"
                f"{salah_emojis['fajr']} {phrases[f'fajr-{l_code}']}: <code>{pray_times['fajr']}</code>\n"
                f"{salah_emojis['shuruq']} {shuruq_name}: <code>{pray_times['shuruq']}</code>\n"
                f"{text_ishraq}"
                f"{zuhr_name}: <code>{pray_times['zuhr']}</code>\n"
                f"{salah_emojis['asr']} {phrases[f'asr-{l_code}']}: <code>{pray_times['asr']}</code>\n"
                f"{salah_emojis['maghrib']} {phrases[f'maghrib-{l_code}']}: <code>{pray_times['maghrib']}</code>\n"
                f"{salah_emojis['isha']} {phrases[f'isha-{l_code}']}: <code>{pray_times['isha']}</code>\n\n"
                f"{madhab} ⦁ {phrases[f'muslimWorldLeague-{l_code}']}\n"
                f"<b>@{bot.username}</b>"
            )
            await message.answer(text)
        else:
            await message.answer(phrases[f'serviceUnaviable-{l_code}'])

    except Exception as e:
        print(f"error: app/handlers.py: cmd_chart(): {e}")
        await message.answer(phrases[f'serviceUnaviable-{l_code}'])


@RT.message(F.text == "📊 Статистика выполнения")
@RT.message(F.text == "📊 Completion statistics")
async def cmd_salah_statistics(message: Message) -> None:
    user_id = message.from_user.id
    l_code = await db_get_language(user_id)

    user_data = await db_read(
        arr=user_id,
        sql_from="general",
        sql_select="timezone_str"
    )

    if not user_data:
        return await reply_need_register(message)

    user_settings = await db_read(
        arr=user_id,
        sql_from="settings",
        sql_select="statistics, ishraq"
    )

    if user_settings[0] == 1:
        return message.reply(phrases[f'statisticsIsOff-{l_code}'])

    raw_user_salah = await db_read(
        arr=user_id,
        sql_from="salah"
    )
    user_salah = list(raw_user_salah)

    for i in range(9):
        user_salah[i] = "✅" if user_salah[i] == 1 else "❌"

    user_timezone = timezone(user_data[0])
    now = datetime.now(user_timezone)
    text_ishraq = f"{user_salah[3]} {phrases[f'ishraq-{l_code}']}\n" if user_settings[1] == 0 else ""
    text_zuhr = f"{user_salah[8]} {phrases[f'jumuah-{l_code}']}\n" if now.weekday() == 4 else f"{user_salah[4]} {phrases[f'zuhr-{l_code}']}\n"
    bot = await BOT.get_me()
    text = (
        f"📊 <b>{message.from_user.first_name}{phrases[f'endEnS-{l_code}']} {phrases[f'yourSalahStatistics-{l_code}']} {phrases[f'today-{l_code}']}</b>\n"
        f"<i>{now.day} {month_map[f'{now.month}-{l_code}']} {now.year} {phrases[f'year-{l_code}']}</i>\n\n"
        f"{user_salah[1]} {phrases[f'fajr-{l_code}']}\n"
        f"{text_ishraq}"
        f"{text_zuhr}"
        f"{user_salah[5]} {phrases[f'asr-{l_code}']}\n"
        f"{user_salah[6]} {phrases[f'maghrib-{l_code}']}\n"
        f"{user_salah[7]} {phrases[f'isha-{l_code}']}\n\n"
        f"<b>@{bot.username}</b>"
    )
    await message.answer(text)

@RT.message(F.text == "📊 Общая статистика")
@RT.message(F.text == "📊 General statistics")
async def cmd_general_statistics(message: Message) -> None:
    user_id = message.from_user.id
    l_code = await db_get_language(user_id)
    
    user_data = await db_read(
        arr=user_id,
        sql_from="general",
        sql_select="timezone_str, registration_date, completed, completed_ishraq, completed_jumuah, missed, missed_jumuah"
    )

    if not user_data:
        return await reply_need_register(message)

    user_settings = await db_read(
        arr=user_id,
        sql_from="settings",
        sql_select="statistics, ishraq, salah"
    )

    if user_settings[0] == 1:
        return message.reply(phrases[f'statisticsIsOff-{l_code}'])

    user_timezone = timezone(user_data[0])
    registration_date = datetime.fromtimestamp(user_data[1], user_timezone)
    registration_date = registration_date.strftime("%d.%m.%Y %H:%M")
    
    text_ishraq = f"📿 {phrases[f'completed-{l_code}']} {phrases[f'ishraq-{l_code}']}: <code>{user_data[3]}</code>\n" if user_settings[1] == 0 else ""
    text_salah = f"{phrases[f'salah-{l_code}']}{phrases[f'endAm-{l_code}']}" if user_settings[2] == 0 else f"{phrases[f'salahLocal-{l_code}']}{phrases[f'endAm-{l_code}']}"
    bot = await BOT.get_me()
    text = (
        f"📊 <b>{message.from_user.first_name}{phrases[f'endEnS-{l_code}']} {phrases[f'yourGeneralStatistics-{l_code}']} {text_salah}</b>\n"
        f"<i>{phrases[f'registrationInBotDate-{l_code}']}: {registration_date}</i>\n\n"
        f"✅ {phrases[f'completed-{l_code}']} {phrases[f'fard-{l_code}']}: <code>{user_data[2]}</code>\n"
        f"❌ {phrases[f'missed-{l_code}']} {phrases[f'fard-{l_code}']}: <code>{user_data[5]}</code>\n"
        f"{text_ishraq}"
        f"🌟 {phrases[f'completed-{l_code}']} {phrases[f'jumuah-{l_code}']}: <code>{user_data[4]}</code>\n"
        f"🌠 {phrases[f'missed-{l_code}']} {phrases[f'jumuah-{l_code}']}: <code>{user_data[6]}</code>\n\n"
        f"<b>@{bot.username}</b>"
    )
    await message.answer(text)


@RT.message(F.text == "⚙️ Настройки")
@RT.message(F.text == "⚙️ Settings")
async def cmd_settings(message: Message) -> None:
    user_id = message.from_user.id
    l_code = await db_get_language(user_id)

    user_data = await db_read(
        arr=user_id,
        sql_from="general",
        return_boolean=True
    )
    if not user_data:
        return await reply_need_register(message)

    await message.answer(
        text=f"<b>⚙️ {phrases[f'settings-{l_code}'].title()}</b>\n{phrases[f'madhabAndCosmetics-{l_code}']}",
        reply_markup=await kb_settings_pg1(user_id)
    )


@RT.message(F.text == "👥 Добавить в группу")
@RT.message(F.text == "👥 Add to group")
async def cmd_add_to_group(message: Message) -> None:
    user_id = message.from_user.id
    l_code = await db_get_language(user_id)
    
    user_data = await db_read(
        arr=user_id,
        sql_from="general",
        return_boolean=True
    )

    if not user_data:
        return await reply_need_register(message)

    await message.reply(phrases[f'comingSoon-{l_code}'])


@RT.message(Command("developer_info"))
async def cmd_developer_info(message: Message):
    l_code = message.from_user.language_code

    bot_github = LinkPreviewOptions(
        url="https://github.com/ibrvtk/iSalahBot",
        prefer_large_media=True,
        show_above_text=False
    )

    await message.reply(
        text=(
            f"<b>{phrases[f'codeDeveloper-{l_code}']}:</b> @ibrvtk | <a href='https://github.com/ibrvtk'>GitHub</a> | <a href='https://ibrvtk.site'>{phrases[f'site-{l_code}']}</a>\n"
            f"<b>{phrases[f'translateRuEn-{l_code}']}:</b> @ibrvtk\n"
            f"<b>{phrases[f'animationAuthor-{l_code}']}:</b> @angelsky1337\n\n"
            f"{phrases[f'aladhanApiWasUsed-{l_code}']} <a href='https://aladhan.com/prayer-times-api'><b>Aladhan API</b></a>.\n"
            f"<a href='https://github.com/ibrvtk/iSalahBot'>🐈‍⬛ <b>{phrases[f'botGithub-{l_code}']}</b></a> <i>(full open-source)</i>"
        ),
        link_preview_options=bot_github
    )


@RT.message(Command("echo"))#, F.from_user.id == DEVELOPER_ID)
async def cmd_echo(message: Message, command: CommandObject):
    args = command.args

    if args is None:
        return await message.delete()

    msg = await message.reply("⏱️")

    users_id = await db_get_all_users()

    for user_id in users_id:
            l_code = await db_get_language(user_id)
            await BOT.send_message(
                chat_id=user_id,
                text=args,
                reply_markup=await kb_menu(l_code)
            )

    await BOT.edit_message_text(
        chat_id=message.from_user.id,
        message_id=msg.message_id,
        text="✅"
    )