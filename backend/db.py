import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")  # e.g. mongodb://localhost:27017
DB_NAME = os.getenv("MONGO_DB", "insideX")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION", "news")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]


def save_news(stock: str, analysis: str, source: str = "perplexity"):
    """Store raw news in MongoDB with timestamp."""
    doc = {
        "stock": stock,
        "analysis": analysis,
        "source": source,
        "timestamp": datetime.utcnow()
    }
    collection.insert_one(doc)
    return doc


def get_news(stock: str, limit: int = 5):
    """Retrieve latest news from MongoDB for a stock."""
    return list(
        collection.find({"stock": stock}).sort("timestamp", -1).limit(limit)
    )
