# AquaGuard AI backend — Stage 2

The backend is a FastAPI application. In this stage it loads configuration from environment variables, manages a MongoDB client during application startup/shutdown, and exposes health endpoints.

## Important files

- `app/main.py`: constructs the FastAPI application.
- `app/core/config.py`: validates environment variables.
- `app/db/mongodb.py`: owns the MongoDB connection lifecycle.
- `app/api/health.py`: defines health endpoints.
- `app/schemas/health.py`: defines typed health responses.
- `tests/test_health.py`: proves both endpoints work.

All commands in the root README use Windows PowerShell.
