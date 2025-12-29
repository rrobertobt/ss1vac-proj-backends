from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


# =============================
# Patient Task Schemas
# =============================

class PatientTaskBase(BaseModel):
    title: str = Field(..., max_length=200, description="Título de la tarea")
    description: Optional[str] = Field(None, description="Descripción detallada")
    due_date: Optional[date] = Field(None, description="Fecha de vencimiento")
    clinical_record_id: Optional[int] = Field(None, description="ID de historia clínica asociada")


class PatientTaskCreate(PatientTaskBase):
    """Schema para crear una tarea de paciente"""
    ...


class PatientTaskUpdate(BaseModel):
    """Schema para actualizar una tarea de paciente"""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[str] = Field(None, description="Estado: PENDING, COMPLETED, CANCELLED")


class EmployeeSimple(BaseModel):
    id: int
    first_name: str
    last_name: str

    class Config:
        from_attributes = True


class PatientTaskResponse(BaseModel):
    """Schema para respuesta de tarea de paciente"""
    id: int
    patient_id: int
    clinical_record_id: Optional[int] = None
    assigned_by_employee_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: str
    created_at: datetime
    updated_at: datetime

    # Relaciones
    assigned_by: Optional[EmployeeSimple] = None

    class Config:
        from_attributes = True
