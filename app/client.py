import os
from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn
from middlewares import static_middleware
from routers import PageRouter

load_dotenv()

print(os.getenv('OPENAI_API_KEY'))

app_client = FastAPI()

# middleware configuration
static_middleware(app_client)

# Routes
PageRouter(app_client)

if __name__ == '__main__':
    uvicorn.run(app_client, host='localhost', port=8000)