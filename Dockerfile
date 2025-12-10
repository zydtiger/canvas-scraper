FROM python:3.13.11-slim-bookworm

# Set the working directory
WORKDIR /app

# Copy the application code
COPY ./ /app/

# Install dependencies
RUN pip install uv
RUN uv sync --frozen --no-dev
RUN uv run playwright install chromium

# Start server
CMD ["/usr/local/bin/uv", "run", "uvicorn", "src.app:app", "--port", "8000"]
