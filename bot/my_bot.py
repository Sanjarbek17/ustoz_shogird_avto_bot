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
import asyncio
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
            KeyboardButton("🔍 Search Messages"),
            KeyboardButton("📋 My Hashtags"),
        ],
        [
            KeyboardButton("➕ Add Hashtags"),
            KeyboardButton("➖ Remove Hashtags"),
        ],
        [
            KeyboardButton("⚙️ Search Settings"),
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


async def remove_hashtag_keyboards(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Sends inline keyboard to remove hashtags."""
    user = update.effective_user
    user_hashtags = user_table.get(User.id == user.id)["hashtags"]

    if len(user_hashtags) == 0:
        await update.message.reply_text("You have no hashtags to remove.")
        return

    # Create keyboard with all user hashtags for removal
    keyboard = [
        [InlineKeyboardButton(f"❌ {hashtag}", callback_data=f"remove{hashtag}")]
        for hashtag in user_hashtags
    ]

    # Add "Remove All" option
    keyboard.append(
        [InlineKeyboardButton("🗑️ Remove All Hashtags", callback_data="remove_all")]
    )

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"""🗑️ *Remove Hashtags*

Your current hashtags: {' '.join(user_hashtags)}

Tap a hashtag to remove it, or remove all at once:""",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def remove_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle hashtag removal from callback."""
    user = update.effective_user
    query = update.callback_query

    await query.answer()

    user_data = user_table.get(User.id == user.id)
    user_hashtags = set(user_data.get("hashtags", []))

    if query.data == "remove_all":
        # Remove all hashtags
        user_table.update({"hashtags": []}, User.id == user.id)
        await query.edit_message_text("✅ All hashtags have been removed!")
        return

    # Extract hashtag from callback data "remove#hashtag"
    hashtag = query.data[6:]  # Remove "remove" prefix

    if hashtag in user_hashtags:
        user_hashtags.remove(hashtag)
        user_hashtags = list(user_hashtags)
        user_table.update({"hashtags": user_hashtags}, User.id == user.id)

        if len(user_hashtags) == 0:
            await query.edit_message_text(
                f"✅ Removed {hashtag}\n\nYou have no more hashtags."
            )
        else:
            # Recreate keyboard with remaining hashtags
            keyboard = [
                [InlineKeyboardButton(f"❌ {tag}", callback_data=f"remove{tag}")]
                for tag in user_hashtags
            ]
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "🗑️ Remove All Hashtags", callback_data="remove_all"
                    )
                ]
            )

            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                f"""🗑️ *Remove Hashtags*

✅ Removed {hashtag}

Remaining hashtags: {' '.join(user_hashtags)}

Tap a hashtag to remove it, or remove all at once:""",
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )
    else:
        await query.answer("Hashtag not found!", show_alert=True)


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show search options to user."""
    user = update.effective_user
    user_data = user_table.get(User.id == user.id)
    user_hashtags = user_data["hashtags"]

    if len(user_hashtags) == 0:
        await update.message.reply_text(
            "You have no hashtags. Please add hashtags first"
        )
        return

    # Create keyboard with search limit options
    keyboard = [
        [InlineKeyboardButton("10 messages", callback_data="search_10")],
        [InlineKeyboardButton("25 messages", callback_data="search_25")],
        [InlineKeyboardButton("50 messages", callback_data="search_50")],
        [InlineKeyboardButton("100 messages", callback_data="search_100")],
        [InlineKeyboardButton("All messages", callback_data="search_all")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    match_mode = user_data.get("match_mode", "any")
    await update.message.reply_text(
        f"""🔍 *Search Messages*

*Current mode:* {match_mode.upper()}
*Your hashtags:* {' '.join(user_hashtags)}

How many recent messages do you want to search?""",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def perform_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Perform the actual search with selected limit."""
    query = update.callback_query
    user = update.effective_user

    await query.answer()

    # Extract limit from callback data "search_10", "search_all", etc.
    limit_str = query.data.split("_")[1]
    limit = None if limit_str == "all" else int(limit_str)

    user_data = user_table.get(User.id == user.id)
    user_hashtags = user_data["hashtags"]
    match_mode = user_data.get("match_mode", "any")

    # Get data according to hashtags and match mode
    if match_mode == "advanced":
        # Advanced mode: (ALL required) AND (ANY optional)
        required_tags = user_data.get("required_hashtags", [])
        optional_tags = user_data.get("optional_hashtags", [])

        # Get all data first
        all_data = data.all()
        search = []

        for item in all_data:
            item_hashtags = item.get("hashtags", [])

            # Check required hashtags (all must be present)
            required_match = (
                all(tag in item_hashtags for tag in required_tags)
                if required_tags
                else True
            )

            # Check optional hashtags (at least one must be present)
            optional_match = (
                any(tag in item_hashtags for tag in optional_tags)
                if optional_tags
                else True
            )

            # Both conditions must be met
            if required_match and optional_match:
                search.append(item)
    elif match_mode == "all":
        search = data.search(Data.hashtags.all(user_hashtags))
    else:
        search = data.search(Data.hashtags.any(user_hashtags))

    # Sort by most recent (assuming there's a timestamp or ID field)
    # If your data has a timestamp, sort by it. Otherwise, reverse to get most recent
    search = list(reversed(search))

    # Apply limit
    if limit:
        search = search[:limit]

    if len(search) == 0:
        await query.edit_message_text(
            f"❌ No data found with match mode: {match_mode.upper()}"
        )
        return

    # Store search context for stop functionality
    context.user_data["searching"] = True
    context.user_data["search_total"] = len(search)
    context.user_data["search_sent"] = 0

    # Create stop button
    stop_keyboard = [
        [InlineKeyboardButton("🛑 Stop Search", callback_data="stop_search")]
    ]
    stop_markup = InlineKeyboardMarkup(stop_keyboard)

    status_message = await query.edit_message_text(
        f"🔍 Searching with mode: {match_mode.upper()}\nFound {len(search)} results\nSending messages...",
        reply_markup=stop_markup,
    )

    context.user_data["status_message_id"] = status_message.message_id
    context.user_data["status_chat_id"] = query.message.chat_id

    sent_count = 0
    for dct in search:
        # Check if user stopped the search
        if not context.user_data.get("searching", False):
            break

        from core.getting_data import (
            clean_markdown_for_telegram,
            remove_all_markdown,
        )

        text = to_text(dct)
        cleaned_text = clean_markdown_for_telegram(str(text))

        try:
            try:
                await context.bot.send_message(
                    user.id,
                    text=cleaned_text,
                    parse_mode="Markdown",
                )
            except Exception as parse_error:
                # If markdown parsing fails, send as plain text
                plain_text = remove_all_markdown(str(text))
                await context.bot.send_message(user.id, text=plain_text)
                logger.info(
                    f"Sent plain text message to user {user.id} due to markdown error"
                )

            sent_count += 1
            context.user_data["search_sent"] = sent_count

            # Update status every 5 messages
            if sent_count % 5 == 0:
                try:
                    await context.bot.edit_message_text(
                        chat_id=context.user_data["status_chat_id"],
                        message_id=context.user_data["status_message_id"],
                        text=f"🔍 Searching with mode: {match_mode.upper()}\nSent {sent_count}/{len(search)} messages...",
                        reply_markup=stop_markup,
                    )
                except Exception:
                    pass  # Ignore if message is too old to edit

            # Small delay to avoid flooding
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"error {e}")

    # Final status update
    context.user_data["searching"] = False
    try:
        if sent_count == len(search):
            await context.bot.edit_message_text(
                chat_id=context.user_data["status_chat_id"],
                message_id=context.user_data["status_message_id"],
                text=f"✅ Search completed!\nSent {sent_count}/{len(search)} messages",
            )
        else:
            await context.bot.edit_message_text(
                chat_id=context.user_data["status_chat_id"],
                message_id=context.user_data["status_message_id"],
                text=f"🛑 Search stopped by user\nSent {sent_count}/{len(search)} messages",
            )
    except Exception:
        pass


async def stop_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stop the ongoing search."""
    query = update.callback_query
    await query.answer("Stopping search...", show_alert=True)

    context.user_data["searching"] = False

    sent = context.user_data.get("search_sent", 0)
    total = context.user_data.get("search_total", 0)

    try:
        await query.edit_message_text(
            f"🛑 Search stopped!\nSent {sent}/{total} messages"
        )
    except Exception:
        pass


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


async def search_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show search settings to user."""
    user = update.effective_user
    user_data = user_table.get(User.id == user.id)
    current_mode = user_data.get("match_mode", "any")

    keyboard = [
        [
            InlineKeyboardButton(
                f"{'✅ ' if current_mode == 'any' else ''}Match ANY hashtag",
                callback_data="mode_any",
            )
        ],
        [
            InlineKeyboardButton(
                f"{'✅ ' if current_mode == 'all' else ''}Match ALL hashtags",
                callback_data="mode_all",
            )
        ],
        [
            InlineKeyboardButton(
                f"{'✅ ' if current_mode == 'advanced' else ''}Advanced (AND/OR groups)",
                callback_data="mode_advanced",
            )
        ],
        [
            InlineKeyboardButton(
                "⚙️ Configure Hashtag Groups",
                callback_data="config_groups",
            )
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Get hashtag groups info
    required_tags = user_data.get("required_hashtags", [])
    optional_tags = user_data.get("optional_hashtags", [])

    advanced_info = ""
    if current_mode == "advanced":
        advanced_info = f"\n\n*Required (AND):* {' '.join(required_tags) if required_tags else 'None'}\n*Optional (OR):* {' '.join(optional_tags) if optional_tags else 'None'}"

    await update.message.reply_text(
        f"""🔍 *Search Settings*

*Current mode:* {current_mode.upper()}

*Match ANY hashtag:* You'll receive messages that contain at least ONE of your hashtags.
Example: If you have #python and #django, you'll get messages with #python OR #django

*Match ALL hashtags:* You'll receive messages that contain ALL of your hashtags.
Example: If you have #python and #django, you'll ONLY get messages with BOTH #python AND #django

*Advanced (AND/OR groups):* You can set REQUIRED hashtags (must all match) and OPTIONAL hashtags (any can match).
Example: Required: #python #django, Optional: #backend
→ Messages MUST have #python AND #django, AND at least one of (#backend){advanced_info}

Choose your preference:""",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def configure_groups(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show interface to configure required and optional hashtag groups."""
    user = update.effective_user
    query = update.callback_query

    await query.answer()

    user_data = user_table.get(User.id == user.id)
    all_hashtags = user_data.get("hashtags", [])
    required_tags = user_data.get("required_hashtags", [])
    optional_tags = user_data.get("optional_hashtags", [])

    # Create keyboard with all user's hashtags
    keyboard = []
    for hashtag in all_hashtags:
        if hashtag in required_tags:
            label = f"🔴 {hashtag} (Required)"
            callback = f"toggle_req_{hashtag}"
        elif hashtag in optional_tags:
            label = f"🟡 {hashtag} (Optional)"
            callback = f"toggle_opt_{hashtag}"
        else:
            label = f"⚪️ {hashtag} (Not set)"
            callback = f"toggle_none_{hashtag}"
        keyboard.append([InlineKeyboardButton(label, callback_data=callback)])

    keyboard.append([InlineKeyboardButton("✅ Done", callback_data="done_groups")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"""⚙️ *Configure Hashtag Groups*

Tap each hashtag to cycle through:
⚪️ Not set → 🔴 Required (AND) → 🟡 Optional (OR)

*Required (AND):* {' '.join(required_tags) if required_tags else 'None'}
*Optional (OR):* {' '.join(optional_tags) if optional_tags else 'None'}

Logic: (All Required) AND (Any Optional)""",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def toggle_hashtag_group(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Toggle hashtag between required, optional, and not set."""
    user = update.effective_user
    query = update.callback_query

    await query.answer()

    # Parse callback data: "toggle_<current_state>_<hashtag>"
    parts = query.data.split("_", 2)
    current_state = parts[1]  # "req", "opt", or "none"
    hashtag = parts[2]

    user_data = user_table.get(User.id == user.id)
    required_tags = set(user_data.get("required_hashtags", []))
    optional_tags = set(user_data.get("optional_hashtags", []))

    # Cycle through states: none -> req -> opt -> none
    if current_state == "none":
        required_tags.add(hashtag)
        optional_tags.discard(hashtag)
    elif current_state == "req":
        required_tags.discard(hashtag)
        optional_tags.add(hashtag)
    elif current_state == "opt":
        required_tags.discard(hashtag)
        optional_tags.discard(hashtag)

    # Update database
    user_table.update(
        {
            "required_hashtags": list(required_tags),
            "optional_hashtags": list(optional_tags),
        },
        User.id == user.id,
    )

    # Refresh the interface
    user_data = user_table.get(User.id == user.id)
    all_hashtags = user_data.get("hashtags", [])

    # Create keyboard with updated states
    keyboard = []
    for tag in all_hashtags:
        if tag in required_tags:
            label = f"🔴 {tag} (Required)"
            callback = f"toggle_req_{tag}"
        elif tag in optional_tags:
            label = f"🟡 {tag} (Optional)"
            callback = f"toggle_opt_{tag}"
        else:
            label = f"⚪️ {tag} (Not set)"
            callback = f"toggle_none_{tag}"
        keyboard.append([InlineKeyboardButton(label, callback_data=callback)])

    keyboard.append([InlineKeyboardButton("✅ Done", callback_data="done_groups")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"""⚙️ *Configure Hashtag Groups*

Tap each hashtag to cycle through:
⚪️ Not set → 🔴 Required (AND) → 🟡 Optional (OR)

*Required (AND):* {' '.join(required_tags) if required_tags else 'None'}
*Optional (OR):* {' '.join(optional_tags) if optional_tags else 'None'}

Logic: (All Required) AND (Any Optional)""",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def search_settings_button(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle search settings button callback."""
    user = update.effective_user
    query = update.callback_query

    await query.answer()

    if query.data == "config_groups":
        await configure_groups(update, context)
        return

    if query.data == "done_groups":
        # Return to search settings
        await search_settings(update, context)
        return

    # Extract mode from callback data
    mode = query.data.split("_")[1]  # "mode_any", "mode_all", or "mode_advanced"

    # Update user's match mode
    user_table.update({"match_mode": mode}, User.id == user.id)

    user_data = user_table.get(User.id == user.id)
    required_tags = user_data.get("required_hashtags", [])
    optional_tags = user_data.get("optional_hashtags", [])

    advanced_info = ""
    if mode == "advanced":
        advanced_info = f"\n\n*Required (AND):* {' '.join(required_tags) if required_tags else 'None'}\n*Optional (OR):* {' '.join(optional_tags) if optional_tags else 'None'}"

    keyboard = [
        [
            InlineKeyboardButton(
                f"{'✅ ' if mode == 'any' else ''}Match ANY hashtag",
                callback_data="mode_any",
            )
        ],
        [
            InlineKeyboardButton(
                f"{'✅ ' if mode == 'all' else ''}Match ALL hashtags",
                callback_data="mode_all",
            )
        ],
        [
            InlineKeyboardButton(
                f"{'✅ ' if mode == 'advanced' else ''}Advanced (AND/OR groups)",
                callback_data="mode_advanced",
            )
        ],
        [
            InlineKeyboardButton(
                "⚙️ Configure Hashtag Groups",
                callback_data="config_groups",
            )
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"""🔍 *Search Settings*

*Current mode:* {mode.upper()}

*Match ANY hashtag:* You'll receive messages that contain at least ONE of your hashtags.
Example: If you have #python and #django, you'll get messages with #python OR #django

*Match ALL hashtags:* You'll receive messages that contain ALL of your hashtags.
Example: If you have #python and #django, you'll ONLY get messages with BOTH #python AND #django

*Advanced (AND/OR groups):* You can set REQUIRED hashtags (must all match) and OPTIONAL hashtags (any can match).
Example: Required: #python #django, Optional: #backend
→ Messages MUST have #python AND #django, AND at least one of (#backend){advanced_info}

✅ Settings updated!

*Match ALL hashtags:* You'll receive messages that contain ALL of your hashtags.
Example: If you have #python and #django, you'll ONLY get messages with BOTH #python AND #django

✅ Settings updated!""",
        reply_markup=reply_markup,
        parse_mode="Markdown",
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
            from core.getting_data import (
                clean_markdown_for_telegram,
                remove_all_markdown,
            )

            text = to_text(dct)
            cleaned_text = clean_markdown_for_telegram(str(text))
            try:
                try:
                    await context.bot.send_message(
                        user["id"],
                        text=cleaned_text,
                        parse_mode="Markdown",
                    )
                except Exception as parse_error:
                    # If markdown parsing fails, send as plain text
                    plain_text = remove_all_markdown(str(text))
                    await context.bot.send_message(user["id"], text=plain_text)
                    logger.info(
                        f"Sent plain text message to user {user['id']} due to markdown error"
                    )
            except Exception as e:
                logger.error(f"error {e}")


def handler(application):
    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("send", send_data))
    application.add_handler(
        CallbackQueryHandler(search_settings_button, pattern=r"^mode_")
    )
    application.add_handler(
        CallbackQueryHandler(search_settings_button, pattern=r"^config_groups$")
    )
    application.add_handler(
        CallbackQueryHandler(search_settings_button, pattern=r"^done_groups$")
    )
    application.add_handler(
        CallbackQueryHandler(toggle_hashtag_group, pattern=r"^toggle_")
    )
    application.add_handler(CallbackQueryHandler(perform_search, pattern=r"^search_"))
    application.add_handler(CallbackQueryHandler(stop_search, pattern=r"^stop_search$"))
    application.add_handler(CallbackQueryHandler(remove_button, pattern=r"^remove"))
    application.add_handler(CallbackQueryHandler(my_button, pattern=r"^my"))
    application.add_handler(CallbackQueryHandler(button, pattern=r"^#"))
    application.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(
        MessageHandler(filters.Text("➕ Add Hashtags"), hashtag_keyboards)
    )
    application.add_handler(
        MessageHandler(filters.Text("➖ Remove Hashtags"), remove_hashtag_keyboards)
    )
    application.add_handler(
        MessageHandler(filters.Text("📋 My Hashtags"), my_hashtag_keyboards)
    )
    application.add_handler(MessageHandler(filters.Text("🔍 Search Messages"), search))
    application.add_handler(
        MessageHandler(filters.Text("⚙️ Search Settings"), search_settings)
    )
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
