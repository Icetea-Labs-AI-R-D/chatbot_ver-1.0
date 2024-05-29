from fastapi import APIRouter, Depends, Request, status
from models.dto import ConversationRequest
from fastapi.responses import StreamingResponse, JSONResponse
from services.openai_service import OpenAIService
from controllers.chat_controller import ChatController
from langsmith import traceable
from services import get_openai_service
from controllers import get_chat_controller, get_report_controller
from database.queue import AsyncQueue
from utils.static_param import many_requests_generator
from controllers.report_controller import ReportController
from models.dto import ReportRequest

router = APIRouter()

async_queue = AsyncQueue()


@router.post("/api/chatbot/v1/new")
async def new(
    requests: Request, chat_controller: ChatController = Depends(get_chat_controller)
):
    data = await requests.json()
    await chat_controller.new_conversation(data.get("conversation_id"))
    return JSONResponse(
        status_code=status.HTTP_200_OK, content={"message": "New conversation"}
    )


@router.post("/api/chatbot/v1/chat")
@traceable
async def chat(
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
                new_conversation=data_qa["new_conversation"],
                selected_suggestions=data_qa["selected_suggestions"],
                rag=data_qa["rag"],
            ),
            status_code=status.HTTP_200_OK,
            media_type="text/event-stream",
        )
    print("Too many requests")
    return StreamingResponse(
        many_requests_generator(),
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        media_type="text/event-stream",
    )


@router.post("/api/chatbot/v1/report")
async def report(
    request: Request,
    report_controller: ReportController = Depends(get_report_controller),
):
    data = await request.json()
    await report_controller.generate_report(ReportRequest(**data))
    return JSONResponse(
        status_code=status.HTTP_200_OK, content={"message": "Report created"}
    )


@router.post("/api/chatbot/v1/upcoming_ido")
async def upcoming_ido(
    request: Request, openai_service: OpenAIService = Depends(get_openai_service)
):
    data = await request.json()
    return StreamingResponse(
        openai_service.list_upcoming_ido(data.get("conversation_id")),
        status_code=status.HTTP_200_OK,
        media_type="text/event-stream",
    )
