# Canvas Scraper

A FastAPI service that scrapes Canvas LMS for announcements and assignments using Playwright browser automation.

## Quick Start

```bash
# Install dependencies
pip install uv
uv sync
uv run playwright install chromium

# Run the server
uv run uvicorn src.app:app --reload
```

## API Usage

```bash
# Get announcements (replace with your Canvas session token)
curl -H "Authorization: Bearer your_token" http://localhost:8000/announcements

# Get assignments
curl -H "Authorization: Bearer your_token" http://localhost:8000/assignments
```

## Project Structure

```
src/
├── app.py                      # FastAPI endpoints
├── models.py                   # Pydantic models
└── robots/
    ├── base_scraper.py         # Base scraper class
    ├── announcements_scraper.py  # Announcements scraper
    └── assignments_scraper.py     # Assignments scraper
```

## Docker

```bash
docker-compose up --build
```

## Configuration

Currently configured for `jhu.instructure.com`. Modify the domain in `src/robots/base_scraper.py` for other Canvas instances.