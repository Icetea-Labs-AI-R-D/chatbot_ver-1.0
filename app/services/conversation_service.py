from threading import Lock

class Singleton:
    _instance = None
    _look : Lock = Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._look:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
class ConversationService(Singleton):
    conversations: dict
    def __init__(self):
        self.conversations = {}
    def add_conversation(self, conversation: dict):
        self.conversations[conversation['conversation_id']] = conversation['history']

    def get_conversation(self, conversation_id):
        return self.conversations.get(conversation_id, [])