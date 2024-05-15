import os
from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn
from middlewares import cors_middleware
from api.v1.api_router import router

load_dotenv()

def get_application() -> FastAPI:
    application = FastAPI()
    cors_middleware(application)
    application.include_router(router)

    return application

app = get_application()