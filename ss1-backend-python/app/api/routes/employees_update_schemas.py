from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Literal, List
from datetime import date
from app.api.routes.employee_availability_schemas import EmployeeAvailabilityDto


class EmployeeUpdate(BaseModel):
    # Datos del usuario
    email: Optional[EmailStr] = Field(None, description="Email del empleado")
    username: Optional[str] = Field(
        None, min_length=3, max_length=100, description="Nombre de usuario"
    )
    role_id: Optional[int] = Field(None, gt=0, description="ID del rol")

    # Datos del empleado
    first_name: Optional[str] = Field(
        None, min_length=2, max_length=100, description="Nombre del empleado"
    )
    last_name: Optional[str] = Field(
        None, min_length=2, max_length=100, description="Apellido del empleado"
    )
    license_number: Optional[str] = Field(
        None, max_length=100, description="Número de licencia profesional"
    )
    area_id: Optional[int] = Field(None, gt=0, description="ID del área")
    base_salary: Optional[float] = Field(
        None, ge=0, le=999999999.99, description="Salario base"
    )
    session_rate: Optional[float] = Field(
        None, ge=0, le=999999999.99, description="Tarifa por sesión"
    )
    igss_percentage: Optional[float] = Field(
        None, ge=0, le=100, description="Porcentaje IGSS (0-100)"
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
    def validate_names(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError("El nombre no puede estar vacío")
        return v.strip() if v else v

    @field_validator("hired_at")
    @classmethod
    def validate_hired_date(cls, v: Optional[date]) -> Optional[date]:
        if v and v > date.today():
            raise ValueError("La fecha de contratación no puede ser futura")
        return v
