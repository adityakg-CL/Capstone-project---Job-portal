import asyncio
import json
import os

os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret-that-is-not-used-for-signing")

from fastapi import Request
from pymongo.errors import PyMongoError

from main import app, handle_database_error


def test_mongodb_errors_return_service_unavailable_without_internal_details(caplog):
    request = Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/api/v1/auth/login",
            "raw_path": b"/api/v1/auth/login",
            "query_string": b"",
            "headers": [],
            "server": ("testserver", 80),
            "client": ("testclient", 1),
            "root_path": "",
        }
    )
    error = PyMongoError("private database detail")

    response = asyncio.run(handle_database_error(request, error))

    assert response.status_code == 503
    assert json.loads(response.body) == {"detail": "Database is temporarily unavailable"}
    assert "private database detail" in caplog.text
    assert app.exception_handlers[PyMongoError] is handle_database_error
