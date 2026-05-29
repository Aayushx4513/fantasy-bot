from pymongo import MongoClient
import ssl

MONGO_URL = "mongodb://Aayushbot:cricketbot%40123@ac-xgbsmge-shard-00-00.lmmhitx.mongodb.net:27017,ac-xgbsmge-shard-00-01.lmmhitx.mongodb.net:27017,ac-xgbsmge-shard-00-02.lmmhitx.mongodb.net:27017/?ssl=true&replicaSet=atlas-xhb7s7-shard-0&authSource=admin"

client = MongoClient(MONGO_URL, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=5000)
db = client['fantasy_bot']

print("✅ MongoDB Connected!", client.server_info())
