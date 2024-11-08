import os
from telegram import Update
from telegram.ext import Updater
from telegram.error import NetworkError

from bot.my_bot import handler
import json

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("Bot token not found. Please set the TOKEN environment variable.")

def set_webhook(url):
    updater = Updater(TOKEN)
    return updater.bot.set_webhook(url=url)

def process_single_update(update_json):
    try:
        updater = Updater(TOKEN)
        
        application = updater.dispatcher
        application = handler(application)
        # bot_app.start_polling()
        update = Update.de_json(update_json, updater.bot)
        application.process_update(update)
        # bot_app.shutdown()  # Cleanly shutdown the bot
    except NetworkError as e:
        print(f"Network error during update processing: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    with open('data_json/dummy.json') as f:
        update_json = f.read()
    update_json = json.loads(update_json)
    process_single_update(update_json)
