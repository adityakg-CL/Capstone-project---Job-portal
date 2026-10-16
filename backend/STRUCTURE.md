# Backend layout

- `main.py` creates the FastAPI application and lifecycle.
- `server.py` is a convenience development launcher.
- `config/` contains environment-backed settings.
- `controllers/` contains HTTP endpoint implementations.
- `middleware/` contains authentication and authorization helpers.
- `models/` contains MongoDB access and Pydantic request/response schemas.
- `routes/` registers the API controllers.
- `services/` contains business services.
- `utils/` contains shared serialization, audit, notification, and time helpers.
