from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db_read_user, db_get_language
from app.localization import phrases



async def kb_yesno(l_code: str) -> InlineKeyboardMarkup:
    inline_keyboard = InlineKeyboardBuilder()

    inline_keyboard.add(InlineKeyboardButton(
        text=f"👍 {phrases[f'yes-{l_code}'].title()}",
        callback_data="yesno_yes"
    ))
    inline_keyboard.add(InlineKeyboardButton(
        text=f"👎 {phrases[f'no-{l_code}'].title()}",
        callback_data="yesno_no"
    ))

    return inline_keyboard.adjust(2).as_markup()

# async def kb_ok(l_code) -> InlineKeyboardMarkup:
#     inline_keyboard = InlineKeyboardBuilder()
#     inline_keyboard.add(InlineKeyboardButton(
#         text=f"✅ {phrases[f'ok-{l_code}']}",
#         callback_data="ok"
#     ))
#     return inline_keyboard.as_markup()


async def kb_language() -> InlineKeyboardMarkup:
    inline_keyboard = InlineKeyboardBuilder()

    inline_keyboard.add(InlineKeyboardButton(
        text="🇷🇺 Русский язык",
        callback_data="language_ru"
    ))
    inline_keyboard.add(InlineKeyboardButton(
        text="🇬🇧 English language",
        callback_data="language_en"
    ))

    return inline_keyboard.as_markup()


async def kb_check_salah(l_code: str, salah_key: str) -> InlineKeyboardMarkup:
    inline_keyboard = InlineKeyboardBuilder()

    inline_keyboard.add(InlineKeyboardButton(
        text=f"✅ {phrases[f'check-{l_code}']}",
        callback_data=f"check_salah_{salah_key}")
    )

    return inline_keyboard.as_markup()


async def kb_menu(l_code: str,) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=f"🕋 {phrases[f'scheduleFor-{l_code}']} {phrases[f'today-{l_code}']}")],
        [KeyboardButton(text=f"📊 {phrases[f'completionStatistics-{l_code}']}"), KeyboardButton(text=f"📊 {phrases[f'generalStatistics-{l_code}']}")],
        [KeyboardButton(text=f"⚙️ {phrases[f'settings-{l_code}'].title()}")],
        [KeyboardButton(text=f"👥 {phrases[f'addToGroup-{l_code}']}")]
    ],
    resize_keyboard=True,
    input_field_placeholder=f"{phrases[f'chooseOption-{l_code}']}"
    )

    return keyboard


async def kb_settings_pg1(user_id: int) -> InlineKeyboardMarkup:
    inline_keyboard = InlineKeyboardBuilder()
    l_code = await db_get_language(user_id)

    user_data = await db_read_user(
        arr=user_id,
        sql_from="settings",
        sql_select="madhab, ishraq, shuruq, salah"
    )


    madhab = phrases[f'hanafi-{l_code}'] if user_data[0] == 0 else phrases[f'shafii-{l_code}']
    ishraq = phrases[f'off-{l_code}'] if user_data[1] == 0 else phrases[f'on-{l_code}']
    shuruq = f"{phrases[f'shuruq-{l_code}']}{phrases[f'endRuA-{l_code}']}: {phrases[f'inArabic-{l_code}']}" if user_data[2] == 0 else f"{phrases[f'shuruqLocal-{l_code}']}{phrases[f'endRuA-{l_code}']}: {phrases[f'inLocal-{l_code}']}"
    salah = f"{phrases[f'salah-{l_code}']}{phrases[f'endRuA-{l_code}']}: {phrases[f'inArabic-{l_code}']}" if user_data[3] == 0 else f"{phrases[f'salahLocal-{l_code}']}{phrases[f'endRuA-{l_code}']}: {phrases[f'inLocal-{l_code}']}"

    inline_keyboard.add(InlineKeyboardButton(
        text=f"{phrases[f'madhab-{l_code}'].title()}: {madhab}",
        callback_data="settings_madhab"
    ))
    inline_keyboard.add(InlineKeyboardButton(
        text=f"{phrases[f'dont-{l_code}']} {phrases[f'show-{l_code}']} {phrases[f'ishraq-{l_code}']}: {ishraq}",
        callback_data="settings_ishraq"
    ))
    inline_keyboard.add(InlineKeyboardButton(
        text=f"{phrases[f'nameOf-{l_code}']} {shuruq}",
        callback_data="settings_shuruq"
    ))
    inline_keyboard.add(InlineKeyboardButton(
        text=f"{phrases[f'nameOf-{l_code}']} {salah}",
        callback_data="settings_salah"
    ))
    inline_keyboard.add(InlineKeyboardButton(
        text=f"{phrases[f'next-{l_code}']} ⏭️",
        callback_data="settings_pg2"
    ))

    return inline_keyboard.adjust(1).as_markup()

async def kb_settings_pg2(user_id: int) -> InlineKeyboardMarkup:
    inline_keyboard = InlineKeyboardBuilder()
    l_code = await db_get_language(user_id)

    user_data = await db_read_user(
        arr=user_id,
        sql_from="settings",
        sql_select="statistics"
    )


    statistics = phrases[f'off-{l_code}'] if user_data[0] == 0 else phrases[f'on-{l_code}']

    inline_keyboard.add(InlineKeyboardButton(
        text=f"{phrases[f'language-{l_code}']}: {phrases[f'languageCode-{l_code}']}",
        callback_data="settings_language"
    ))
    inline_keyboard.add(InlineKeyboardButton(
        text=f"{phrases[f'dont-{l_code}']} {phrases[f'keepStatistics-{l_code}']}: {statistics}",
        callback_data="settings_statistics"
    ))
    inline_keyboard.add(InlineKeyboardButton(
        text=phrases[f'resetStatistics-{l_code}'],
        callback_data="settings_rmstat"
    ))
    inline_keyboard.add(InlineKeyboardButton(
        text=phrases[f'deleteMyData-{l_code}'],
        callback_data="settings_rmrf"
    ))

    inline_keyboard.add(InlineKeyboardButton(
        text=f"⏮️ {phrases[f'previous-{l_code}']}",
        callback_data="settings_pg1"
    ))

    return inline_keyboard.adjust(1).as_markup()