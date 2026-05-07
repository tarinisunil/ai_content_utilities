from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field


class ContentBlock(BaseModel):
    type: str = "paragraph"   # "paragraph", "bullet", "table"
    text: str = ""
    rows: List[List[str]] = Field(default_factory=list)
    headers: List[str] = Field(default_factory=list)
    source: str = ""


class ContentBlock(BaseModel):
    type: str  # "paragraph", "bullet", etc.
    text: str


class Section(BaseModel):
    heading: str = ""
    level: int = 1
    type: str = "general"
    content: List[ContentBlock] = Field(default_factory=list)
    children: List["Section"] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    notes: List[str] = Field(default_factory=list)


class DocumentSchema(BaseModel):
    title: str = ""
    sections: List[Section] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    notes: List[str] = Field(default_factory=list)
    summary: str = ""
    document_type: str = "unknown"


Section.model_rebuild()