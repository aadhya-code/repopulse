import os
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/repopulse")

_client = MongoClient(MONGO_URI)
db = _client.get_default_database()

commits_collection = db["commits"]
pulls_collection = db["pullrequests"]
