from motor import motor_asyncio, core
from pymongo.driver_info import DriverInfo

DRIVER_INFO = DriverInfo(name="chatbot", version="1.0.0")
class _MongoClientSingleton:
    mongo_client: motor_asyncio.AsyncIOMotorClient = None
    
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(_MongoClientSingleton, cls).__new__(cls)
            cls.instance.mongo_client = motor_asyncio.AsyncIOMotorClient(
                'mongodb://localhost:27017',
                driver=DRIVER_INFO
            )
        return cls.instance

def MongoDatabase() -> core.AgnosticClient:
        return _MongoClientSingleton().mongo_client['chatbot']