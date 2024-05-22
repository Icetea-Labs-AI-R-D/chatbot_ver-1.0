from motor import motor_asyncio, core
import logging
import datetime

class MongoManager:
    client: motor_asyncio.AsyncIOMotorClient = None
    db: motor_asyncio.AsyncIOMotorDatabase = None
    
    def __init__(self) -> None:
        self.client = motor_asyncio.AsyncIOMotorClient(
            "mongodb://localhost:27017",
            maxPoolSize=10,
            minPoolSize=10)
        self.db = self.client.chatbot
    
    async def get_conversation(
        self,
        conversation_id: str
    ):
        conversation = await self.db.conversation.find_one(
            {
                'conversation_id': conversation_id
            },
            sort=[('start_date', -1)]
        )
        return conversation or {}

    async def add_conversation(
        self,
        conversation_id: str,
        message: dict
    ):
        await self.db.conversation.find_one_and_update(
            {
                'conversation_id': conversation_id,
                'count': {'$lt': 20}
            }
            ,
            {
                '$push': {
                    "history": [
                    {
                        "role": message.get('role_user'),
                        "content": message.get('content_user')
                    },
                    {
                        "role": message.get('role_assistant'),
                        "content": message.get('content_assistant')
                    }
                    ]
                },
                "$set": {
                    "global_topic": message.get('global_topic')
                },
                "$inc": { "count": 1 },
                "$setOnInsert": {
                    "conversation_id": conversation_id,
                    "start_date": datetime.datetime.now(),
                    "status": "open",
                    "report": []
                }
            },
            new=True,
            upsert=True
        )
    
    async def hi(self, content: str):
        print(content)