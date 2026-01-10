from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

from os import getenv
from dotenv import load_dotenv; load_dotenv()



TOKEN=getenv('BOT_TOKEN')
BOT = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode='HTML')
)
DEVELOPER_ID=getenv('DEVELOPER_ID')

DB_DB=getenv('DB_DB')
DB_SQL=getenv('DB_SQL')