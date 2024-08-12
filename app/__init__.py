from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import addresses, update, ens

def create_app() -> FastAPI:
    app = FastAPI()
    
    # Enable CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allows all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allows all methods
        allow_headers=["*"],  # Allows all headers
    )
    
    app.include_router(addresses.router)
    app.include_router(update.router)
    app.include_router(ens.router)
    return app

app = create_app()