from pymongo import MongoClient
from dotenv import load_dotenv
import os
import uuid
from datetime import datetime

# Load environment variables
load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DB_NAME")]
logs_collection = db["backend_logs"]

def log_json(endpoint_name: str, json_data: dict):
    """
    Logs JSON output from backend endpoints to MongoDB anonymously.
    """
    log_entry = {
        "session_id": str(uuid.uuid4()),  # Random anonymous ID
        "endpoint": endpoint_name,
        "data": json_data,
        "timestamp": datetime.utcnow()
    }

    try:
        logs_collection.insert_one(log_entry)
        print(f"[LOG] Stored response for endpoint: {endpoint_name}")
    except Exception as e:
        print(f"[ERROR] Failed to log data: {e}")
