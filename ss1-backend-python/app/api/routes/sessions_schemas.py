from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# =============================
# Session Schemas
# =============================

class SessionBase(BaseModel):
    session_datetime: datetime = Field(..., description="Fecha y hora de la sesión")
    professional_id: Optional[int] = Field(None, description="ID del profesional")
    session_number: Optional[int] = Field(None, description="Número de sesión")
    attended: Optional[bool] = Field(True, description="Asistió el paciente")
    absence_reason: Optional[str] = Field(None, description="Razón de inasistencia")
    topics: Optional[str] = Field(None, description="Temas tratados")
    interventions: Optional[str] = Field(None, description="Intervenciones realizadas")
    patient_response: Optional[str] = Field(None, description="Respuesta del paciente")
    assigned_tasks: Optional[str] = Field(None, description="Tareas asignadas")
    observations: Optional[str] = Field(None, description="Observaciones")
    next_appointment_datetime: Optional[datetime] = Field(None, description="Próxima cita")
    appointment_id: Optional[int] = Field(None, description="ID de cita relacionada")


class SessionCreate(SessionBase):
    """Schema para crear una sesión"""
    ...


class SessionUpdate(BaseModel):
    """Schema para actualizar una sesión"""
    session_datetime: Optional[datetime] = None
    professional_id: Optional[int] = None
    session_number: Optional[int] = None
    attended: Optional[bool] = None
    absence_reason: Optional[str] = None
    topics: Optional[str] = None
    interventions: Optional[str] = None
    patient_response: Optional[str] = None
    assigned_tasks: Optional[str] = None
    observations: Optional[str] = None
    next_appointment_datetime: Optional[datetime] = None
    digital_signature_path: Optional[str] = None
    appointment_id: Optional[int] = None


class EmployeeSimple(BaseModel):
    id: int
    first_name: str
    last_name: str
    license_number: Optional[str] = None

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    """Schema para respuesta de sesión"""
    id: int
    clinical_record_id: int
    professional_id: int | None
    session_datetime: datetime
    session_number: int | None
    attended: bool
    absence_reason: str | None
    topics: str | None
    interventions: str | None
    patient_response: str | None
    assigned_tasks: str | None
    observations: str | None
    next_appointment_datetime: datetime | None
    digital_signature_path: str | None
    appointment_id: int | None
    created_at: datetime
    updated_at: datetime

    # Relaciones
    professional: EmployeeSimple | None = None

    class Config:
        from_attributes = True
