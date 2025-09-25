"""
Simple Bot to reply to Telegram messages.

First, a few handler functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

from pprint import pprint

import os
from dotenv import load_dotenv
from tinydb import TinyDB, Query

from core.getting_data import to_text

userdb = TinyDB("data_json/user.json", indent=4, separators=(",", ": "))
datadb = TinyDB(
    "data_json/data.json", indent=4, separators=(",", ": "), encoding="utf-8"
)
hashdb = TinyDB(
    "data_json/hashtag.json", sort_keys=True, indent=4, separators=(",", ": ")
)

Data = Query()
data = datadb.table("data")
User = Query()
user_table = userdb.table("user")

Hashtag = Query()
hash_table = hashdb.table("hashtag")

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

import logging

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user

    # save user data
    user_data = {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "hashtags": [],
    }
    # check if user exists
    if not user_table.get(User.id == user.id):
        user_table.insert(user_data)

    keyboard = [
        [
            KeyboardButton("Search"),
            KeyboardButton("My Hashtags"),
        ],
        [
            KeyboardButton("Add Hashtags"),
        ],
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard)

    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=reply_markup,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")


async def hashtag_keyboards(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends inline keyboard contains hashtags."""
    search = hash_table.search(Hashtag.hashtag.exists())
    search.sort(key=lambda x: x["count"], reverse=True)
    # most 10 used hashtags
    most_hashtags = search[:10]

    keyboard = [
        [InlineKeyboardButton(hashtag["hashtag"], callback_data=hashtag["hashtag"])]
        for hashtag in most_hashtags
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # get hashtags
    user = update.effective_user
    user_hashtags = user_table.get(User.id == user.id)["hashtags"]

    await update.message.reply_text(
        f"""Currently hashtags: {" ".join(user_hashtags)}
You can choose one of these by tapping, or delete if it exists.
You can also add your own hashtag by typing: #yourOwnHashtag,""",
        reply_markup=reply_markup,
    )


async def my_hashtag_keyboards(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Sends inline keyboard contains hashtags."""
    # get user hashtags
    user = update.effective_user
    user_hashtags = user_table.get(User.id == user.id)["hashtags"]

    keyboard = [
        [InlineKeyboardButton(hashtag, callback_data="my" + hashtag)]
        for hashtag in user_hashtags
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # get hashtags
    user = update.effective_user
    user_hashtags = user_table.get(User.id == user.id)["hashtags"]

    if len(user_hashtags) == 0:
        await update.message.reply_text(
            f"Currently hashtags None", reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            f"Currently hashtags {' '.join(user_hashtags)}", reply_markup=reply_markup
        )


async def add_hashtag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add hashtag to user hashtags."""
    text = update.message.text

    # check text has valid hashtag
    if not text.startswith("#"):
        await update.message.reply_text("Please enter a valid hashtag")
        return

    # if multiple hashtags
    user = update.effective_user
    user_hashtags = set(user_table.get(User.id == user.id)["hashtags"])

    if " " in text:
        hashtags = text.split()
        for hashtag in hashtags:
            if hashtag.startswith("#"):
                user_hashtags.add(hashtag)
            else:
                continue

    user_hashtags.add(update.message.text)
    # convert set to list
    user_hashtags = list(user_hashtags)
    user_table.update({"hashtags": user_hashtags}, User.id == user.id)
    await update.message.reply_text(f"Hashtag {update.message.text} added")


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the text search is issued."""
    # get user hashtags
    user = update.effective_user
    user_hashtags = user_table.get(User.id == user.id)["hashtags"]
    # logger.info(user_hashtags)
    if len(user_hashtags) == 0:
        await update.message.reply_text("You have no hashtags. Please add hashtags first")
        return
    # get data according to hashtags
    search = data.search(Data.hashtags.all(user_hashtags))
    # logger.info(search)
    if len(search) == 0:
        await update.message.reply_text("No data found")
        return

    for dct in search:

        text = to_text(dct)
        try:
            await update.message.reply_text(text)
        except Exception as e:
            logger.error(f"error {e}")


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    user = update.effective_user
    query = update.callback_query

    search = hash_table.search(Hashtag.hashtag.exists())
    search.sort(key=lambda x: x["count"], reverse=True)
    # most 10 used hashtags
    most_hashtags = search[:10]

    keyboard = [
        [InlineKeyboardButton(hashtag["hashtag"], callback_data=hashtag["hashtag"])]
        for hashtag in most_hashtags
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()
    logger.info(query.data)
    user_hashtags = set(user_table.get(User.id == user.id)["hashtags"])

    if query.data != "done":
        if query.data in user_hashtags:
            user_hashtags.remove(query.data)
        else:
            user_hashtags.add(query.data)

        user_hashtags = list(user_hashtags)
        user_table.update({"hashtags": user_hashtags}, User.id == user.id)
        await query.edit_message_text(
            text=f"Selected option: {' '.join(user_hashtags)}",
            reply_markup=reply_markup,
        )

    # await query.edit_message_text(text=f"Selected option: {query.data}")


async def my_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    user = update.effective_user
    query = update.callback_query

    # get user hashtags
    user_hashtags = user_table.get(User.id == user.id)["hashtags"]

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()
    logger.info(query.data)
    data = query.data[2:]
    user_hashtags = set(user_table.get(User.id == user.id)["hashtags"])

    if data in user_hashtags:
        user_hashtags.remove(data)
    else:
        user_hashtags.add(data)

    user_hashtags = list(user_hashtags)

    keyboard = [
        [InlineKeyboardButton(hashtag, callback_data="my" + hashtag)]
        for hashtag in user_hashtags
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    user_table.update({"hashtags": user_hashtags}, User.id == user.id)

    if len(user_hashtags) == 0:
        await query.edit_message_text(
            text=f"Selected option: None", reply_markup=reply_markup
        )
    else:
        await query.edit_message_text(
            text=f"Selected option: {' '.join(user_hashtags)}",
            reply_markup=reply_markup,
        )


async def send_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message according to all users hashtags."""

    # get users ids and hashtags
    users = user_table.all()

    for user in users:
        user_hashtags = user["hashtags"]
        search = data.search(Data.hashtags.all(user_hashtags))
        if len(search) == 0:
            continue
        for dct in search:
            text = to_text(dct)
            try:
                await context.bot.send_message(user["id"], text)
            except Exception as e:
                logger.error(f"error {e}")


def handler(application):
    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("send", send_data))
    application.add_handler(CallbackQueryHandler(my_button, pattern=r"^my"))
    application.add_handler(CallbackQueryHandler(button, pattern=r"^#"))
    application.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(
        MessageHandler(filters.Text("Add Hashtags"), hashtag_keyboards)
    )
    application.add_handler(
        MessageHandler(filters.Text("My Hashtags"), my_hashtag_keyboards)
    )
    application.add_handler(MessageHandler(filters.Text("Search"), search))
    application.add_handler(MessageHandler(filters.Regex(r"^#"), add_hashtag))

    return application


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    application = handler(application)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
