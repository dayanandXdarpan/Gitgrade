"""
API Routes for GitGrade

Defines all HTTP endpoints for the grading service.
Now supports: Analysis Modes (fast/deep) and Viewer Personas
"""

import traceback
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.core.schemas import GradeRequest, GradeReport
from src.core.orchestrator import grade_repository
from src.core.personas import PERSONAS, ANALYSIS_MODES, get_all_personas


router = APIRouter(prefix="/api/v1", tags=["grading"])


@router.post("/grade", response_model=GradeReport)
async def grade_repo(request: GradeRequest):
    """
    Grade a GitHub repository.
    
    Accepts a GitHub URL and returns a comprehensive grading report including:
    - Score (0-100)
    - Skill level (Beginner/Intermediate/Advanced)
    - Summary and critique
    - Resume bullet points
    - Personalized improvement roadmap
    - File health diagram
    - Asset gallery
    - Deployment status
    
    Advanced Options:
    - mode: "fast" (30s) or "deep" (2-5min full analysis)
    - persona: "recruiter", "mentor", "bug_hunter", or "gsoc_admin"
    
    Example:
        POST /api/v1/grade
        {
            "repo_url": "https://github.com/user/repo",
            "deployed_link": "https://myapp.vercel.app",
            "mode": "fast",
            "persona": "mentor"
        }
    """
    try:
        print(f"📥 Grading request: {request.repo_url} (mode={request.mode}, persona={request.persona})")
        
        report = await grade_repository(
            request.repo_url, 
            request.deployed_link,
            mode=request.mode,
            persona=request.persona
        )
        
        print(f"✅ Grading complete: score={report.score}")
        return report
    
    except ValueError as e:
        # Invalid URL or parsing error
        print(f"❌ ValueError: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except FileNotFoundError as e:
        # System prompt not found
        print(f"❌ FileNotFoundError: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration error: {e}")
    
    except RuntimeError as e:
        # LLM API error
        print(f"❌ RuntimeError: {e}")
        raise HTTPException(status_code=502, detail=f"AI service error: {e}")
    
    except Exception as e:
        # Unexpected error - log full traceback
        print(f"❌ Unexpected error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/personas")
async def get_personas():
    """Get available personas for analysis."""
    return {
        "personas": get_all_personas(),
        "modes": {
            mode_id: {
                "name": mode["name"],
                "icon": mode["icon"],
                "description": mode["description"]
            }
            for mode_id, mode in ANALYSIS_MODES.items()
        }
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "GitGrade API"}
