from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

mongo_uri = os.getenv("MONGO_URI")
mongo_db_name = os.getenv("MONGO_DB_NAME")

print("URI:", mongo_uri)
print("DB name:", mongo_db_name)

client = MongoClient(mongo_uri)
db = client[mongo_db_name]

print("Connected to:", db.name)
print("Collections:", db.list_collection_names())
