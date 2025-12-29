from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


# ============================================
# Schemas para Availability
# ============================================
class CheckAvailabilityRequest(BaseModel):
    date: str = Field(..., description="Fecha en formato YYYY-MM-DD")
    specialty_id: Optional[int] = Field(None, ge=1)
    professional_id: Optional[int] = Field(None, ge=1)


class TimeSlot(BaseModel):
    start: str  # ISO 8601 datetime
    end: str    # ISO 8601 datetime
    available: bool


class ProfessionalAvailability(BaseModel):
    employee_id: int
    employee_name: str
    specialty_id: Optional[int]
    specialty_name: Optional[str]
    available_slots: list[TimeSlot]


class AvailabilityResponse(BaseModel):
    date: str
    day_of_week: int
    professionals: list[ProfessionalAvailability]


# ============================================
# Schemas para Appointments
# ============================================
class PatientBasic(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: Optional[str] = None

    class Config:
        from_attributes = True


class ProfessionalBasic(BaseModel):
    id: int
    first_name: str
    last_name: str
    license_number: Optional[str] = None

    class Config:
        from_attributes = True


class SpecialtyBasic(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class AppointmentCreate(BaseModel):
    patient_id: int = Field(..., ge=1)
    professional_id: Optional[int] = Field(None, ge=1)
    specialty_id: Optional[int] = Field(None, ge=1)
    appointment_type: Optional[str] = Field(None, max_length=50)
    start_datetime: str  # ISO 8601 datetime string
    end_datetime: str    # ISO 8601 datetime string
    notes: Optional[str] = None

    @field_validator("start_datetime", "end_datetime")
    @classmethod
    def validate_datetime(cls, v: str) -> str:
        """Validar que sea un datetime válido en formato ISO"""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError("Formato de fecha inválido. Use formato ISO 8601")


class AppointmentUpdate(BaseModel):
    professional_id: Optional[int] = Field(None, ge=1)
    specialty_id: Optional[int] = Field(None, ge=1)
    appointment_type: Optional[str] = Field(None, max_length=50)
    start_datetime: Optional[str] = None
    end_datetime: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("start_datetime", "end_datetime")
    @classmethod
    def validate_datetime(cls, v: Optional[str]) -> Optional[str]:
        """Validar que sea un datetime válido en formato ISO"""
        if v is None:
            return v
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError("Formato de fecha inválido. Use formato ISO 8601")


class AppointmentResponse(BaseModel):
    id: int
    patient_id: int
    professional_id: Optional[int]
    specialty_id: Optional[int]
    appointment_type: Optional[str]
    start_datetime: datetime
    end_datetime: datetime
    status: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    # Relaciones
    patient: Optional[PatientBasic] = None
    professional: Optional[ProfessionalBasic] = None
    specialty: Optional[SpecialtyBasic] = None

    class Config:
        from_attributes = True


class AppointmentListResponse(BaseModel):
    data: list[AppointmentResponse]
    meta: dict
