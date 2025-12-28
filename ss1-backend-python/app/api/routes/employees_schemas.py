from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Literal, List
from datetime import date
import re
from app.api.routes.employee_availability_schemas import EmployeeAvailabilityDto


class EmployeeCreate(BaseModel):
    # Datos del usuario
    email: EmailStr = Field(..., description="Email del empleado")
    username: Optional[str] = Field(
        None, min_length=3, max_length=100, description="Nombre de usuario"
    )
    role_id: int = Field(..., gt=0, description="ID del rol")

    # Datos del empleado
    first_name: str = Field(
        ..., min_length=2, max_length=100, description="Nombre del empleado"
    )
    last_name: str = Field(
        ..., min_length=2, max_length=100, description="Apellido del empleado"
    )
    employee_type: Literal[
        "PSYCHOLOGIST", "PSYCHIATRIST", "TECHNICIAN", "MAINTENANCE", "ADMIN_STAFF"
    ] = Field(..., description="Tipo de empleado")
    license_number: Optional[str] = Field(
        None, max_length=100, description="Número de licencia profesional"
    )
    area_id: Optional[int] = Field(None, gt=0, description="ID del área")
    base_salary: Optional[float] = Field(
        0, ge=0, le=999999999.99, description="Salario base"
    )
    session_rate: Optional[float] = Field(
        0, ge=0, le=999999999.99, description="Tarifa por sesión"
    )
    igss_percentage: Optional[float] = Field(
        0, ge=0, le=100, description="Porcentaje IGSS (0-100)"
    )
    hired_at: Optional[date] = Field(None, description="Fecha de contratación")
    specialty_ids: Optional[List[int]] = Field(
        None, description="IDs de las especialidades del empleado"
    )
    availability: Optional[List[EmployeeAvailabilityDto]] = Field(
        None, description="Horarios de disponibilidad del empleado"
    )

    @field_validator("specialty_ids")
    @classmethod
    def validate_specialty_ids(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        if v:
            for spec_id in v:
                if spec_id <= 0:
                    raise ValueError("Cada ID de especialidad debe ser mayor a 0")
        return v

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_names(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        return v.strip()

    @field_validator("hired_at")
    @classmethod
    def validate_hired_date(cls, v: Optional[date]) -> Optional[date]:
        if v and v > date.today():
            raise ValueError("La fecha de contratación no puede ser futura")
        return v


class EmployeeResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    first_name: str
    last_name: str
    employee_type: str
    license_number: Optional[str] = None
    area_id: Optional[int] = None
    base_salary: float
    session_rate: float
    igss_percentage: float
    hired_at: Optional[date] = None
    status: str

    class Config:
        from_attributes = True
