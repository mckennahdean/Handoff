# Handoff backend: the FastAPI app served by uvicorn.
# Build from the repo root:
#   docker build -f backend/Dockerfile -t handoff-backend .

FROM python:3.13-slim
LABEL org.opencontainers.image.source="https://github.com/mckennahdean/Handoff" \
      org.opencontainers.image.description="Handoff backend: FastAPI API with grounded Q&A"

# Print logs immediately instead of buffering them, and skip .pyc files.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Dependencies first: Docker caches this layer, so rebuilding after
# a code change skips the slow pip install entirely.
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Then the application code.
COPY backend/ backend/

# Run as a regular user instead of root.
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

# Create or update tables (idempotent), then start the API.
# "exec" hands the process to uvicorn so it receives stop signals.
CMD ["sh", "-c", "python -m backend.create_tables && exec uvicorn backend.main:app --host 0.0.0.0 --port 8000"]