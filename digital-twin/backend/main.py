from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# Import API router
from api import api_router

app = FastAPI(
    title="Digital Twin Simulation Sandbox",
    description="Production-grade digital twin for EV battery swap networks",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)

@app.get("/")
def read_root():
    return {
        "message": "Digital Twin Simulation Sandbox API",
        "version": "1.0.0",
        "status": "running",
        "docs_url": "/docs",
        "api_url": "/api"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)