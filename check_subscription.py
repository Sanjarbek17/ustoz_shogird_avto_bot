#!/usr/bin/env python3
"""
Check if we're subscribed to the channel
"""
from telethon import TelegramClient
import os
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
CHANNEL = "https://t.me/UstozShogird"

client = TelegramClient("anon", API_ID, API_HASH)


async def check_subscription():
    await client.start()

    try:
        entity = await client.get_entity(CHANNEL)
        print(f"✅ Channel: {entity.title}")
        print(f"🆔 Channel ID: {entity.id}")

        # Check if we're a participant
        try:
            # This will throw an error if we're not a member
            participant = await client.get_participants(entity, limit=1)
            print(f"✅ We are subscribed/joined to the channel")

            # Get our participation info
            me = await client.get_me()
            my_participation = await client(
                GetParticipantRequest(channel=entity, participant=me)
            )
            print(
                f"📊 Our status in channel: {type(my_participation.participant).__name__}"
            )

        except Exception as e:
            print(f"❌ Subscription check failed: {e}")
            print(f"💡 Try joining the channel manually first!")

        # Try to join the channel programmatically
        try:
            await client(JoinChannelRequest(entity))
            print(f"✅ Successfully joined the channel!")
        except Exception as e:
            if "already" in str(e).lower():
                print(f"✅ Already a member of the channel")
            else:
                print(f"❌ Failed to join: {e}")

    except Exception as e:
        print(f"❌ Error accessing channel: {e}")

    await client.disconnect()


if __name__ == "__main__":
    # Import required functions
    from telethon.tl.functions.channels import JoinChannelRequest, GetParticipantRequest

    client.loop.run_until_complete(check_subscription())
