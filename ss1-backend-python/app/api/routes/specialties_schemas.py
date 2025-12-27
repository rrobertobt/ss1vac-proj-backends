from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SpecialtyCreate(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=120, description="Nombre de la especialidad"
    )
    description: Optional[str] = Field(None, description="Descripción de la especialidad")


class SpecialtyUpdate(BaseModel):
    name: Optional[str] = Field(
        None, min_length=1, max_length=120, description="Nombre de la especialidad"
    )
    description: Optional[str] = Field(None, description="Descripción de la especialidad")


class SpecialtyResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
