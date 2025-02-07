from fastapi import FastAPI
from .routes import addresses, update, ens, stats

def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(addresses.router)
    app.include_router(update.router)
    app.include_router(ens.router)
    app.include_router(stats.router)
    return app

app = create_app()
