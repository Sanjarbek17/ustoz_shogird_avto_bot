#!/usr/bin/env python3
"""
Test to check recent messages and verify channel access
"""
from telethon import TelegramClient
import os
from dotenv import load_dotenv
import datetime

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
CHANNEL = "https://t.me/UstozShogird"

client = TelegramClient("anon", API_ID, API_HASH)


async def check_recent_messages():
    await client.start()

    try:
        entity = await client.get_entity(CHANNEL)
        print(f"✅ Connected to: {entity.title}")
        print(f"🆔 Channel ID: {entity.id}")
        print("-" * 50)

        # Get the last 10 messages to see recent activity
        messages = await client.get_messages(entity, limit=10)

        print(f"📊 Last 10 messages:")
        for i, msg in enumerate(messages, 1):
            print(f"  {i}. ID: {msg.id}")
            print(f"     Date: {msg.date}")
            print(f"     Text: {msg.text[:100] if msg.text else 'No text'}...")
            print(f"     ---")

        # Check if there are any very recent messages (last 2 hours)
        now = datetime.datetime.now(datetime.timezone.utc)
        recent_cutoff = now - datetime.timedelta(hours=2)

        recent_messages = [
            msg for msg in messages if msg.date and msg.date > recent_cutoff
        ]

        if recent_messages:
            print(f"\n🔥 RECENT MESSAGES (last 2 hours): {len(recent_messages)} found")
            for msg in recent_messages:
                print(f"   - ID {msg.id} at {msg.date}")
        else:
            print(f"\n❄️  No messages in the last 2 hours")

    except Exception as e:
        print(f"❌ Error: {e}")

    await client.disconnect()


if __name__ == "__main__":
    client.loop.run_until_complete(check_recent_messages())
