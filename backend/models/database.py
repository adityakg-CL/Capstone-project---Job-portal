from pymongo import MongoClient
from pymongo.database import Database
from config.config import get_settings

_client: MongoClient | None = None

def connect() -> None:
    global _client
    settings = get_settings()
    _client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=3000)
    _client.admin.command("ping")

def close() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None

def get_database() -> Database:
    if _client is None:
        raise RuntimeError("MongoDB is not connected")
    return _client[get_settings().mongodb_database]

def get_client() -> MongoClient:
    if _client is None:
        raise RuntimeError("MongoDB is not connected")
    return _client
