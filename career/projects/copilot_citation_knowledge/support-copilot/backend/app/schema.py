from pydantic import BaseModel, Field
from typing import Optional, List

class DocumentMetadata(BaseModel):
    source_name: str = Field(..., description="Name of the file or URL")
    section_heading: Optional[str] = Field(None, description="Heading under which the chunk falls")
    last_updated: str = Field(..., description="ISO format date string")
    doc_type: str = Field(..., description="e.g., FAQ, API_DOC, POLICY")
    access_level: str = Field(default="public", description="public or internal")

class AssistantResponse(BaseModel):
    answer: str
    citations: List[str]
    confidence_score: float
    unverified_claims: Optional[str]