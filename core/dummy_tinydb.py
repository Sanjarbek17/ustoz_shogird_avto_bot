from tinydb import TinyDB, Query
from pprint import pprint

# db = TinyDB('data_json/hashtag.json', indent=4, separators=(',', ': '))
# db = TinyDB('data_json/user.json', indent=4, separators=(',', ': '))

# db = db.table('hashtag')
# User = Query()

# search = db.search(User.hashtag.exists())

# search.sort(key=lambda x: x['count'], reverse=True)
# pprint(search)

db = TinyDB('data_json/user.json', indent=4, separators=(',', ': '))

db = db.table('user')
db.truncate()
users = db.all()
# data = users[0]
for i in range(10):
    db.insert({
            "id": 7662812087,
            "username": "Sanjarbek177",
            "first_name": "Saidov Sanjarbek",
            "last_name": None,
            "hashtags": [
                "#xodim",
                "#flutter"
            ]
        })