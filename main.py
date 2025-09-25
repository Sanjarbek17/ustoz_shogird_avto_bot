from bot.my_bot import main

import telegram
from tinydb import Query, TinyDB

from core.getting_data import to_text
from telegram import Bot, Update
from telegram.ext import Application
from dotenv import load_dotenv
import os
import asyncio

userdb = TinyDB('data_json/user.json', indent=4, separators=(',', ': '))
datadb = TinyDB('data_json/data.json', indent=4, separators=(',', ': '), encoding='utf-8')

Data = Query()
data = datadb.table('data')
User = Query()
user_table = userdb.table('user')

load_dotenv()
token = os.getenv('BOT_TOKEN')

bot = Bot(token=token)

async def send_data() -> None:
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
                await bot.send_message(chat_id=user['id'], text=text)
                await asyncio.sleep(5)  # Add a delay of 1 second between messages
            except telegram.error.RetryAfter as e:
                await asyncio.sleep(e.retry_after)
                continue
            except Exception as e:
                continue


async def send_new_message(message_data: dict) -> None:
    """Send a new message to users who have matching hashtags."""
    if not message_data or 'hashtags' not in message_data:
        return
    
    message_hashtags = message_data['hashtags']
    if not message_hashtags:
        return
    
    # Get all users
    users = user_table.all()
    
    for user in users:
        user_hashtags = user.get('hashtags', [])
        if not user_hashtags:
            continue
            
        # Check if user has any hashtag that matches the message hashtags
        has_matching_hashtag = any(hashtag in message_hashtags for hashtag in user_hashtags)
        
        if has_matching_hashtag:
            try:
                text = to_text(message_data)
                await bot.send_message(chat_id=user['id'], text=text)
                await asyncio.sleep(1)  # Add a delay between messages
                print(f"Sent new message to user {user['id']}")
            except telegram.error.RetryAfter as e:
                await asyncio.sleep(e.retry_after)
                # Retry sending
                try:
                    await bot.send_message(chat_id=user['id'], text=text)
                    print(f"Retry successful: Sent message to user {user['id']}")
                except Exception as retry_e:
                    print(f"Failed to send message to user {user['id']} after retry: {retry_e}")
            except Exception as e:
                print(f"Failed to send message to user {user['id']}: {e}")
                continue

async def run_bot_async() -> None:
    """Run the bot asynchronously."""
    from telegram.ext import Application
    from bot.my_bot import handler

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(token).build()

    application = handler(application)

    # Start polling asynchronously
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    # Keep the application running
    try:
        # Wait indefinitely
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        await application.updater.stop()
        await application.stop()


async def run_both() -> None:
    """Run both the bot and the listener concurrently."""
    from bot.scraping import start_listening

    # Create tasks for both async functions
    bot_task = asyncio.create_task(run_bot_async())
    listener_task = asyncio.create_task(start_listening())

    # Run both tasks concurrently
    await asyncio.gather(bot_task, listener_task)

if __name__ == '__main__':
    if 'send_data' in os.sys.argv:
        asyncio.run(send_data())
    elif 'hashtags' in os.sys.argv:
        from bot.scraping import run_hashtags
        run_hashtags()
    elif 'get_data' in os.sys.argv:
        from bot.scraping import run_main
        run_main()
    elif 'listen' in os.sys.argv:
        # Run the listener mode for real-time message forwarding
        from bot.scraping import run_listener
        run_listener()
    else:
        # Run both bot and listener concurrently
        asyncio.run(run_both())