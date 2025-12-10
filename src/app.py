from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from .robots import AnnouncementScraper, AssignmentScraper
from .models import ScrapeException

app = FastAPI(
    title="Canvas Scraper API",
    description="API for scraping Canvas announcements and assignments",
    version="1.0.0",
)

# Security scheme for Bearer token authentication
security = HTTPBearer()


def extract_session_from_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Extract Canvas session token from Authorization header.

    Args:
        credentials: Bearer token credentials

    Returns:
        Canvas session token string

    Raises:
        HTTPException: If authorization is invalid
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail="Canvas session token required in Authorization header",
        )
    return credentials.credentials


@app.get("/announcements")
async def get_announcements(session: str = Depends(extract_session_from_auth)):
    """
    Scrape Canvas announcements for a given session.

    Args:
        session: Canvas session token (extracted from Authorization header)

    Returns:
        JSON response with list of announcements or error message
    """
    try:
        scraper = AnnouncementScraper(session)
        announcements = await scraper.scrape()

        # Convert Pydantic models to dictionaries for JSON response
        return [announcement.model_dump() for announcement in announcements]

    except ScrapeException as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"error": f"Unexpected error: {str(e)}"}
        )


@app.get("/assignments")
async def get_assignments(session: str = Depends(extract_session_from_auth)):
    """
    Scrape Canvas assignments for a given session.

    Args:
        session: Canvas session token (extracted from Authorization header)

    Returns:
        JSON response with list of assignments or error message
    """
    try:
        scraper = AssignmentScraper(session)
        assignments = await scraper.scrape()

        # Convert Pydantic models to dictionaries for JSON response
        return [assignment.model_dump() for assignment in assignments]

    except ScrapeException as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"error": f"Unexpected error: {str(e)}"}
        )


@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "Canvas Scraper API",
        "version": "1.0.0",
        "running": True,
        "security": "Bearer token authentication required",
        "endpoints": {
            "announcements": "/announcements (Authorization: Bearer <session_token>)",
            "assignments": "/assignments (Authorization: Bearer <session_token>)",
        },
        "usage_example": {
            "headers": {"Authorization": "Bearer your_canvas_session_token_here"}
        },
    }
