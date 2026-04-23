from pydantic import BaseModel, Field
from typing import List


class Section(BaseModel):
    heading: str = ""
    content: str = ""
    bullets: List[str] = Field(default_factory=list)


class DocumentSchema(BaseModel):
    title: str = ""
    sections: List[Section] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    notes: List[str] = Field(default_factory=list)