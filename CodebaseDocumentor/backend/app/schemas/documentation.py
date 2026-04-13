"""
Documentation schemas
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class DocumentationResponse(BaseModel):
    project_id: str
    url: str
    created_at: datetime
    markdown: Optional[str] = None
    content: Optional[dict[str, Any]] = None
