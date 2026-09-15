# API Documentation

FastAPI endpoint specifications and interface contracts for the Handoff backend.

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/api/upload-audio` | Uploads audio for transcription |
| `POST` | `/api/structure-procedure` | Structures raw text into a procedure |
| `POST` | `/api/approve-procedure` | Owner approves and persists a procedure |
| `GET` | `/api/procedures` | Lists all approved procedures |
| `POST` | `/api/query` | Employee submits a plain-language question |
| `GET` | `/api/gaps` | Lists logged documentation gaps |

## Interactive documentation

FastAPI generates live API documentation at:

- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc

Both are available when the backend is running locally.

## Design reference

See `docs/architecture/` for the full System Design Specification, including request/response schemas and interface contracts.
