import os
from dotenv import load_dotenv
from fastapi import FastAPI
from middlewares import cors_middleware
from database.queue import AsyncQueue
from fastapi.responses import Response

load_dotenv('../.env')

async_queue = AsyncQueue()

app = FastAPI()
cors_middleware(app)

@app.post("/put")
async def put():
    print("put")
    await async_queue.put("test")

@app.get("/init")
async def init():
    await async_queue.init_queue()
    
@app.get("/get")
async def get():
    print('get')
    return await async_queue.get()

@app.get("/")
async def size():
    print('hello')
