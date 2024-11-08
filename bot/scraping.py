from pprint import pprint
from telethon import TelegramClient, events
from tinydb import TinyDB, Query

import os
from dotenv import load_dotenv

from core.getting_data import to_json

load_dotenv()

API_ID = os.getenv( 'API_ID' )
API_HASH = os.getenv( 'API_HASH' )
ustoz_shogird = '@UstozShogird'

client = TelegramClient('anon', API_ID, API_HASH)

db = TinyDB('data_json/data.json', indent=4, separators=(',', ': '))
hashdb = TinyDB('data_json/hashtag.json', indent=4, separators=(',', ': '))

datadb = db.table('data')


Hashtag = Query()
hashtag = hashdb.table('hashtag')

async def main(limit=100):
    datadb.truncate()
    async for message in client.iter_messages(ustoz_shogird, limit=limit):
        lst = message.text.split('\n\n')
        if len(lst) < 4:
            continue
        dct = to_json(lst)
        datadb.insert(dct)

async def get_hashtags(limit=100):
    async for message in client.iter_messages(ustoz_shogird, limit=limit):
        lst = message.text.split('\n')
        
        for line in lst:
            if line.startswith('#'):
                hashtags = line.split(' ')
                for h in hashtags:
                    # check if hashtag exists
                    if len(h) == 0 or h.isspace():
                        continue
                    if not hashtag.get(Hashtag.hashtag == h):
                        hashtag.insert({'hashtag': h, 'count': 1})
                    else:
                        dct = hashtag.get(Hashtag.hashtag == h)
                        # update count
                        hashtag.update({'count': dct['count'] + 1}, Hashtag.hashtag == h)

def run_main(limit=100):
    with client:
        client.loop.run_until_complete(main(limit))

def run_hashtags(limit=100):
    with client:
        client.loop.run_until_complete(get_hashtags(limit))

if __name__ == '__main__':
    run_main()