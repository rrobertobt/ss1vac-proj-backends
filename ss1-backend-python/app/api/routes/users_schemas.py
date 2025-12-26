from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    role_id: int
    is_active: Optional[bool] = True


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None


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
