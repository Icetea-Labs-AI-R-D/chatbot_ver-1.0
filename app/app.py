import os
from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn
from middlewares import cors_middleware
from routers import ApiRouter

load_dotenv()

print(os.getenv('OPENAI_API_KEY'))

app = FastAPI()

# middleware configuration
cors_middleware(app)

# Routes
ApiRouter(app)