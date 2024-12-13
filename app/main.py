from fastapi.middleware.cors import CORSMiddleware
from . import app

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",           # Allow localhost without a port
        "http://localhost:8000",      # Allow localhost on port 8000
        "http://localhost:3000",      # Allow localhost on port 3000 (common for React dev servers)
        "https://prime-maxi.com",     # Example production origin
        "https://*.app-paragonsdao-com.pages.dev/",  # Wildcard subdomains
        "https://paragonsdao.com",    # Specific domain
        "https://*.paragonsdao.com"   # Wildcard subdomains
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
