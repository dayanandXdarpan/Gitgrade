"""
GitGrade API - Main FastAPI Application

The automated GitHub repository grading service.
Evaluates student repositories and provides professional feedback.
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

from src.api.routes import router

# Load environment variables from .env
load_dotenv()

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Create FastAPI application
app = FastAPI(
    title="GitGrade API",
    description="Automated GitHub repository grading for students and developers",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=PROJECT_ROOT / "static"), name="static")

# Include API routes
app.include_router(router)


@app.get("/")
async def root():
    """Serve the main dashboard HTML"""
    return FileResponse(PROJECT_ROOT / "static" / "index.html")


# Entry point for running with uvicorn directly
if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    # In Render and other PaaS, bind to 0.0.0.0 and use the provided $PORT
    uvicorn.run("src.api.main:app", host=os.getenv("HOST", "0.0.0.0"), port=port, reload=True)
