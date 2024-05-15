from services.openai_service import OpenAIService
from services.chroma_service import ChromaService
from database.session import MongoDatabase

def get_openai_service():
    return OpenAIService()

def get_chroma_service():
    return ChromaService()

def get_db():
    return MongoDatabase()