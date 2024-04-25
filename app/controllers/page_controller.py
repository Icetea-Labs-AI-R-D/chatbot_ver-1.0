from fastapi import Request
from fastapi.responses import RedirectResponse, StreamingResponse
import httpx
import requests
from time import time
import json
from os import urandom
from fastapi.templating import Jinja2Templates

class PageController:
    templates: Jinja2Templates
    def __init__(self):
        self.templates = Jinja2Templates(
            directory="./app/templates/html"
        )

    def _chat(self, request: Request, conversation_id: str):
        if '-' not in conversation_id:
            return RedirectResponse(url="/chat/")
        return self.templates.TemplateResponse("index.html", {"request": request, "chat_id": conversation_id})
    
    def _index(self, request: Request):
        chat_id = f'{urandom(4).hex()}-{urandom(2).hex()}-{urandom(2).hex()}-{urandom(2).hex()}-{hex(int(time() * 1000))[2:]}'
        print(chat_id)
        return self.templates.TemplateResponse("index.html", {"request": request, "chat_id": chat_id})
    
    def _root(self):
        return RedirectResponse(url="/chat/")
    
    async def _stream_response(self, data):
        url = 'http://127.0.0.1:9191/backend/v1/request'
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", url, json=data) as r:
                async for chunk in r.aiter_bytes():
                    yield chunk