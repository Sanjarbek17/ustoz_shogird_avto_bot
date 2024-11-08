import os
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, ContextTypes
from telegram.error import NetworkError

from bot.my_bot import handler

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
    update_json = {"update_id": 7433649,
        "message": {
            "message_id": 473,
            "from": {
                "id": 7662812087,
                "is_bot": False,
                "first_name": "Saidov Sanjarbek",
                "username": "Sanjarbek177",
                "language_code": "en"
            },
            "chat": {
                "id": 7662812087,
                "first_name": "Saidov Sanjarbek",
                "username": "Sanjarbek177",
                "type": "private"
            },
            "date": 1731010949,
            "text": "/start",
            "entities": [
                {
                    "offset": 0,
                    "length": 6,
                    "type": "bot_command"
                }
            ]
        }
    }
    
    process_single_update(update_json)
