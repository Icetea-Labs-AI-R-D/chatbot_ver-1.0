from fastapi import APIRouter, Depends, Request, status
from models.dto import ConversationRequest
from fastapi.responses import StreamingResponse, JSONResponse
from services.openai_service import OpenAIService
from controllers.chat_controller import ChatController
from langsmith import traceable
from services import get_chroma_service, get_openai_service
from controllers import get_chat_controller
from database.queue import AsyncQueue

router = APIRouter()

async_queue = AsyncQueue()


async def too_many_requests_generator():
    yield b'{"detail": "Too many requests, please try again later."}'


@router.post("/chatbot/v1/request")
@traceable
async def conversation(
    request: Request,
    openai_service: OpenAIService = Depends(get_openai_service),
    chat_controller: ChatController = Depends(get_chat_controller),
):
    data = await request.json()
    conversation_dto = ConversationRequest(**data)
    openai_client = await async_queue.get()
    if openai_client != None:
        data_qa = await chat_controller.get_data_for_rag(
            conversation_dto, openai_client
        )
        return StreamingResponse(
            openai_service.ask_openai_with_rag(
                data_qa["user_question"],
                conversation=data_qa["conversation"],
                context=data_qa["context"],
                global_topic=data_qa["global_topic"],
                openai_client=openai_client,
                features_keywords=data_qa["features_keywords"],
            ),
            media_type="text/event-stream",
        )
    headers = {"Content-Type": "application/json"}
    return StreamingResponse(
        too_many_requests_generator(),
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        headers=headers,
    )
