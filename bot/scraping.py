from pprint import pprint
from telethon import TelegramClient, events
from tinydb import TinyDB, Query

import os
from dotenv import load_dotenv

from core.getting_data import to_json

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
TOKEN = os.getenv("BOT_TOKEN")

music_bot = "@music_storage1718_bot"
ustoz_shogird = "@UstozShogird"

client: TelegramClient = TelegramClient("anon", API_ID, API_HASH)
bot: TelegramClient = TelegramClient("anon2", API_ID, API_HASH).start(bot_token=TOKEN)

db = TinyDB("data_json/data.json", indent=4, separators=(",", ": "), encoding="utf-8")
hashdb = TinyDB(
    "data_json/hashtag.json", sort_keys=True, indent=4, separators=(",", ": ")
)

datadb = db.table("data")


Hashtag = Query()
hashtag = hashdb.table("hashtag")


async def scrape_all():
    """
    Scrape all messages from the channel in reverse order, saving progress to allow resuming.
    Progress is tracked by last processed message ID in a file.
    """
    import json

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
        dct = to_json(lst)
        datadb.insert(dct)
        last_id = message.id
        total += 1
        # Save progress every 20 messages
        if total % 20 == 0:
            with open(progress_file, "w") as f:
                json.dump({"last_id": last_id}, f)
    # Save final progress
    if last_id is not None:
        with open(progress_file, "w") as f:
            json.dump({"last_id": last_id}, f)


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


def run_main():
    with client:
        client.loop.run_until_complete(scrape_all())


def run_hashtags():
    with client:
        client.loop.run_until_complete(get_hashtags())


if __name__ == "__main__":
    run_main()
