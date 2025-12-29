from pydantic import BaseModel, Field
from datetime import datetime


# =============================
# Confidential Note Schemas
# =============================

class ConfidentialNoteCreate(BaseModel):
    """Schema para crear una nota confidencial"""
    content: str = Field(..., description="Contenido de la nota confidencial")


class EmployeeSimple(BaseModel):
    id: int
    first_name: str
    last_name: str

    class Config:
        from_attributes = True


class ConfidentialNoteResponse(BaseModel):
    """Schema para respuesta de nota confidencial"""
    id: int
    patient_id: int
    clinical_record_id: int
    author_employee_id: int | None
    content: str
    created_at: datetime

    # Relaciones
    author: EmployeeSimple | None = None

    class Config:
        from_attributes = True
