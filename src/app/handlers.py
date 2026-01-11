from aiogram import Router, F
from aiogram.types import Message, LinkPreviewOptions
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import CommandObject

from pytz import timezone
from datetime import datetime
from timezonefinder import TimezoneFinder

from config import BOT, DEVELOPER_ID
from database import db_read_user, db_get_all_users, db_set_stage
from app.data import stages, UserCity, Registration, registration_data, salah_names, salah_emojis, month_map
from app.utils import get_location, get_pray_times, reply_need_register
from app.keyboards import kb_menu, kb_yesno, kb_settings_pg1


RT = Router()
TZF = TimezoneFinder()



@RT.message(Command('start'))
async def cmd_start(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id

    user_data = await db_read_user(
        arr=user_id,
        sql_from="general",
        return_boolean=True
    )
    if user_data:
        return await message.reply("<b>Вы уже зарегистрированны.</b> Удалить свои данные можно в настройках.")

    await db_set_stage(
        user_id=user_id,
        stage=stages['registration']
    )
    
    await state.set_state(UserCity.city)
    await message.answer(
        "<b>Ас-саляму алейкум.</b>\n\n"
        "Этот бот будет <b>автоматически</b> присылать Вам сообщение, когда нужно совершить салят. "
        "В нём <b>нет рекламы</b>, он не будет писать ничего лишнего.\n"
        "Также можно смотреть количество выполненых и пропущенных моментов.\n\n"
        "На данный момент бот работает <b>только</b> в пределах <b>Российской Федерации</b> и методу <b>Всемирной мусульманской лиги</b>.\n"
        "Просто введите в следующем сообщении название <b>города или поселения</b>, в котором Вы сейчас находитесь. "
        "Позже в настройках можно будет выбрать метод подсчёта: <b>Ханафи либо Шафии <i>(Малики, Ханбали)</i></b>."
    )

@RT.message(UserCity.city)
async def fsm_confirm_city(message: Message) -> None:
    city = message.text
    
    city_data = await get_location(
        city=city,
        return_full=True
    )
    
    if not city_data:
        return await message.answer("<b>Город/поселение не найден(о) или находится вне РФ.</b> Попробуйте снова.")

    if "," in city:
        city = city.split(",")[0]
    lat = round(city_data.latitude, 4)
    lng = round(city_data.longitude, 4)
    user_id = message.from_user.id

    timezone_str = TZF.timezone_at(lng=lng, lat=lat)
    if not timezone_str:
        timezone_str = "Europe/Moscow"

    registration_data[user_id] = Registration(
        user_id=user_id,
        city=city,
        timezone_str=timezone_str,
        lng=lng,
        lat=lat
    )

    await message.answer(
        text=f"<b>{city_data}</b>. Часовой пояс: <b>{timezone_str}</b>. Это верно?",
        reply_markup=kb_yesno
    )


@RT.message(F.text == "⚙️ Настройки")
async def cmd_settings(message: Message) -> None:
    user_id = message.from_user.id
    
    user_data = await db_read_user(
        arr=user_id,
        sql_from="general",
        return_boolean=True
    )
    if not user_data:
        return await reply_need_register(message)

    await message.answer(
        text="<b>⚙️ Настройки</b>\nМазхаб и косметические изменения",
        reply_markup=await kb_settings_pg1(user_id)
    )


@RT.message(F.text == "📅 Расписание на сегодня")
async def cmd_chart(message: Message) -> None:
    try:
        user_id = message.from_user.id
        user_data = await db_read_user(
            arr=user_id,
            sql_from="general",
            sql_select="city, timezone_str, lng, lat"
        )

        if not user_data:
            return await reply_need_register(message)

        pray_times = await get_pray_times(user_id=user_id, lng=user_data[2], lat=user_data[3])
        user_settings = await db_read_user(
            arr=user_id,
            sql_from="settings",
            sql_select="ishraq, shuruq"
        )
        user_settings_ishraq = user_settings[0]
        text_ishraq = f"{salah_emojis['ishraq']} {salah_names['ishraq']} <i>(нафль)</i>: <code>{pray_times['ishraq']}</code>\n" if user_settings_ishraq == 0 else ""
        user_settings_shuruq = user_settings[1]
        shuruq_name = salah_names['shuruq'] if user_settings_shuruq == 0 else salah_names['shuruqru']
        madhab = await db_read_user(
            arr=user_id,
            sql_from="settings",
            sql_select="madhab"
        )
        madhab = "Ханафи" if madhab[0] == 0 else "Шафии, Малики, Ханбали"
        if pray_times:
            user_timezone = timezone(user_data[1])
            now = datetime.now(user_timezone)
            bot = await BOT.get_me()
            text = (
                f"🕋 <b>Расписание на {now.day} {month_map[now.month]} {now.year} года</b>\n"
                f"<i>Город {user_data[0]}, часовой пояс {pray_times['timezone_str']}</i>\n\n"
                f"{salah_emojis['fajr']} {salah_names['fajr']}: <code>{pray_times['fajr']}</code>\n"
                f"{salah_emojis['shuruq']} {shuruq_name}: <code>{pray_times['shuruq']}</code>\n"
                f"{text_ishraq}"
                f"{salah_emojis['zuhr']} {salah_names['zuhr']}: <code>{pray_times['zuhr']}</code>\n"
                f"{salah_emojis['asr']} {salah_names['asr']}: <code>{pray_times['asr']}</code>\n"
                f"{salah_emojis['maghrib']} {salah_names['maghrib']}: <code>{pray_times['maghrib']}</code>\n"
                f"{salah_emojis['isha']} {salah_names['isha']}: <code>{pray_times['isha']}</code>\n\n"
                f"{madhab} ⦁ Всемирная исламская лига\n"
                f"<b>@{bot.username}</b>"
            )
            await message.answer(text)
        else:
            await message.answer("Сервис временно недоступен. Попробуйте позже.")

    except Exception as e:
        print(f"error: app/handlers.py: cmd_chart(): {e}")
        await message.answer("Произошла непредвиденная ошибка. Попробуйте позже.")


@RT.message(F.text == "📊 Статистика выполнения")
async def cmd_salah_statistics(message: Message) -> None:
    user_id = message.from_user.id

    user_data = await db_read_user(
        arr=user_id,
        sql_from="general",
        sql_select="timezone_str"
    )

    if not user_data:
        return await reply_need_register(message)

    user_settings = await db_read_user(
        arr=user_id,
        sql_from="settings",
        sql_select="statistics, ishraq"
    )

    if user_settings[0] == 1:
        return message.reply("<b>Вы отключили ведение статистики.</b> Включить обратно можно в настройках.")

    raw_user_salah = await db_read_user(
        arr=user_id,
        sql_from="salah"
    )
    user_salah = list(raw_user_salah)

    for i in range(9):
        user_salah[i] = "✅" if user_salah[i] == 1 else "❌"

    user_timezone = timezone(user_data[0])
    now = datetime.now(user_timezone)
    text_ishraq = f"{user_salah[3]} {salah_names['ishraq']}\n" if user_settings[1] == 0 else ""
    text_zuhr = f"{user_salah[8]} {salah_names['jumuah']}\n" if datetime.now().weekday() == 4 else f"{user_salah[4]} {salah_names['zuhr']}\n"
    bot = await BOT.get_me()
    text = (
         "📊 <b>Ваша статистика выполнения на сегодня</b>\n"
        f"<i>{now.day} {month_map[now.month]} {now.year} год</i>\n\n"
        f"{user_salah[1]} {salah_names['fajr']}\n"
        f"{text_ishraq}"
        f"{text_zuhr}"
        f"{user_salah[5]} {salah_names['asr']}\n"
        f"{user_salah[6]} {salah_names['maghrib']}\n"
        f"{user_salah[7]} {salah_names['isha']}\n\n"
        f"<b>@{bot.username}</b>"
    )
    await message.answer(text)

@RT.message(F.text == "📊 Общая статистика")
async def cmd_general_statistics(message: Message) -> None:
    user_id = message.from_user.id
    
    user_data = await db_read_user(
        arr=user_id,
        sql_from="general",
        sql_select="timezone_str, registration_date, completed, completed_ishraq, completed_jumuah, missed, missed_jumuah"
    )

    if not user_data:
        return await reply_need_register(message)

    user_settings = await db_read_user(
        arr=user_id,
        sql_from="settings",
        sql_select="statistics, ishraq"
    )

    if user_settings[0] == 1:
        return message.reply("<b>Вы отключили ведение статистики.</b> Включить обратно можно в настройках.")

    user_timezone = timezone(user_data[0])
    registration_date = datetime.fromtimestamp(user_data[1], user_timezone)
    registration_date = registration_date.strftime("%d.%m.%Y %H:%M")
    
    text_ishraq = f"📿 Выполнено {salah_names['ishraq']}: <code>{user_data[3]}</code>\n" if user_settings[1] == 0 else ""
    bot = await BOT.get_me()
    text = (
         "📊 <b>Ваша общая статистика по всем салятам</b>\n"
        f"<i>Дата регистрации в боте: {registration_date}</i>\n\n"
        f"✅ Выполнено Фард: <code>{user_data[2]}</code>\n"
        f"❌ Пропущено Фард: <code>{user_data[5]}</code>\n"
        f"{text_ishraq}"
        f"🌟 Выполнено {salah_names['jumuah']}: <code>{user_data[4]}</code>\n"
        f"🌠 Пропущено {salah_names['jumuah']}: <code>{user_data[6]}</code>\n\n"
        f"<b>@{bot.username}</b>"
    )
    await message.answer(text)


@RT.message(F.text == "👥 Добавить в группу")
async def cmd_add_to_group(message: Message) -> None:
    user_data = await db_read_user(
        arr=message.from_user.id,
        sql_from="general",
        return_boolean=True
    )
    if not user_data:
        return await reply_need_register(message)

    await message.reply("В разработке.")


@RT.message(Command("developer_info"))
async def cmd_developer_info(message: Message):
    bot_github = LinkPreviewOptions(
        url="https://github.com/ibrvtk/iSalahBot",
        prefer_large_media=True,
        show_above_text=False
    )

    await message.reply(
        text=(
            "<b>Разработчик кода</b>: @ibrvtk | <a href='https://github.com/ibrvtk'>GitHub</a> | <a href='https://ibrvtk.site'>Сайт</a>\n"
            "<b>Автор Description анимации:</b> @angelsky1337\n\n"
            "Для определения времени намазов использовался <a href='https://aladhan.com/prayer-times-api'><b>Aladhan API</b></a>.\n"
            "<a href='https://github.com/ibrvtk/iSalahBot'>🐈‍⬛ <b>GitHub Бота</b></a> <i>(full open-source)</i>"
        ),
        link_preview_options=bot_github
    )


@RT.message(Command("echo"), F.from_user.id == DEVELOPER_ID)
async def cmd_echo(message: Message, command: CommandObject):
    args = command.args

    if args is None:
        return await message.delete()

    msg = await message.reply("⏱️")

    users_id = await db_get_all_users()

    for user_id in users_id:
            await BOT.send_message(
                chat_id=user_id,
                text=args,
                reply_markup=kb_menu
            )

    await BOT.edit_message_text(
        chat_id=message.from_user.id,
        message_id=msg.message_id,
        text="✅"
    )