from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


def static_middleware(app: FastAPI):
    app.mount("/assets", StaticFiles(directory="./app/templates"), name="assets")