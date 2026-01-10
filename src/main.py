from aiogram import Dispatcher
from aiogram.exceptions import TelegramBadRequest

from asyncio import run

from config import BOT, DEVELOPER_ID
from database import db_create_database
from app.handlers import RT as router_handlers
from app.callbacks import RT as router_callbacks
from app.scheduler import start_scheduler, update_daily_timings


DP = Dispatcher()



async def main() -> None:
    print("(2/5) main() function received")
    await db_create_database()
    await update_daily_timings()
    start_scheduler()
    print("(3/5) Database is got checked and scheduler is started")
    DP.include_router(router_handlers)
    DP.include_router(router_callbacks)
    print("(4/5) Routers are connected")
    if DEVELOPER_ID != None:
        await BOT.send_message(
            chat_id=DEVELOPER_ID,
            text="Connection to Telegram has been successfully established."
        )
    print("(5/5) Done")
    await BOT.delete_webhook(drop_pending_updates=True)
    await DP.start_polling(BOT)


if __name__ == "__main__":
    try:
        print("(1/5) Starting a bot")
        run(main())

    except KeyboardInterrupt:
        print("Stopped (KeyboardInterrupt)")
    except TelegramBadRequest as e:
        print(f"error — TelegramBadRequest: main.py: {e}")
    except Exception as e:
        print(f"error: main.py: {e}")