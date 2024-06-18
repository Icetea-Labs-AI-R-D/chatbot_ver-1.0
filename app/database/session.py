from motor import motor_asyncio, core
import logging
import datetime


class MongoManager:
    client: motor_asyncio.AsyncIOMotorClient = None
    db: motor_asyncio.AsyncIOMotorDatabase = None

    def __init__(self) -> None:
        self.client = motor_asyncio.AsyncIOMotorClient(
            "mongodb://root:gamefichatbot@localhost:27017/", 
            
            maxPoolSize=10, 
            minPoolSize=10,
        )
        self.db = self.client.chatbot

    async def get_conversation(self, conversation_id: str):
        conversation = await self.db.conversation.find_one(
            {
                "conversation_id": conversation_id,
                "last_update": {
                    "$gt": datetime.datetime.now() - datetime.timedelta(minutes=5)
                },
                "status": "open",
            },
            sort=[("last_update", -1)],
        )
        return conversation or {}
    
    async def get_report_conversation(self, conversation_id: str):
        conversation = await self.db.conversation.find_one(
            {
                "conversation_id": conversation_id,
            },
            sort=[("last_update", -1)],
        )
        return conversation or {}

    async def add_conversation(self, conversation_id: str, message: dict):
        await self.db.conversation.find_one_and_update(
            {
                "conversation_id": conversation_id,
                "count": {"$lt": 20},
                "last_update": {
                    "$gt": datetime.datetime.now() - datetime.timedelta(minutes=5)
                },
                "status": "open",
            },
            {
                "$push": {
                    "history": {
                        "content_user": message.get("content_user"),
                        "content_assistant": message.get("content_assistant"),
                        "suggestion": message.get("suggestion"),
                        "context": message.get("context"),
                        "features_keywords": message.get("features_keywords"),
                    }
                },
                "$set": {
                    "last_update": datetime.datetime.now(),
                    "global_topic": message.get("topic"),
                    "selected_suggestions": message.get("selected_suggestions"),
                },
                "$inc": {"count": 1},
                "$setOnInsert": {
                    "conversation_id": conversation_id,
                    "status": "open",
                },
            },
            new=True,
            upsert=True,
        )

    async def close_conversation(self, conversation_id: str):
        await self.db.conversation.find_one_and_update(
            {
                "conversation_id": conversation_id,
                "count": {"$lt": 20},
                "last_update": {
                    "$gt": datetime.datetime.now() - datetime.timedelta(minutes=5)
                },
                "status": "open",
            },
            {"$set": {"status": "close"}},
        )
        
    async def new_conversation(self, conversation_id: str):
        await self.db.conversation.insert_one(
            {
                "conversation_id": conversation_id,
                "count": 0,
                "last_update": datetime.datetime.now(),
                "status": "open",
            }
        )

