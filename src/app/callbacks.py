from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from random import choice

from database import db_create_user, db_read, db_update, db_delete_user, db_get_language, db_set_stage, db_rmstat
from app.data import UserCity, registration_data
from app.keyboards import kb_yesno, kb_menu, kb_settings_pg1, kb_settings_pg2
from app.localization import phrases


RT = Router()



@RT.callback_query(F.data.startswith("yesno"))
async def cb_yesno(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    l_code = await db_get_language(user_id)
    stage = await db_read(
        arr=user_id,
        sql_from="stage"
    )
    stage = stage[1]
    answer = callback.data.split("_")[1]

    match answer:
        case "yes":
            if stage == 1:
                # Регистрация: подтверждение города;
                if user_id in registration_data:
                    l_code = registration_data[user_id].language

                    await db_create_user(
                        user_id=user_id,
                        city=registration_data[user_id].city,
                        timezone_str=registration_data[user_id].timezone_str,
                        lng=registration_data[user_id].lng,
                        lat=registration_data[user_id].lat,
                        language=registration_data[user_id].language,
                    )
                    del registration_data[user_id]
                    await db_set_stage(user_id, 0)

                    await state.clear()
                    await callback.message.delete()
                    await callback.message.answer(
                        text=phrases[f'registrationSucces-{l_code}'],
                        reply_markup=await kb_menu(l_code)
                    )
                else:
                    await callback.message.edit_text(
                        text=phrases[f'registrationError-{l_code}'],
                        reply_markup=None
                    )
            
            if stage == 2:
                # Настройки: сброс статистики;
                await db_rmstat(user_id)
                await callback.answer(f"↩️ {phrases[f'statisticsReset-{l_code}']}")
                await callback.message.edit_text(
                    text=f"<b>⚙️ {phrases[f'settings-{l_code}'].title()}</b>\n{phrases[f'langAndDataManage-{l_code}']}",
                    reply_markup=await kb_settings_pg2(user_id)
                )
                await db_set_stage(user_id, 0)
            
            if stage == 3:
                # Настройки: полное удаление себя из БД.
                await db_delete_user(user_id)
                await callback.answer(f"↩️ {phrases[f'removedFromDatabase-{l_code}']}")
                await callback.message.delete()

        case "no":
            if stage == 1:
                # Регистрация: подтверждение города;
                if user_id in registration_data:
                    l_code = registration_data[user_id].language
                    await callback.message.edit_text(phrases[f'tryEnterClarifications-{l_code}'])
                    # Не трогаем FSM-состояние; продолжаем принимать город/поселение.
                else:
                    await callback.message.edit_text(
                        text=phrases[f'registrationError-{l_code}'],
                        reply_markup=None
                    )

            if stage == 2:
                # Настройки: сброс статистики;
                await callback.message.edit_text(
                    text=f"<b>⚙️ {phrases[f'settings-{l_code}'].title()}</b>\n{phrases[f'langAndDataManage-{l_code}']}",
                    reply_markup=await kb_settings_pg2(user_id)
                )

            if stage == 3:
                # Настройки: полное удаление себя из БД.
                await callback.message.edit_text(
                    text=f"<b>⚙️ {phrases[f'settings-{l_code}'].title()}</b>\n{phrases[f'langAndDataManage-{l_code}']}",
                    reply_markup=await kb_settings_pg2(user_id)
                )


@RT.callback_query(F.data.startswith("language"))
async def cb_language(callback: CallbackQuery, state: FSMContext) -> None:
    l_code = callback.data.split("_")[1]

    await state.set_state(UserCity.city)
    await state.update_data(language=l_code)

    await callback.message.edit_text(
        text=f"<b>{phrases[f'salam-{l_code}']}.</b>\n\n{phrases[f'cmdStart-{l_code}']}",
        reply_markup=None
    )


@RT.callback_query(F.data.startswith("check_salah"))
async def cb_check_salah(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    l_code = await db_get_language(user_id)
    salah_key = callback.data.split("_")[2]

    match salah_key:
        case "ishraq":
            user_data = await db_read(
                arr=user_id,
                sql_from="general",
                sql_select="completed_ishraq"
            )

            old_ishraq = user_data[0]
            new_ishraq = old_ishraq + 1

            await db_update(
                arr_set=new_ishraq,
                arr_where=user_id,
                sql_update="general",
                sql_set="completed_ishraq"
            )
        case "jumuah":
            user_data = await db_read(
                arr=user_id,
                sql_from="general",
                sql_select="completed_jumuah, missed_jumuah"
            )

            old_completed_jumuah = user_data[0]
            new_completed_jumuah = old_completed_jumuah + 1
            old_missed_jumuah = user_data[1]
            new_missed_jumuah = old_missed_jumuah - 1

            await db_update(
                arr_set=new_completed_jumuah,
                arr_where=user_id,
                sql_update="general",
                sql_set="completed_jumuah"
            )
            await db_update(
                arr_set=new_missed_jumuah,
                arr_where=user_id,
                sql_update="general",
                sql_set="missed_jumuah"
            )
        case _:
            user_data = await db_read(
                arr=user_id,
                sql_from="general",
                sql_select="completed, missed"
            )

            old_completed = user_data[0]
            new_completed = old_completed + 1
            old_missed = user_data[1]
            new_missed = old_missed - 1

            await db_update(
                arr_set=new_completed,
                arr_where=user_id,
                sql_update="general",
                sql_set="completed"
            )
            await db_update(
                arr_set=new_missed,
                arr_where=user_id,
                sql_update="general",
                sql_set="missed"
            )

    await db_update(
        arr_set=1,
        arr_where=user_id,
        sql_update="salah",
        sql_set=salah_key
    )

    user_settings = await db_read(
        arr=user_id,
        sql_from="settings",
        sql_select="salah"
    )

    completed_emoji = choice(["👍", "👏", "🙏", "🤲"])
    text_salah = phrases[f'salah-{l_code}'] if user_settings[0] == 0 else phrases[f'salahLocal-{l_code}']
    salah_name = phrases.get(f"{salah_key}-{l_code}")
    # bot = await BOT.get_me()
    await callback.message.edit_text(
        text=f"{completed_emoji} {text_salah.title()} <b>{salah_name}</b> {phrases[f'completed-{l_code}'][:-1].lower()}! <b>{phrases[f'mashAllah-{l_code}']}!</b>",#\n<b>@{bot.username}</b>",
        reply_markup=None
    )


@RT.callback_query(F.data.startswith("settings"))
async def cb_settings(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    option = callback.data.split("_")[1]
    l_code = await db_get_language(user_id)

    user_data = await db_read(
        arr=user_id,
        sql_from="settings"
    )

    match option:
        case "madhab":
            arr_set = 1 if user_data[1] == 0 else 0
            await db_update(
                arr_set=arr_set,
                arr_where=user_id,
                sql_update="settings",
                sql_set="madhab"
            )
            await callback.answer(phrases[f'changesWillTakeEffect-{l_code}'])
        case "ishraq":
            arr_set = 1 if user_data[2] == 0 else 0
            await db_update(
                arr_set=arr_set,
                arr_where=user_id,
                sql_update="settings",
                sql_set="ishraq"
            )
        case "shuruq":
            arr_set = 1 if user_data[3] == 0 else 0
            await db_update(
                arr_set=arr_set,
                arr_where=user_id,
                sql_update="settings",
                sql_set="shuruq"
            ) 
        case "salah":
            arr_set = 1 if user_data[5] == 0 else 0
            await db_update(
                arr_set=arr_set,
                arr_where=user_id,
                sql_update="settings",
                sql_set="salah"
            )

        case "language":
            arr_set = "en" if user_data[6] == "ru" else "ru"
            await db_update(
                arr_set=arr_set,
                arr_where=user_id,
                sql_update="settings",
                sql_set="language"
            )
            l_code = await db_get_language(user_id)
            await callback.message.answer(
                text=f"{phrases[f'languageHasBeenChanged-{l_code}']} <b>{phrases[f'languageCode-{l_code}']}</b>.",
                reply_markup=await kb_menu(l_code)
            )
        case "statistics":
            arr_set = 1 if user_data[4] == 0 else 0
            await db_update(
                arr_set=arr_set,
                arr_where=user_id,
                sql_update="settings",
                sql_set="statistics"
            )
        case "rmstat":
            await db_set_stage(user_id, 2)
            await callback.message.edit_text(
                text=phrases[f'areYouSure-{l_code}'],
                reply_markup=await kb_yesno(l_code)
            )
        case "rmrf":
            await db_set_stage(user_id, 3)
            await callback.message.edit_text(
                text=phrases[f'areYouSure-{l_code}'],
                reply_markup=await kb_yesno(l_code)
            )

    if option not in ("rmstat", "rmrf"):
        if option in ("pg1", "madhab", "ishraq", "shuruq", "salah"):
            await callback.message.edit_text(
                text=f"<b>⚙️ {phrases[f'settings-{l_code}'].title()}</b>\n{phrases[f'madhabAndCosmetics-{l_code}']}",
                reply_markup=await kb_settings_pg1(user_id)
            )
        else:
            await callback.message.edit_text(
                text=f"<b>⚙️ {phrases[f'settings-{l_code}'].title()}</b>\n{phrases[f'langAndDataManage-{l_code}']}",
                reply_markup=await kb_settings_pg2(user_id)
            )