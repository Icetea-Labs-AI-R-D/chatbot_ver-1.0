from pymongo import MongoClient
from typing import Optional

class Database:
    _instance = None
    def __new__(cls):
        
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.client = MongoClient("localhost", 27017)
            cls._instance.db = cls._instance.client["chatbot"]
        return cls._instance

def get_db() -> Optional[Database]:
    return Database()._instance.db