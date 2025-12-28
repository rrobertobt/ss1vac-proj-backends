from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re
from datetime import time


class EmployeeAvailabilityDto(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6, description="Día de la semana (0=Domingo, 6=Sábado)")
    start_time: str = Field(..., description="Hora de inicio en formato HH:mm (ej: 09:00)")
    end_time: str = Field(..., description="Hora de fin en formato HH:mm (ej: 17:00)")
    specialty_id: Optional[int] = Field(None, gt=0, description="ID de la especialidad (opcional)")

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """Valida que el formato de hora sea HH:mm"""
        if not re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", v):
            raise ValueError("La hora debe tener el formato HH:mm (ej: 09:00)")
        return v

    @field_validator("end_time")
    @classmethod
    def validate_time_range(cls, v: str, info) -> str:
        """Valida que end_time sea mayor que start_time"""
        start_time = info.data.get("start_time")
        if start_time:
            start_parts = start_time.split(":")
            end_parts = v.split(":")
            start_minutes = int(start_parts[0]) * 60 + int(start_parts[1])
            end_minutes = int(end_parts[0]) * 60 + int(end_parts[1])
            
            if end_minutes <= start_minutes:
                raise ValueError("La hora de fin debe ser mayor que la hora de inicio")
        return v


class EmployeeAvailabilityResponse(BaseModel):
    id: int
    employee_id: int
    day_of_week: int
    start_time: time
    end_time: time
    specialty_id: Optional[int] = None
    is_active: bool

    class Config:
        from_attributes = True
