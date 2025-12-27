from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr = Field(..., description="Email del usuario")
    username: Optional[str] = Field(
        None, min_length=3, max_length=100, description="Nombre de usuario"
    )


class UserCreate(UserBase):
    password: Optional[str] = Field(
        None, min_length=8, max_length=100, description="Contraseña del usuario"
    )
    role_id: int = Field(..., gt=0, description="ID del rol")
    is_active: Optional[bool] = Field(True, description="Estado activo/inactivo")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("El username no puede estar vacío")
        return v.strip() if v else None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, description="Email del usuario")
    username: Optional[str] = Field(
        None, min_length=3, max_length=100, description="Nombre de usuario"
    )
    role_id: Optional[int] = Field(None, gt=0, description="ID del rol")
    is_active: Optional[bool] = Field(None, description="Estado activo/inactivo")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("El username no puede estar vacío")
        return v.strip() if v else None


class UserStatusUpdate(BaseModel):
    is_active: bool


class RoleInfo(BaseModel):
    id: int
    name: str
    label: Optional[str] = None

    class Config:
        from_attributes = True


class EmployeeInfo(BaseModel):
    id: int
    first_name: str
    last_name: str
    employee_type: str

    class Config:
        from_attributes = True


class PatientInfo(BaseModel):
    id: int
    first_name: str
    last_name: str

    class Config:
        from_attributes = True


class UserResponse(UserBase):
    id: int
    role_id: int
    is_active: bool
    role: Optional[RoleInfo] = None
    employee: Optional[EmployeeInfo] = None
    patient: Optional[PatientInfo] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    data: list[UserResponse]
    meta: dict
