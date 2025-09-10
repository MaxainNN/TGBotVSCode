import logging
import json
from aiogram import Bot, Dispatcher, types

import app.config as cfg
import app.db as ensure_tables_created
from app.handlers import router

logging.basicConfig(level=logging.INFO)

bot = Bot(token=cfg.API_TOKEN)
dp = Dispatcher()

async def process_event(event):
    update = types.Update.model_validate(json.loads(event['body']), context={"bot": bot})
    await dp.feed_update(bot, update)

async def webhook(event, context):
    await ensure_tables_created()
    if event['httpMethod'] == 'POST':
        await process_event(event)
        return {'statusCode': 200, 'body': 'ok'}
    return {'statusCode': 405}   