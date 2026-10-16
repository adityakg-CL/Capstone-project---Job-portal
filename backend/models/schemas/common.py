from pydantic import BaseModel, Field
from typing import Any

class Message(BaseModel):
    message: str

class Page(BaseModel):
    items: list[dict[str, Any]]
    page: int
    page_size: int
    total: int
