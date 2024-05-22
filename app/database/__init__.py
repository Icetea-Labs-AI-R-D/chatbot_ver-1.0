from .session import MongoManager

db = MongoManager()

async def get_db() -> MongoManager:
    return db