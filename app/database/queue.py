import asyncio
from langsmith.wrappers import wrap_openai
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv("../../.env")


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class AsyncQueue(metaclass=SingletonMeta):
    queue: asyncio.Queue

    def __init__(self):
        self.queue = asyncio.Queue()

    async def put(self, item):
        await self.queue.put(item)

    async def get(self):
        length = self.queue.qsize()
        item = None
        if length > 0:
            item = await self.queue.get()
            self.queue.task_done()
        return item

    async def empty(self):
        return await self.queue.empty()

    async def init_queue(self):
        self.queue = asyncio.Queue()
        if self.queue.empty():
            apis = [
                wrap_openai(AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY1")))
                for _ in range(5)
            ] + [
                wrap_openai(AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY2")))
                for _ in range(5)
            ]
            for api in apis:
                await self.put(api)
