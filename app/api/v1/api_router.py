from fastapi import APIRouter, Depends, Request, Body
from models.dto import ConversationRequest
from fastapi.responses import StreamingResponse
from services.openai_service import OpenAIService
from controllers.chat_controller import ChatController
from langsmith import traceable
from help import deps

router = APIRouter()

@router.post("/backend/v1/request")
@traceable
def conversation(conversation_dto: ConversationRequest, openai_service: OpenAIService = Depends(deps.get_openai_service)):
    data_qa = ChatController.get_data_for_rag(conversation_dto)
    return StreamingResponse(openai_service.ask_openai_with_rag(data_qa['user_question'], conversation= data_qa['conversation'], context=data_qa['context'], global_topic=data_qa['global_topic']), media_type="text/event-stream")