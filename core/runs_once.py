from tinydb import TinyDB, Query

db = TinyDB('db.json', indent=4, separators=(',', ': '))

db = db.table('users')

db.insert({'name': 'user1', 'groups': ['admin', 'user']})
db.insert({'name': 'user2', 'groups': ['user']})
db.insert({'name': 'user3', 'groups': ['sudo', 'user']})