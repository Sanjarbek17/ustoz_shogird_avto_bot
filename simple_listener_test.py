#!/usr/bin/env python3
"""
Simple listener test for UstozShogird channel
"""
from telethon import TelegramClient, events
import os
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
CHANNEL = "https://t.me/UstozShogird"

client = TelegramClient("anon", API_ID, API_HASH)

@client.on(events.NewMessage(chats=CHANNEL))
async def handler(event):
    """Handle messages from UstozShogird channel"""
    print(f"🎯 NEW MESSAGE FROM USTOZ-SHOGIRD!")
    print(f"   Message ID: {event.message.id}")
    print(f"   Date: {event.message.date}")
    print(f"   Text preview: {event.message.text[:200] if event.message.text else 'No text'}...")
    print("-" * 50)

async def main():
    await client.start()
    
    # Test channel access first
    try:
        entity = await client.get_entity(CHANNEL)
        print(f"✅ Connected to: {entity.title}")
        print(f"🆔 Channel ID: {entity.id}")
        
        # Check if we can get messages (means we have access)
        messages = await client.get_messages(entity, limit=1)
        if messages:
            print(f"📨 Last message ID: {messages[0].id}")
            print(f"📅 Last message date: {messages[0].date}")
        
        print(f"\n🎧 Listening for new messages...")
        print(f"⏰ Channel posts every hour, so wait for the next post...")
        print(f"💡 Press Ctrl+C to stop\n")
        
        await client.run_until_disconnected()
        
    except Exception as e:
        print(f"❌ Error accessing channel: {e}")

if __name__ == "__main__":
    try:
        client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n👋 Listener stopped")