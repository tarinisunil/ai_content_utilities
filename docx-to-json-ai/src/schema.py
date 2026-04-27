from pydantic import BaseModel, Field
from typing import List


class ContentBlock(BaseModel):
    type: str  # "paragraph", "bullet", etc.
    text: str


class Section(BaseModel):
    heading: str = ""
    content: List[ContentBlock] = Field(default_factory=list)
    type: str = "general"


class DocumentSchema(BaseModel):
    title: str = ""
    sections: List[Section] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    notes: List[str] = Field(default_factory=list)