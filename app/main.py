from fastapi.middleware.cors import CORSMiddleware
from . import app

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://prime-maxi.com"],  # Add http:// version too if needed
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
