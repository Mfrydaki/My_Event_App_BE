import certifi
from pymongo import MongoClient
from django.conf import settings

client = MongoClient(settings.MONGODB_URI , tlsCAFile=certifi.where())

db = client[settings.MONGODB_DB_NAME]
events_collection = db["events"]