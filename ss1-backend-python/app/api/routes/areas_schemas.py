from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AreaCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120, description="Nombre del área")
    description: Optional[str] = Field(None, description="Descripción del área")


class AreaUpdate(BaseModel):
    name: Optional[str] = Field(
        None, min_length=1, max_length=120, description="Nombre del área"
    )
    description: Optional[str] = Field(None, description="Descripción del área")


class AreaResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
