#!/usr/bin/env python3
"""
Debug script to test channel access and message listening
"""
from telethon import TelegramClient, events
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

# Target channel - try different formats
ustoz_shogird_formats = [
    "https://t.me/UstozShogird",  # Current format
    "@UstozShogird",              # @ format
    "UstozShogird",               # Plain username
    # Add channel ID if you know it: -1001234567890
]

client = TelegramClient("anon", API_ID, API_HASH)

async def test_channel_access():
    """Test if we can access the target channel"""
    await client.start()
    
    print("🔍 Testing channel access with different formats...")
    
    working_format = None
    channel_entity = None
    
    for channel_format in ustoz_shogird_formats:
        try:
            print(f"\n📋 Testing format: {channel_format}")
            entity = await client.get_entity(channel_format)
            
            print(f"✅ SUCCESS! Channel found:")
            print(f"   Title: {entity.title}")
            print(f"   ID: {entity.id}")
            print(f"   Username: {getattr(entity, 'username', 'No username')}")
            print(f"   Type: {type(entity).__name__}")
            
            # Try to get recent messages
            messages = await client.get_messages(entity, limit=3)
            print(f"   Recent messages: {len(messages)} found")
            
            if messages:
                print(f"   Last message ID: {messages[0].id}")
                print(f"   Last message date: {messages[0].date}")
                print(f"   Last message preview: {messages[0].text[:100] if messages[0].text else 'No text'}...")
            
            working_format = channel_format
            channel_entity = entity
            break
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
    
    if not working_format:
        print("\n🚨 ERROR: Could not access channel with any format!")
        print("Possible issues:")
        print("1. Channel doesn't exist or username is wrong")
        print("2. Channel is private and you're not a member")
        print("3. Your account doesn't have permission to access it")
        return None, None
    
    print(f"\n🎯 Use this format in your code: {working_format}")
    return working_format, channel_entity

async def test_message_listener(channel_format, entity):
    """Test the message listener with debug output"""
    if not channel_format:
        print("❌ Cannot test listener without valid channel access")
        return
    
    print(f"\n🎧 Starting message listener for: {channel_format}")
    print("📝 Send a message to the channel to test...")
    print("💡 Press Ctrl+C to stop\n")
    
    @client.on(events.NewMessage())
    async def debug_all_messages(event):
        """Listen to ALL messages for debugging"""
        chat_info = f"Chat: {event.chat.title if hasattr(event.chat, 'title') else 'Unknown'}"
        chat_id = f"ID: {event.chat_id}"
        username = f"Username: {getattr(event.chat, 'username', 'No username')}"
        
        print(f"📨 Message received - {chat_info}, {chat_id}, {username}")
        
        # Check if this is from our target channel
        if (event.chat_id == entity.id or 
            getattr(event.chat, 'username', '') == getattr(entity, 'username', '')):
            print(f"🎯 TARGET CHANNEL MESSAGE DETECTED!")
            print(f"   Message ID: {event.message.id}")
            print(f"   Text preview: {event.message.text[:100] if event.message.text else 'No text'}...")
        else:
            print(f"   (This is not from target channel)")
    
    @client.on(events.NewMessage(chats=entity))
    async def debug_target_messages(event):
        """Listen specifically to target channel"""
        print(f"🎯 TARGET CHANNEL SPECIFIC LISTENER TRIGGERED!")
        print(f"   Message ID: {event.message.id}")
        print(f"   Date: {event.message.date}")
        print(f"   Text: {event.message.text[:200] if event.message.text else 'No text'}...")
    
    # Keep listening
    await client.run_until_disconnected()

async def main():
    """Main debug function"""
    print("🚀 Telegram Channel Debug Tool")
    print("=" * 50)
    
    # Test 1: Channel access
    working_format, entity = await test_channel_access()
    
    if working_format and entity:
        print("\n" + "=" * 50)
        print("✅ Channel access successful!")
        print(f"🔧 Update your code to use: ustoz_shogird = \"{working_format}\"")
        
        # Ask user if they want to test listener
        print("\n🎧 Ready to test message listener...")
        print("This will listen for new messages. Send a test message to the channel.")
        
        try:
            await test_message_listener(working_format, entity)
        except KeyboardInterrupt:
            print("\n👋 Listener stopped by user")
    else:
        print("\n❌ Cannot proceed with listener test due to channel access issues")
    
    await client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Debug session ended")