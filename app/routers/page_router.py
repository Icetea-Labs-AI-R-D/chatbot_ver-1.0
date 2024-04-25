from .base_router import BaseRouter
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse

class PageRouter(BaseRouter):
    def __init__(self, app: FastAPI) -> None:
        super().__init__()
        self._init_routes(app)

    def _init_routes(self, app: FastAPI) -> None:
        @app.get("/chat/", response_class=HTMLResponse)
        def index(request: Request):
            return self.page_controller._index(request)

        @app.get("/", response_class=HTMLResponse)
        def root():
            return self.page_controller._root()
        
        @app.get("/chat/{conversation_id}", response_class=HTMLResponse)
        def chat(request: Request, conversation_id: str):
            return self.page_controller._chat(request, conversation_id)
        
        @app.post("/backend-api/v1/conversation")
        async def conversation(request: Request):
            data = await request.json()
            return StreamingResponse(self.page_controller._stream_response(data), media_type="text/event-stream")