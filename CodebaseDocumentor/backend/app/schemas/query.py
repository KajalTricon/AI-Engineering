"""
Query / Q&A schemas
"""

from typing import List

from pydantic import BaseModel


class QueryRequest(BaseModel):

    question: str


class QuerySource(BaseModel):

    module: str

    path: str


class QueryResponse(BaseModel):

    answer: str

    sources: List[QuerySource]