import datetime
from database.database import Database, get_db
    
class MongoService():
    mongd: Database
    def __init__(self):
        self.mongd = get_db()

    def add_conversation(self, conversation_id, message):
        return self.mongd.db['conversation'].find_one_and_update(
            {
                'conversation_id': conversation_id,
                'count': {'$lt': 20}
            }
            ,
            {
                '$push': {
                    "history": {
                        "role": message.get('role', None),
                        "content": message.get('content', None),
                        "previous_topic": message.get('previous_topic', None),
                    }
                },
                "$inc": { "count": 1 },
                "$setOnInsert": {
                    "conversation_id": conversation_id,
                    "start_date": datetime.datetime.now(),
                }
            },
            new=True,
            upsert=True
        )
    
    def get_conversation(self, conversation_id):
        conver = self.mongd.db['conversation'].find(
            {
                'conversation_id': conversation_id,
                'start_date': {'$gte': datetime.datetime.now() - datetime.timedelta(minutes=30)}
            }
        )
        conversation = []
        for c in conver:
            conversation.extend(c['history'])
        return conversation