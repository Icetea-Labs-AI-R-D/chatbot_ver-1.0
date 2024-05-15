from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn
from middlewares import static_middleware
from api.v1.page_router import router

load_dotenv()

def get_application() -> FastAPI:
    application = FastAPI()
    static_middleware(application)
    application.include_router(router)

    return application

app = get_application()

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)