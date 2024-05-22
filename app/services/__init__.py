from .chroma_service import ChromaService
from .openai_service import OpenAIService

async def get_chroma_service() -> ChromaService:
    return ChromaService()

async def get_openai_service() -> OpenAIService:
    return OpenAIService()