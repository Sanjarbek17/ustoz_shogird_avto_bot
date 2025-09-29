from pprint import pprint
from telethon import TelegramClient, events
from tinydb import TinyDB, Query
import datetime
import json
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to import main module
sys.path.append(str(Path(__file__).parent.parent))

from core.getting_data import to_json

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
TOKEN = os.getenv("BOT_TOKEN")

music_bot = "@music_storage1718_bot"
ustoz_shogird = "https://t.me/UstozShogird"
# ustoz_shogird = "@sanjarbek1718"

client: TelegramClient = TelegramClient("anon", API_ID, API_HASH)
bot: TelegramClient = TelegramClient("anon2", API_ID, API_HASH).start(bot_token=TOKEN)

db = TinyDB("data_json/data.json", indent=4, separators=(",", ": "), encoding="utf-8")
hashdb = TinyDB(
    "data_json/hashtag.json", sort_keys=True, indent=4, separators=(",", ": ")
)
statsdb = TinyDB(
    "data_json/statistics.json", sort_keys=True, indent=4, separators=(",", ": ")
)

datadb = db.table("data")
stats_table = statsdb.table("stats")

Hashtag = Query()
hashtag = hashdb.table("hashtag")
Stats = Query()
Stats = Query()


def save_message_stats(message):
    """Save message statistics to database"""
    stats_data = {
        "message_id": message.id,
        "date": message.date.isoformat() if message.date else None,
        "text_length": len(message.text) if message.text else 0,
        "has_media": message.media is not None,
        "views": getattr(message, "views", 0),
        "forwards": getattr(message, "forwards", 0),
        "processed_at": datetime.datetime.now().isoformat(),
    }
    stats_table.insert(stats_data)


def process_message(message):
    """Process a single message and save to database"""
    if not message.text:
        return False

    # Save statistics
    save_message_stats(message)

    # Process message content
    lst = message.text.split("\n\n")
    if len(lst) < 4:
        print(f"Skipping message {message.id}: insufficient parts")
        return False

    try:
        dct = to_json(lst)
        # Add comprehensive message metadata directly
        dct["message_id"] = message.id
        dct["date"] = message.date.isoformat() if message.date else None
        dct["views"] = getattr(message, "views", 0)
        dct["forwards"] = getattr(message, "forwards", 0)
        # Handle MessageReplies object properly
        replies = getattr(message, "replies", None)
        dct["replies"] = replies.replies if replies else None
        dct["edit_date"] = message.edit_date.isoformat() if message.edit_date else None
        dct["media_type"] = type(message.media).__name__ if message.media else None
        dct["text_length"] = len(message.text)
        dct["processed_at"] = datetime.datetime.now().isoformat()
        datadb.insert(dct)
        print(f"Processed message {message.id}")
        return True
    except Exception as e:
        print(f"Error processing message {message.id}: {e}")
        return False


# Add a general message listener for debugging
@client.on(events.NewMessage())
async def debug_all_messages(event):
    """Debug handler to catch ALL messages"""
    chat_info = getattr(
        event.chat, "title", getattr(event.chat, "username", f"ID:{event.chat_id}")
    )
    print(f"📨 [DEBUG] Message from: {chat_info} (ID: {event.chat_id})")

    # Check if this is our target channel
    target_entity = await client.get_entity(ustoz_shogird)
    if event.chat_id == target_entity.id:
        print(f"🎯 TARGET CHANNEL DETECTED! This should trigger specific handler too!")


@client.on(events.NewMessage(chats=ustoz_shogird))
async def new_message_handler(event):
    """Handle new messages from the channel in real-time"""
    print(f"🎯 NEW MESSAGE FROM USTOZ-SHOGIRD!")
    print(f"   Message ID: {event.message.id}")
    print(f"   Date: {event.message.date}")
    print(
        f"   Text preview: {event.message.text[:100] if event.message.text else 'No text'}..."
    )
    print(f"New message received: {event.message.id}")

    # Process message and get the processed data
    message_processed = process_message(event.message)

    if message_processed:
        # Get the processed message data from database
        processed_data = datadb.get(Query().message_id == event.message.id)
        if processed_data:
            # Import and call the send function from main.py
            try:
                import main

                await main.send_new_message(processed_data)
                print(f"Sent new message {event.message.id} to subscribed users")
            except Exception as e:
                print(f"Error sending message to users: {e}")

    # Also update hashtags if the message contains hashtags
    if event.message.text:
        await update_hashtags_from_message(event.message)


async def update_hashtags_from_message(message):
    """Update hashtag statistics from a single message"""
    if not message.text:
        return

    lines = message.text.split("\n")
    for line in lines:
        if line.startswith("#"):
            hashtags = line.split(" ")
            for h in hashtags:
                if len(h) == 0 or h.isspace():
                    continue
                if not hashtag.get(Hashtag.hashtag == h):
                    hashtag.insert({"hashtag": h, "count": 1})
                else:
                    dct = hashtag.get(Hashtag.hashtag == h)
                    hashtag.update({"count": dct["count"] + 1}, Hashtag.hashtag == h)


async def start_listening():
    """Start listening for new messages"""
    print(f"Starting to listen for new messages from {ustoz_shogird}...")
    await client.start()
    await client.run_until_disconnected()


async def scrape_all():
    """
    Scrape all messages from the channel in reverse order, saving progress to allow resuming.
    Progress is tracked by last processed message ID in a file.
    """

    progress_file = "data_json/scrape_progress.json"
    last_id = None
    # Load last processed message id if exists
    if os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            try:
                last_id = json.load(f).get("last_id")
            except Exception:
                last_id = None

    # Only truncate if starting from scratch
    if last_id is None:
        datadb.truncate()

    total = 0
    async for message in client.iter_messages(
        ustoz_shogird, reverse=True, min_id=last_id or 0
    ):
        if not message.text:
            continue
        lst = message.text.split("\n\n")
        if len(lst) < 4:
            print(lst)
            continue
        try:
            dct = to_json(lst)
            # Add comprehensive message metadata directly
            dct["message_id"] = message.id
            dct["date"] = message.date.isoformat() if message.date else None
            dct["views"] = getattr(message, "views", 0)
            dct["forwards"] = getattr(message, "forwards", 0)
            # Handle MessageReplies object properly
            replies = getattr(message, "replies", None)
            dct["replies"] = replies.replies if replies else None
            dct["edit_date"] = (
                message.edit_date.isoformat() if message.edit_date else None
            )
            dct["media_type"] = type(message.media).__name__ if message.media else None
            dct["text_length"] = len(message.text)
            dct["processed_at"] = datetime.datetime.now().isoformat()
            datadb.insert(dct)
            last_id = message.id
            total += 1
            print(f"Scraped message {message.id} from {message.date}")
        except Exception as e:
            print(f"Error processing message {message.id}: {e}")
            continue
        # Save progress every 20 messages
        if total % 20 == 0:
            with open(progress_file, "w") as f:
                json.dump({"last_id": last_id}, f)
    # Save final progress
    if last_id is not None:
        with open(progress_file, "w") as f:
            json.dump({"last_id": last_id}, f)


async def scrape_periodic(interval_days=30):
    """
    Periodically re-scrape all messages to update views/forwards data.
    Default interval is 30 days (monthly).
    """
    import asyncio

    last_scrape_file = "data_json/last_scrape.json"

    while True:
        # Check if it's time for periodic scrape
        should_scrape = False

        if os.path.exists(last_scrape_file):
            with open(last_scrape_file, "r") as f:
                try:
                    last_scrape = json.load(f).get("last_scrape")
                    last_scrape_date = datetime.datetime.fromisoformat(last_scrape)
                    days_since = (datetime.datetime.now() - last_scrape_date).days

                    if days_since >= interval_days:
                        should_scrape = True
                        print(
                            f"⏰ {days_since} days since last scrape. Starting periodic update..."
                        )
                except Exception:
                    should_scrape = True
                    print(
                        "🚀 No valid last scrape found. Starting initial periodic scrape..."
                    )
        else:
            should_scrape = True
            print("🚀 Starting first periodic scrape...")

        if should_scrape:
            print(f"📊 Updating message statistics (views, forwards, etc.)...")
            await scrape_all_for_updates()

            # Save last scrape timestamp
            with open(last_scrape_file, "w") as f:
                json.dump(
                    {
                        "last_scrape": datetime.datetime.now().isoformat(),
                        "interval_days": interval_days,
                    },
                    f,
                )

            print(f"✅ Periodic scrape completed. Next update in {interval_days} days.")

        # Wait for next check (check daily)
        print(
            f"💤 Sleeping for 24 hours. Next check: {datetime.datetime.now() + datetime.timedelta(days=1)}"
        )
        await asyncio.sleep(24 * 60 * 60)  # 24 hours


async def scrape_all_for_updates():
    """
    Re-scrape all messages to update changing data like views and forwards.
    This doesn't add new records, just updates existing ones.
    """
    total = 0
    updated = 0

    async for message in client.iter_messages(ustoz_shogird):
        if not message.text:
            continue

        # Check if message exists in database
        existing = datadb.get(Query().message_id == message.id)
        if existing:
            # Update only the changing fields
            current_views = getattr(message, "views", 0)
            current_forwards = getattr(message, "forwards", 0)

            old_views = existing.get("views", 0)
            old_forwards = existing.get("forwards", 0)

            # Only update if there's a change
            if current_views != old_views or current_forwards != old_forwards:
                datadb.update(
                    {
                        "views": current_views,
                        "forwards": current_forwards,
                        "last_updated": datetime.datetime.now().isoformat(),
                    },
                    Query().message_id == message.id,
                )

                # Also save to stats table for historical tracking
                stats_data = {
                    "message_id": message.id,
                    "date": message.date.isoformat() if message.date else None,
                    "text_length": len(message.text) if message.text else 0,
                    "has_media": message.media is not None,
                    "views": current_views,
                    "forwards": current_forwards,
                    "processed_at": datetime.datetime.now().isoformat(),
                    "update_type": "periodic",
                }
                stats_table.insert(stats_data)

                updated += 1
                print(
                    f"📈 Updated message {message.id}: views {old_views}→{current_views}, forwards {old_forwards}→{current_forwards}"
                )

        total += 1
        if total % 100 == 0:
            print(f"🔄 Checked {total} messages, updated {updated} so far...")

    print(f"✅ Completed update: {updated}/{total} messages had changes")


async def scrape_periodic(interval_days=30):
    """
    Periodically re-scrape all messages to update views/forwards data.
    Default interval is 30 days (monthly).
    """
    import asyncio

    last_scrape_file = "data_json/last_scrape.json"

    while True:
        # Check if it's time for periodic scrape
        should_scrape = False

        if os.path.exists(last_scrape_file):
            with open(last_scrape_file, "r") as f:
                try:
                    last_scrape = json.load(f).get("last_scrape")
                    last_scrape_date = datetime.datetime.fromisoformat(last_scrape)
                    days_since = (datetime.datetime.now() - last_scrape_date).days

                    if days_since >= interval_days:
                        should_scrape = True
                        print(
                            f"⏰ {days_since} days since last scrape. Starting periodic update..."
                        )
                except Exception:
                    should_scrape = True
                    print(
                        "🚀 No valid last scrape found. Starting initial periodic scrape..."
                    )
        else:
            should_scrape = True
            print("🚀 Starting first periodic scrape...")

        if should_scrape:
            print("📊 Updating message statistics (views, forwards, etc.)...")
            await scrape_all_for_updates()

            # Save last scrape timestamp
            with open(last_scrape_file, "w") as f:
                json.dump(
                    {
                        "last_scrape": datetime.datetime.now().isoformat(),
                        "interval_days": interval_days,
                    },
                    f,
                )

            print(f"✅ Periodic scrape completed. Next update in {interval_days} days.")

        # Wait for next check (check daily)
        print(
            f"💤 Sleeping for 24 hours. Next check: {datetime.datetime.now() + datetime.timedelta(days=1)}"
        )
        await asyncio.sleep(24 * 60 * 60)  # 24 hours


async def scrape_all_for_updates():
    """
    Re-scrape all messages to update changing data like views and forwards.
    This doesn't add new records, just updates existing ones.
    """
    total = 0
    updated = 0

    async for message in client.iter_messages(ustoz_shogird):
        if not message.text:
            continue

        # Check if message exists in database
        existing = datadb.get(Query().message_id == message.id)
        if existing:
            # Update only the changing fields
            current_views = getattr(message, "views", 0)
            current_forwards = getattr(message, "forwards", 0)

            old_views = existing.get("views", 0)
            old_forwards = existing.get("forwards", 0)

            # Only update if there's a change
            if current_views != old_views or current_forwards != old_forwards:
                datadb.update(
                    {
                        "views": current_views,
                        "forwards": current_forwards,
                        "last_updated": datetime.datetime.now().isoformat(),
                    },
                    Query().message_id == message.id,
                )

                # Also save to stats table for historical tracking
                stats_data = {
                    "message_id": message.id,
                    "date": message.date.isoformat() if message.date else None,
                    "text_length": len(message.text) if message.text else 0,
                    "has_media": message.media is not None,
                    "views": current_views,
                    "forwards": current_forwards,
                    "processed_at": datetime.datetime.now().isoformat(),
                    "update_type": "periodic",
                }
                stats_table.insert(stats_data)

                updated += 1
                print(
                    f"📈 Updated message {message.id}: views {old_views}→{current_views}, forwards {old_forwards}→{current_forwards}"
                )

        total += 1
        if total % 100 == 0:
            print(f"🔄 Checked {total} messages, updated {updated} so far...")

    print(f"✅ Completed update: {updated}/{total} messages had changes")


async def get_hashtags():
    async for message in client.iter_messages(ustoz_shogird, limit=500):
        lst = message.text.split("\n")

        for line in lst:
            if line.startswith("#"):
                hashtags = line.split(" ")
                for h in hashtags:
                    # check if hashtag exists
                    if len(h) == 0 or h.isspace():
                        continue
                    if not hashtag.get(Hashtag.hashtag == h):
                        hashtag.insert({"hashtag": h, "count": 1})
                    else:
                        dct = hashtag.get(Hashtag.hashtag == h)
                        # update count
                        hashtag.update(
                            {"count": dct["count"] + 1}, Hashtag.hashtag == h
                        )


def run_scrape_all():
    with client:
        client.loop.run_until_complete(scrape_all())


def run_hashtags():
    with client:
        client.loop.run_until_complete(get_hashtags())


def run_listener():
    """Run the real-time message listener"""
    with client:
        client.loop.run_until_complete(start_listening())


def run_periodic(days=30):
    """Run periodic scraper with specified interval"""
    print(f"Starting periodic scraper (every {days} days)...")
    with client:
        client.loop.run_until_complete(scrape_periodic(days))


def run_periodic(days=30):
    """Run periodic scraper with specified interval"""
    print(f"Starting periodic scraper (every {days} days)...")
    with client:
        client.loop.run_until_complete(scrape_periodic(days))


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "listen":
            print("Starting listener mode...")
            run_listener()
        elif sys.argv[1] == "scrape":
            print("Starting scrape mode...")
            run_scrape_all()
        elif sys.argv[1] == "hashtags":
            print("Starting hashtag collection...")
            run_hashtags()
        elif sys.argv[1] == "periodic":
            # Default to monthly (30 days), or custom interval
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            print(f"Starting periodic mode (every {days} days)...")
            run_periodic(days)
        else:
            print("Usage: python scraping.py [listen|scrape|hashtags|periodic [days]]")
            print("Examples:")
            print("  python scraping.py periodic       # Monthly updates (30 days)")
            print("  python scraping.py periodic 7     # Weekly updates")
            print("  python scraping.py periodic 1     # Daily updates")
    else:
        print("Usage: python scraping.py [listen|scrape|hashtags|periodic [days]]")
        print("Examples:")
        print("  python scraping.py listen         # Real-time listener mode")
        print("  python scraping.py scrape         # Scrape all messages")
        print("  python scraping.py hashtags       # Collect hashtags")
        print("  python scraping.py periodic       # Monthly updates (30 days)")
        print("  python scraping.py periodic 7     # Weekly updates")
        print("  python scraping.py periodic 1     # Daily updates")
