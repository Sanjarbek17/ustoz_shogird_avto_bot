import time
from bot.my_bot import main

import telegram
from tinydb import Query, TinyDB

from core.getting_data import to_text
from telegram import Bot
from dotenv import load_dotenv
import os

userdb = TinyDB('data_json/user.json', indent=4, separators=(',', ': '))
datadb = TinyDB('data_json/data.json', indent=4, separators=(',', ': '), encoding='utf-8')

Data = Query()
data = datadb.table('data')
User = Query()
user_table = userdb.table('user')

load_dotenv()
token = os.getenv('TOKEN')

bot = Bot(token=token)

def send_data() -> None:
    """Send a message according to all users hashtags."""
    # get users ids and hashtags
    users = user_table.all()
    for user in users:
        user_hashtags = user['hashtags']
        search = data.search(Data.hashtags.all(user_hashtags))
        if len(search) == 0:
            continue
        for dct in search:
            text = to_text(dct)
            try:
                bot.send_message(chat_id=user['id'], text=text)
                time.sleep(5)  # Add a delay of 1 second between messages
            except telegram.error.RetryAfter as e:
                time.sleep(e.retry_after)
                continue
            except Exception as e:
                continue

if __name__ == '__main__':
    if 'send_data' in os.sys.argv:
        send_data()
    elif 'hashtags' in os.sys.argv:
        from bot.scraping import run_hashtags
        run_hashtags()
    elif 'get_data' in os.sys.argv:
        from bot.scraping import run_main
        run_main()
    else:
        main()