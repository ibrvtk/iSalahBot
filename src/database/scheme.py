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


async def db_create_user(user_id: int, city: str, timezone_str: str, lng: float, lat: float, language: str) -> None:
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

            await db.execute("""
                UPDATE settings 
                SET language = ?
                WHERE user_id = ?
            """, (language, user_id,))

            await db.commit()

    except Exception as e:
        print(f"error: database: db_create_user(): {e}")

async def db_read(arr, sql_from: str, sql_where: str = "user_id", sql_select: str = "*", user_is_in_db: bool = False) -> list | bool | None:
    '''
    `SELECT {sql_select} FROM {sql_from} WHERE {sql_where} = ?(arr)`
    
    :param arr: Required value of the `sql_where` parameter
    :type arr: Any
    :param sql_from: In which table the operation needs to be performed
    :type sql_from: str
    :param sql_where: Which parameter needs to be read. By default, `user_id` *(because `PRIMARY KEY`)*
    :type sql_where: str
    :param sql_select: What parameters should be returned? By default, `*` *(will return everything)*
    :type sql_select: str
    :param user_is_in_db: If `True`, it will return the fact that a **user or chat** is in the table *(`True` if he is there. Otherwise `False`)*
    :type user_is_in_db: bool
    '''
    try:
        async with connect(DB_DB) as db:
            if not user_is_in_db:
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
        print(f"error: database: db_read(): {e}")
        return None

async def db_update(arr_set, arr_where, sql_update: str, sql_set: str, sql_where: str = "user_id") -> None:
    '''
    `UPDATE {sql_update} SET {sql_set} = ?(arr_set) WHERE {sql_where} = ?(arr_where)`
    
    :param arr_set: Required value of the `sql_set` parameter
    :type arr_set: Any
    :param arr_where: Required value of the `sql_where` parameter
    :type arr_where: Any
    :param sql_update: In which table the operation needs to be performed
    :type sql_update: str
    :param sql_set: Which parameter needs to be updated
    :type sql_set: str
    :param sql_where: update all those with `sql_where` equal to `arr_where`. By default, `id` *(because `PRIMARY KEY`)*
    :type sql_where: str
    '''
    try:
        async with connect(DB_DB) as db:
            await db.execute(f"UPDATE {sql_update} SET {sql_set} = ? WHERE {sql_where} = ?", (arr_set, arr_where))
            await db.commit()

    except Exception as e:
        print(f"error: database: db_update(): {e}")

async def db_delete_user(user_id: int) -> None:
    async with connect(DB_DB) as db:
        await db.execute("DELETE FROM general WHERE user_id = ?", (user_id,))
        await db.commit()


async def db_get_all_users() -> list:
    try:
        async with connect(DB_DB) as db:
            async with db.execute("SELECT user_id FROM general",) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    except Exception as e:
        print(f"error: database: db_get_all_users(): {e}")
        return []

async def db_get_language(user_id: int) -> str:
    user_data = await db_read(
        arr=user_id,
        sql_from="settings",
        return_boolean=True
    )
    if user_data:
        try:
            async with connect(DB_DB) as db:
                async with db.execute("SELECT language FROM settings WHERE user_id = ?", (user_id,)) as cursor:
                    raw_data = await cursor.fetchone()
                    l_code = raw_data[0]
                    return l_code

        except Exception as e:
            print(f"error: database: db_get_language(): {e}")
            return None

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

async def db_rmstat(user_id: int):
    try:
        async with connect(DB_DB) as db:
            await db.execute("""
                UPDATE general 
                SET completed = 0, completed_ishraq = 0, completed_jumuah = 0, missed = 0, missed_jumuah = 0
                WHERE user_id = ?
            """, (user_id,))
            await db.execute("INSERT OR IGNORE INTO salah (user_id) VALUES (?)", (user_id,))
            await db.commit()

    except Exception as e:
        print(f"error: database: db_rmstat(): {e}")