from fastapi.middleware.cors import CORSMiddleware
from . import app

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:8000",
        "http://localhost:3000",
        "https://prime-maxi.com",
        "https://paragonsdao.com",
        "https://www.paragonsdao.com",
        "https://app.paragonsdao.com"
    ],
    allow_origin_regex=r"https://.*\.app-paragonsdao-com\.pages\.dev",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
