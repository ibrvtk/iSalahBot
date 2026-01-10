from datetime import datetime
from aiosqlite import connect

from config import DB_DB, DB_SQL



async def db_create_database() -> None:
    try:
        async with connect(DB_DB) as db:
            with open(DB_SQL, 'r', encoding='utf-8') as file:
                sql_script = file.read()
            await db.executescript(sql_script)
            await db.commit()

    except Exception as e:
        print(f"error: database: db_create_database(): {e}")


async def db_create_user(user_id: int) -> None:
    try:
        async with connect(DB_DB) as db:
            await db.execute("INSERT OR IGNORE INTO general (user_id) VALUES (?)", (user_id,))
            await db.execute("INSERT OR IGNORE INTO salah (user_id) VALUES (?)", (user_id,))
            await db.execute("INSERT OR IGNORE INTO settings (user_id) VALUES (?)", (user_id,))
            await db.commit()
            
    except Exception as e:
        print(f"error: database: db_create_user(): {e}")

async def db_register_user(user_id: int, city: str, timezone_str: str, lng: float, lat: float) -> None:
    try:
        async with connect(DB_DB) as db:
            await db.execute("INSERT OR IGNORE INTO general (user_id) VALUES (?)", (user_id,))
            await db.execute("INSERT OR IGNORE INTO salah (user_id) VALUES (?)", (user_id,))
            await db.execute("INSERT OR IGNORE INTO settings (user_id) VALUES (?)", (user_id,))
            
            await db.execute("""
                UPDATE general 
                SET city = ?, timezone_str = ?, lng = ?, lat = ?, registration_date = ?
                WHERE user_id = ?
            """, (city, timezone_str, lng, lat, int(datetime.now().timestamp()), user_id,))
            
            await db.commit()

    except Exception as e:
        print(f"error: database: db_register_user(): {e}")

async def db_set_stage(user_id: int, stage: str) -> None:
    try:
        async with connect(DB_DB) as db:
            await db.execute("INSERT OR IGNORE INTO stage (user_id) VALUES (?)", (user_id,))
            
            await db.execute("""
                UPDATE stage 
                SET stage = ?
                WHERE user_id = ?
            """, (stage, user_id,))
            
            await db.commit()

    except Exception as e:
        print(f"error: database: db_set_stage(): {e}")


async def db_read_user(arr, sql_from: str, sql_where: str = "user_id", sql_select: str = "*", return_boolean: bool = False) -> dict | bool | None:
    '''
    * `arr` — требуемое значение параметра `sql_where`;
    * `sql_from` — в какой таблице нужно произвести операцию;
    * `sql_where` — какой параметр нужно прочитать. По умолчанию "user_id" *(т. к. PRIMARY KEY)*;
    * `sql_select` — какие параметры нужно вернуть? По умолчанию "\*" *(вернёт все)*;
    * `return_boolean` — если True, то вернёт факт наличия человека в таблице *(True если он там есть. Иначе False)*.
    Требует только параметры `arr` и `sql_from`.
    По умолчанию False.
    '''
    try:
        async with connect(DB_DB) as db:
            if not return_boolean:
                async with db.execute(f"SELECT {sql_select} FROM {sql_from} WHERE {sql_where} = ?", (arr,)) as cursor:
                    return await cursor.fetchone()
            
            else:
                async with db.execute(f"SELECT user_id FROM {sql_from} WHERE user_id = ?", (arr,)) as cursor:
                    user_data = await cursor.fetchone()

                    if not user_data:
                        return False
                    else:
                        return True

    except Exception as e:
        print(f"error: database: db_read_user(): {e}")
        return None

async def db_update_user(arr_set, arr_where, sql_update: str, sql_set: str, sql_where: str) -> None:
    '''
    * `arr_set` — требуемое значение параметра `sql_set`;
    * `arr_where` — требуемое значение параметра `sql_where`;
    * `sql_update` — в какой таблице нужно произвести операцию;
    * `sql_set` — какой параметр нужно обновить;
    * `sql_where` — обновить всех, у кого `sql_where` равен `arr_where`.
    '''
    try:
        async with connect(DB_DB) as db:
            await db.execute(f"UPDATE {sql_update} SET {sql_set} = ? WHERE {sql_where} = ?", (arr_set, arr_where))
            await db.commit()

    except Exception as e:
        print(f"error: database: db_update_user(): {e}")


async def db_delete_user(user_id: int) -> None:
    async with connect(DB_DB) as db:
        await db.execute("DELETE FROM general WHERE user_id = ?", (user_id,))
        await db.execute("DELETE FROM salah WHERE user_id = ?", (user_id,))
        await db.execute("DELETE FROM settings WHERE user_id = ?", (user_id,))
        await db.execute("DELETE FROM stage WHERE user_id = ?", (user_id,))
        await db.commit()

async def db_rmstat(user_id: int):
    try:
        async with connect(DB_DB) as db:
            await db.execute("""
                UPDATE general 
                SET completed = 0, completed_ishraq = 0, completed_jumuah = 0, missed = 0, missed_jumuah = 0
                WHERE user_id = ?
            """, (user_id,))
            await db.commit()

    except Exception as e:
        print(f"error: database: db_rmstat(): {e}")