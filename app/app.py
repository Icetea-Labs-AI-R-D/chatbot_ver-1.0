import os
from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn
from middlewares import cors_middleware, static_middleware
from routers import ApiRouter, PageRouter
import asyncio

load_dotenv()

print(os.getenv('OPENAI_API_KEY'))

app_client = FastAPI()
app_server = FastAPI()

# middleware configuration
cors_middleware(app_server)
static_middleware(app_client)

# Routes
ApiRouter(app_server)
PageRouter(app_client)

def run_app(app, host, port):
    config = uvicorn.Config(app=app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    return server.serve()

async def main():
    client_server = asyncio.create_task(run_app(app_client, 'localhost', 8080))
    api_server = asyncio.create_task(run_app(app_server, 'localhost',9191))
    await asyncio.gather(client_server, api_server)
    
if __name__ == "__main__":
    asyncio.run(main())