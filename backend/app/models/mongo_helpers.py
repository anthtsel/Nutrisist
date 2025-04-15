from pymongo import MongoClient
from flask import current_app

class MongoConnection:
    @staticmethod
    def get_client():
        return MongoClient(current_app.config['MONGO_URI'])

    @staticmethod
    def get_db():
        client = MongoConnection.get_client()
        return client.get_default_database() 