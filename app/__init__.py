from fastapi import FastAPI
from .routes import addresses, update

def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(addresses.router)
    app.include_router(update.router)
    return app

app = create_app()
