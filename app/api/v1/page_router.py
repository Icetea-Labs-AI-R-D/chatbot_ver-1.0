from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from controllers.page_controller import PageController
from typing import Annotated

router = APIRouter()

@router.get("/chat/", response_class=HTMLResponse)
def index(request: Request, page_controller: PageController = Depends()):
    return page_controller._index(request)

@router.get("/", response_class=HTMLResponse)
def root(page_controller: PageController = Depends()):
    return page_controller._root()
        
@router.get("/chat/{conversation_id}", response_class=HTMLResponse)
def chat(request: Request, conversation_id: str, page_controller: PageController = Depends()):
    return page_controller._chat(request, conversation_id)
        
@router.post("/backend-api/v1/conversation")
async def conversation(request: Request, page_controller: PageController = Depends()):
    data = await request.json()
    return StreamingResponse(page_controller._stream_response(data), media_type="text/event-stream")