import atexit
import certifi
from pymongo import MongoClient
from django.conf import settings

_client = None
_db = None


def get_client() -> MongoClient:
    """
    Get (and cache) a MongoDB client instance.

    Returns
    -------
    MongoClient
    A connected MongoDB client.
    """
    global _client
    if _client is None:
        uri = getattr(settings, "MONGODB_URI", None)
        if not uri:
            raise RuntimeError("MONGODB_URI is missing from settings/.env")
        _client = MongoClient(
            uri,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5000
        )
    return _client


def get_db():
    """
    Get (and cache) the target MongoDB database.

    Returns
    -------
    Database
    The MongoDB database object.
    """
    global _db
    if _db is None:
        client = get_client()
        db_name = getattr(settings, "MONGODB_DB_NAME", "my_events_backend")
        _db = client[db_name]
    return _db


def get_events_collection():
    """
    Get the events collection from the database.

    Returns
    -------
    Collection
    The MongoDB collection for events.
    """
    name = getattr(settings, "MONGODB_EVENTS_COLLECTION", "events")
    return get_db()[name]


def get_users_collection():
    """
    Get the users collection from the database.

    Returns
    -------
    Collection
    The MongoDB collection for users.
    """
    name = getattr(settings, "MONGODB_USERS_COLLECTION", "users")
    return get_db()[name]


@atexit.register
def _close_client():
    """
    Close the global MongoClient on process exit.
    """
    global _client
    if _client is not None:
        _client.close()
