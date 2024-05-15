import datetime
from motor.core import AgnosticDatabase
from typing import Any, Generator, Annotated
from fastapi import Depends, HTTPException
from database.session import MongoDatabase

async def get_conversation(
    conversation_id: str,
    db = MongoDatabase()
):
    conversation = await db['conversation'].find_one(
        {
            'conversation_id': conversation_id
        },
        sort=[('start_date', -1)]
    )
    if conversation:
        return conversation
    return {}

async def add_conversation(
    conversation_id: str,
    message: dict,
    db = MongoDatabase()
):
    await db['conversation'].find_one_and_update(
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