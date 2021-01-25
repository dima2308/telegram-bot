import os
import pymongo
import dns

TG_TOKEN = os.environ.get('TG_TOKEN')
WEATHERSTACK_API_KEY = os.environ.get('WEATHERSTACK_API_KEY')

MONGO_BD_NAME = os.environ.get('TG_BOT')
MONGO_DB_PASSWORD = os.environ.get('BD_PASSWORD')
MONGO_DB_LINK = 'mongodb+srv://Dmitry:{}@cluster0.4w26s.mongodb.net/{}?retryWrites=true&w=majority'.format(
    MONGO_DB_PASSWORD, MONGO_BD_NAME)

client = pymongo.MongoClient(MONGO_DB_LINK)
