from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Literal
from datetime import date
import re


class PatientCreate(BaseModel):
    # Datos del usuario (opcional - puede no tener acceso al sistema)
    email: Optional[EmailStr] = Field(None, description="Email para acceso al sistema")
    username: Optional[str] = Field(
        None, min_length=3, max_length=100, description="Nombre de usuario"
    )

    # Datos del paciente
    first_name: str = Field(
        ..., min_length=2, max_length=100, description="Nombre del paciente"
    )
    last_name: str = Field(
        ..., min_length=2, max_length=100, description="Apellido del paciente"
    )
    dob: Optional[date] = Field(None, description="Fecha de nacimiento")
    gender: Optional[Literal["MALE", "FEMALE", "OTHER"]] = Field(
        None, description="Género del paciente"
    )
    marital_status: Optional[
        Literal["SINGLE", "MARRIED", "DIVORCED", "WIDOWED", "DOMESTIC_PARTNERSHIP"]
    ] = Field(None, description="Estado civil")
    occupation: Optional[str] = Field(
        None, max_length=120, description="Ocupación del paciente"
    )
    education_level: Optional[str] = Field(
        None, max_length=120, description="Nivel educativo"
    )
    address: Optional[str] = Field(None, max_length=500, description="Dirección")
    phone: Optional[str] = Field(None, max_length=50, description="Teléfono de contacto")
    patient_email: Optional[str] = Field(
        None, max_length=150, description="Email del paciente (no para login)"
    )
    emergency_contact_name: Optional[str] = Field(
        None, max_length=150, description="Nombre del contacto de emergencia"
    )
    emergency_contact_relationship: Optional[str] = Field(
        None, max_length=80, description="Relación con el contacto de emergencia"
    )
    emergency_contact_phone: Optional[str] = Field(
        None, max_length=50, description="Teléfono del contacto de emergencia"
    )

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_names(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        return v.strip()

    @field_validator("dob")
    @classmethod
    def validate_dob(cls, v: Optional[date]) -> Optional[date]:
        if v and v > date.today():
            raise ValueError("La fecha de nacimiento no puede ser futura")
        if v and v.year < 1900:
            raise ValueError("La fecha de nacimiento no es válida")
        return v

    @field_validator("phone", "emergency_contact_phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Validación de formato de teléfono
        phone_pattern = r"^[+]?[(]?[0-9]{1,4}[)]?[-\s.]?[(]?[0-9]{1,4}[)]?[-\s.]?[0-9]{1,9}$"
        if not re.match(phone_pattern, v):
            raise ValueError("El teléfono debe tener un formato válido")
        return v

    @field_validator("patient_email")
    @classmethod
    def validate_patient_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Validación básica de email
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, v):
            raise ValueError("El email del paciente debe ser válido")
        return v


class PatientResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    first_name: str
    last_name: str
    dob: Optional[date] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    occupation: Optional[str] = None
    education_level: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class PatientUpdate(BaseModel):
    dob: Optional[date] = Field(None, description="Fecha de nacimiento")
    gender: Optional[Literal["MALE", "FEMALE", "OTHER"]] = Field(
        None, description="Género del paciente"
    )
    marital_status: Optional[
        Literal["SINGLE", "MARRIED", "DIVORCED", "WIDOWED", "DOMESTIC_PARTNERSHIP"]
    ] = Field(None, description="Estado civil")
    occupation: Optional[str] = Field(
        None, max_length=120, description="Ocupación del paciente"
    )
    education_level: Optional[str] = Field(
        None, max_length=120, description="Nivel educativo"
    )
    address: Optional[str] = Field(None, max_length=500, description="Dirección")
    phone: Optional[str] = Field(None, max_length=50, description="Teléfono de contacto")
    email: Optional[str] = Field(
        None, max_length=150, description="Email del paciente"
    )
    emergency_contact_name: Optional[str] = Field(
        None, max_length=150, description="Nombre del contacto de emergencia"
    )
    emergency_contact_relationship: Optional[str] = Field(
        None, max_length=80, description="Relación con el contacto de emergencia"
    )
    emergency_contact_phone: Optional[str] = Field(
        None, max_length=50, description="Teléfono del contacto de emergencia"
    )

    @field_validator("dob")
    @classmethod
    def validate_dob(cls, v: Optional[date]) -> Optional[date]:
        if v and v > date.today():
            raise ValueError("La fecha de nacimiento no puede ser futura")
        if v and v.year < 1900:
            raise ValueError("La fecha de nacimiento no es válida")
        return v

    @field_validator("phone", "emergency_contact_phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Validación de formato de teléfono
        phone_pattern = r"^[+]?[(]?[0-9]{1,4}[)]?[-\s.]?[(]?[0-9]{1,4}[)]?[-\s.]?[0-9]{1,9}$"
        if not re.match(phone_pattern, v):
            raise ValueError("El teléfono debe tener un formato válido")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Validación básica de email
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, v):
            raise ValueError("El email del paciente debe ser válido")
        return v


class PatientListResponse(BaseModel):
    data: list[PatientResponse]
    meta: dict

