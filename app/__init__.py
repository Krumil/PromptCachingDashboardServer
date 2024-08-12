from fastapi import FastAPI
from .routes import addresses, update, ens

def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(addresses.router)
    app.include_router(update.router)
    app.include_router(ens.router)
    return app

app = create_app()
