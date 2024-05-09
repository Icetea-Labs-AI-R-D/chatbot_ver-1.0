from .base_router import BaseRouter
from fastapi import FastAPI, Request
from models.dto import ConversationRequest
from fastapi.responses import StreamingResponse
from services import OpenAIService
from langsmith.wrappers import wrap_openai
from langsmith import traceable

class ApiRouter(BaseRouter):
    
    openai_service: OpenAIService
    def __init__(self, app: FastAPI) -> None:
        super().__init__()
        self._init_routes(app)
        self.openai_service = OpenAIService()

    def _init_routes(self, app: FastAPI) -> None:
        @app.post("/backend/v1/request")
        @traceable
        async def _conversation(request: Request):
            data = await request.json()
            conversation_dto = ConversationRequest(**data)
            data_qa = await self.chat_controller._qa_conversation(conversation_dto)
            return StreamingResponse(self.openai_service._ask_OpenAI_with_RAG(data_qa['user_question'], conversation= data_qa['conversation'], context=data_qa['context'], previous_topic=data_qa['previous_topic']), media_type="text/event-stream")