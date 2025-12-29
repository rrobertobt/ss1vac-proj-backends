from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date, datetime


# =============================
# Clinical Record Schemas
# =============================

class ClinicalRecordBase(BaseModel):
    patient_id: int = Field(..., description="ID del paciente")
    record_number: Optional[str] = Field(None, max_length=50, description="Número de historia clínica")
    institution_name: Optional[str] = Field(None, max_length=150, description="Nombre de la institución")
    service: Optional[str] = Field(None, max_length=120, description="Servicio (ej. Psicología clínica)")
    opening_date: Optional[date] = Field(None, description="Fecha de apertura")
    responsible_employee_id: Optional[int] = Field(None, description="ID del empleado responsable")
    responsible_license: Optional[str] = Field(None, max_length=100, description="Licencia del responsable")
    referral_source: Optional[str] = Field(None, max_length=150, description="Fuente de referencia")
    chief_complaint: Optional[str] = Field(None, description="Motivo de consulta")


class ClinicalRecordCreate(ClinicalRecordBase):
    """Schema para crear una historia clínica"""
    ...  # pylint: disable=unnecessary-pass


class ClinicalRecordUpdate(BaseModel):
    """Schema para actualizar una historia clínica"""
    record_number: Optional[str] = Field(None, max_length=50)
    institution_name: Optional[str] = Field(None, max_length=150)
    service: Optional[str] = Field(None, max_length=120)
    opening_date: Optional[date] = None
    responsible_employee_id: Optional[int] = None
    responsible_license: Optional[str] = Field(None, max_length=100)
    referral_source: Optional[str] = Field(None, max_length=150)
    chief_complaint: Optional[str] = None
    status: Optional[str] = Field(None, description="Estado: ACTIVE o CLOSED")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v is not None and v not in ['ACTIVE', 'CLOSED']:
            raise ValueError('El estado debe ser ACTIVE o CLOSED')
        return v


# Schemas simplificados para relaciones
class PatientSimple(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class EmployeeSimple(BaseModel):
    id: int
    first_name: str
    last_name: str
    license_number: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class ClinicalRecordResponse(BaseModel):
    """Schema para respuesta de historia clínica"""
    id: int
    patient_id: int
    record_number: Optional[str] = None
    institution_name: Optional[str] = None
    service: Optional[str] = None
    opening_date: Optional[date] = None
    responsible_employee_id: Optional[int] = None
    responsible_license: Optional[str] = None
    referral_source: Optional[str] = None
    chief_complaint: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    # Relaciones
    patient: Optional[PatientSimple] = None
    responsible_employee: Optional[EmployeeSimple] = None

    class Config:
        from_attributes = True


class PaginationMeta(BaseModel):
    """Schema para metadatos de paginación"""
    total: int
    page: int
    limit: int
    totalPages: int


class ClinicalRecordListResponse(BaseModel):
    """Schema para lista paginada de historias clínicas"""
    data: list[ClinicalRecordResponse]
    meta: PaginationMeta
