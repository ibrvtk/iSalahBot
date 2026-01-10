from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db_read_user
from app.data import salah_names



kb_yesno = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="👍 Да", callback_data="yesno_yes"),
     InlineKeyboardButton(text="👎 Нет", callback_data="yesno_no")]
])


async def kb_check_salah(salah_key: str) -> InlineKeyboardBuilder:
    inline_keyboard = InlineKeyboardBuilder()
    inline_keyboard.add(InlineKeyboardButton(
        text="✅ Отметить",
        callback_data=f"check_salah_{salah_key}")
    )
    return inline_keyboard.as_markup()


kb_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="⚙️ Настройки")],
    [KeyboardButton(text="📅 Расписание на сегодня"), KeyboardButton(text="📊 Статистика выполнения")],
    [KeyboardButton(text="👥 Добавить в группу")]
],
resize_keyboard=True,
input_field_placeholder="Выберите опцию..."
)


async def kb_settings_pg1(user_id: int) -> InlineKeyboardBuilder:
    inline_keyboard = InlineKeyboardBuilder()

    user_data = await db_read_user(
        arr=user_id,
        sql_from="settings",
        sql_select="madhab, ishraq, shuruq, salah"
    )

    madhab = "Ханафи" if user_data[0] == 0 else "Шафии"
    ishraq = "Откл." if user_data[1] == 0 else "Вкл."
    shuruq = f"{salah_names['shuruq']}а: По-арабски" if user_data[2] == 0 else f"{salah_names['shuruqru']}а: По-русски"
    salah = "Салята: По-арабски" if user_data[3] == 0 else "Намаза: По-русски"

    inline_keyboard.add(InlineKeyboardButton(
        text=f"Мазхаб: {madhab}",
        callback_data=f"settings_madhab"
    ))
    inline_keyboard.add(InlineKeyboardButton(
        text=f"Не показывать {salah_names['ishraq']}: {ishraq}",
        callback_data=f"settings_ishraq"
    ))
    inline_keyboard.add(InlineKeyboardButton(
        text=f"Название {shuruq}",
        callback_data=f"settings_shuruq"
    ))

    inline_keyboard.add(InlineKeyboardButton(
        text=f"Далее ⏭️",
        callback_data=f"settings_pg2"
    ))

    return inline_keyboard.adjust(1).as_markup()

async def kb_settings_pg2(user_id: int) -> InlineKeyboardBuilder:
    inline_keyboard = InlineKeyboardBuilder()

    user_data = await db_read_user(
        arr=user_id,
        sql_from="settings",
        sql_select="statistics"
    )

    statistics = "Откл." if user_data[0] == 0 else "Вкл."

    inline_keyboard.add(InlineKeyboardButton(
        text=f"Не вести статистику в целом: {statistics}",
        callback_data=f"settings_statistics"
    ))
    inline_keyboard.add(InlineKeyboardButton(
        text=f"Сбросить статистику",
        callback_data=f"settings_rmstat"
    ))
    inline_keyboard.add(InlineKeyboardButton(
        text=f"Удалить все мои данные",
        callback_data=f"settings_rmrf"
    ))

    inline_keyboard.add(InlineKeyboardButton(
        text=f"⏮️ Назад",
        callback_data=f"settings_pg1"
    ))

    return inline_keyboard.adjust(1).as_markup()