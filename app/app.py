import os
from dotenv import load_dotenv
from fastapi import FastAPI
from middlewares import cors_middleware
from api.v1.api_router import router
from contextlib import asynccontextmanager
from database import db
from database.queue import AsyncQueue

load_dotenv('../.env')

async_queue = AsyncQueue()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await async_queue.init_queue()
    yield

app = FastAPI(lifespan=lifespan)
cors_middleware(app)
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=9191,workers=2)
    # uvicorn.run("app:app", host="0.0.0.0", port=9191)