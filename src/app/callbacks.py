from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from random import choice

from database import db_register_user, db_set_stage, db_read_user, db_update_user, db_delete_user, db_rmstat
from app.data import stages, registration_data, salah_names
from app.keyboards import kb_yesno, kb_menu, kb_settings_pg1, kb_settings_pg2


RT = Router()



@RT.callback_query(F.data.startswith("yesno"))
async def cb_yesno(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    stage = await db_read_user(
        arr=user_id,
        sql_from="stage"
    )
    stage = stage[1]
    answer = callback.data.split("_")[1]

    match answer:
        case "yes":
            if stage == stages['registration']:
                if user_id in registration_data:
                    await db_register_user(
                        user_id=user_id,
                        city=registration_data[user_id].city,
                        timezone_str=registration_data[user_id].timezone_str,
                        lng=registration_data[user_id].lng,
                        lat=registration_data[user_id].lat
                    )
                    await db_update_user(
                        arr_set=callback.from_user.language_code,
                        arr_where=user_id,
                        sql_update="settings",
                        sql_set="language",
                        sql_where="user_id"
                    )
                    del registration_data[user_id]
                    await db_set_stage(user_id, stages['none'])

                    await state.clear()
                    await callback.message.delete()
                    await callback.message.answer(
                        text="<b>Успех.</b> Рекомендуется посмотреть в настройки.",
                        reply_markup=kb_menu
                    )
                else:
                    await callback.message.edit_text(
                        text="<b>Произошёл сбой.</b> Пожалуйста, пройдите регистрацию заново — /start. <b>Спасибо.</b>",
                        reply_markup=None
                    )
            
            if stage == stages['settings_rmstat']:
                await db_rmstat(user_id)
                await callback.answer("↩️ Вы полностью сбросили свою статистику")
                await callback.message.edit_text(
                    text="<b>⚙️ Настройки</b>\nУправление данными",
                    reply_markup=await kb_settings_pg2(user_id)
                )
                await db_set_stage(user_id, 0)
            
            if stage == stages['settings_rmrf']:
                await db_delete_user(user_id)
                await callback.answer("↩️ Вы полностью удалили себя из БД")
                await callback.message.delete()

        case "no":
            if stage == stages['registration']:
                if user_id in registration_data:
                    await callback.message.edit_text(
                        "Попробуйте ввести уточнения, "
                        "например «<code>Москва, Центральный федеральный округ</code>» "
                        "или «<code>Махачкала, городской округ Махачкала, Дагестан, Северо-Кавказский федеральный округ</code>»."
                    )
                    # Не трогаем FSM-состояние; продолжаем принимать город/поселение.
                else:
                    await callback.message.edit_text(
                        text="<b>Произошёл сбой.</b> Пожалуйста, пройдите регистрацию заново — /start.",
                        reply_markup=None
                    )

            if stage == stages['settings_rmstat']:
                await callback.message.edit_text(
                    text="<b>⚙️ Настройки</b>\nУправление данными",
                    reply_markup=await kb_settings_pg2(user_id)
                )

            if stage == stages['settings_rmrf']:
                await callback.message.edit_text(
                    text="<b>⚙️ Настройки</b>\nУправление данными",
                    reply_markup=await kb_settings_pg2(user_id)
                )


@RT.callback_query(F.data.startswith("check_salah"))
async def cb_check_salah(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    salah_key = callback.data.split("_")[2]
    text_mashAllah = ""

    match salah_key:
        case "ishraq":
            user_data = await db_read_user(
                arr=user_id,
                sql_from="general",
                sql_select="completed_ishraq"
            )

            old_ishraq = user_data[0]
            new_ishraq = old_ishraq + 1

            await db_update_user(
                arr_set=new_ishraq,
                arr_where=user_id,
                sql_update="general",
                sql_set="completed_ishraq",
                sql_where="user_id"
            )

            text_mashAllah = "<b>МашАллах!</b>"
        case "jumuah":
            user_data = await db_read_user(
                arr=user_id,
                sql_from="general",
                sql_select="completed_jumuah, missed_jumuah"
            )

            old_completed_jumuah = user_data[0]
            new_completed_jumuah = old_completed_jumuah + 1
            old_missed_jumuah = user_data[1]
            new_missed_jumuah = old_missed_jumuah - 1

            await db_update_user(
                arr_set=new_completed_jumuah,
                arr_where=user_id,
                sql_update="general",
                sql_set="completed_jumuah",
                sql_where="user_id"
            )
            await db_update_user(
                arr_set=new_missed_jumuah,
                arr_where=user_id,
                sql_update="general",
                sql_set="missed_jumuah",
                sql_where="user_id"
            )

            text_mashAllah = "<b>МашАллах!</b>"
        case _:
            user_data = await db_read_user(
                arr=user_id,
                sql_from="general",
                sql_select="completed, missed"
            )

            old_completed = user_data[0]
            new_completed = old_completed + 1
            old_missed = user_data[1]
            new_missed = old_missed - 1

            await db_update_user(
                arr_set=new_completed,
                arr_where=user_id,
                sql_update="general",
                sql_set="completed",
                sql_where="user_id"
            )
            await db_update_user(
                arr_set=new_missed,
                arr_where=user_id,
                sql_update="general",
                sql_set="missed",
                sql_where="user_id"
            )

    await db_update_user(
        arr_set=1,
        arr_where=user_id,
        sql_update="salah",
        sql_set=salah_key,
        sql_where="user_id"
    )

    salah_name = salah_names.get(salah_key)
    # bot = await BOT.get_me()
    completed_emoji = choice(["👍", "👏", "🙏", "🤲"])
    await callback.message.edit_text(
        text=f"{completed_emoji} Намаз <b>{salah_name}</b> выполнен! {text_mashAllah}",#\n<b>@{bot.username}</b>",
        reply_markup=None
    )


@RT.callback_query(F.data.startswith("settings"))
async def cb_settings(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    option = callback.data.split("_")[1]

    user_data = await db_read_user(
        arr=user_id,
        sql_from="settings"
    )

    match option:
        case "madhab":
            arr_set = 1 if user_data[1] == 0 else 0
            await db_update_user(
                arr_set=arr_set,
                arr_where=user_id,
                sql_update="settings",
                sql_set="madhab",
                sql_where="user_id"
            )
            await callback.answer("Изменения вступят в силу в течении 24 часов")
        case "ishraq":
            arr_set = 1 if user_data[2] == 0 else 0
            await db_update_user(
                arr_set=arr_set,
                arr_where=user_id,
                sql_update="settings",
                sql_set="ishraq",
                sql_where="user_id"
            )
        case "shuruq":
            arr_set = 1 if user_data[3] == 0 else 0
            await db_update_user(
                arr_set=arr_set,
                arr_where=user_id,
                sql_update="settings",
                sql_set="shuruq",
                sql_where="user_id"
            )

        case "statistics":
            arr_set = 1 if user_data[4] == 0 else 0
            await db_update_user(
                arr_set=arr_set,
                arr_where=user_id,
                sql_update="settings",
                sql_set="statistics",
                sql_where="user_id"
            )
        case "rmstat":
            await db_set_stage(user_id, stages['settings_rmstat'])
            await callback.message.edit_text(
                text="<b>Вы уверены?</b> Это действие нельзя будет отменить.",
                reply_markup=kb_yesno
            )
        case "rmrf":
            await db_set_stage(user_id, stages['settings_rmrf'])
            await callback.message.edit_text(
                text="<b>Вы уверены?</b> Это действие нельзя будет отменить.",
                reply_markup=kb_yesno
            )

    if option not in ("rmstat", "rmrf"):
        if option in ("pg1", "madhab", "ishraq", "shuruq"):
            await callback.message.edit_text(
                text="<b>⚙️ Настройки</b>\nМазхаб и косметические изменения",
                reply_markup=await kb_settings_pg1(user_id)
            )
        else:
            await callback.message.edit_text(
                text="<b>⚙️ Настройки</b>\nУправление данными",
                reply_markup=await kb_settings_pg2(user_id)
            )