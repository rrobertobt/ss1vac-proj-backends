from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets
import string
import math
from typing import Optional

from app.api.deps import get_db, require_permissions
from app.core.permissions import Permission
from app.core.security import hash_value
from app.db.repositories.patients_repo import PatientsRepo
from app.db.repositories.users_repo import UsersRepo
from app.db.models import Role
from app.services.mail_mailtrap import MailService
from app.api.routes.patients_schemas import (
    PatientCreate,
    PatientResponse,
    PatientUpdate,
    PatientListResponse,
)

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("", response_model=PatientResponse, status_code=201)
async def create_patient(
    patient_data: PatientCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permissions(Permission.CREATE_PATIENTS)),
):
    """
    Crear un nuevo paciente con su usuario asociado (opcional).
    Requiere permiso: CREATE_PATIENTS
    """
    users_repo = UsersRepo(db)
    patients_repo = PatientsRepo(db)

    user_id = None

    # Si se proporciona email, crear usuario con rol de paciente
    if patient_data.email:
        # Verificar si el email ya existe
        existing_user = await users_repo.find_by_email(patient_data.email)
        if existing_user:
            raise HTTPException(status_code=409, detail="El email ya está registrado")

        # Verificar si el username ya existe (si se proporcionó)
        if patient_data.username:
            existing_username = await users_repo.find_by_username(patient_data.username)
            if existing_username:
                raise HTTPException(status_code=409, detail="El username ya está registrado")

        # Buscar el rol de PATIENT
        result = await db.execute(select(Role).where(Role.name == "PATIENT"))
        patient_role = result.scalar_one_or_none()

        if not patient_role:
            raise HTTPException(status_code=500, detail="Rol de PATIENT no encontrado en el sistema")

        # Generar contraseña aleatoria
        generated_password = generate_password()
        hashed_password = hash_value(generated_password)

        try:
            # Crear usuario
            user_dict = {
                "email": patient_data.email,
                "username": patient_data.username,
                "password_hash": hashed_password,
                "role_id": patient_role.id,
                "is_active": True,
            }
            user = await users_repo.create(user_dict)
            user_id = user.id

            # Enviar correo con credenciales
            try:
                mail_service = MailService()
                mail_service.send_text_email(
                    to=patient_data.email,
                    subject="Bienvenido a PsiFirm - Portal de Pacientes",
                    text=f"""Hola {patient_data.first_name},

Tu cuenta de paciente ha sido creada exitosamente en PsiFirm.

Tus credenciales de acceso son:
Email: {patient_data.email}
Contraseña: {generated_password}

Puedes acceder al portal de pacientes para ver tu información y citas.

Por favor, cambia tu contraseña después de iniciar sesión por primera vez.

Saludos,
Equipo PsiFirm""",
                )
            except Exception as e:
                print(f"Error al enviar correo: {e}")

        except HTTPException:
            # Re-lanzar HTTPExceptions para que mantengan su código de estado
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al crear usuario: {str(e)}")

    # Crear paciente
    try:
        patient_dict = {
            "user_id": user_id,
            "first_name": patient_data.first_name,
            "last_name": patient_data.last_name,
            "dob": patient_data.dob,
            "gender": patient_data.gender,
            "marital_status": patient_data.marital_status,
            "occupation": patient_data.occupation,
            "education_level": patient_data.education_level,
            "address": patient_data.address,
            "phone": patient_data.phone,
            "email": patient_data.patient_email or patient_data.email,
            "emergency_contact_name": patient_data.emergency_contact_name,
            "emergency_contact_relationship": patient_data.emergency_contact_relationship,
            "emergency_contact_phone": patient_data.emergency_contact_phone,
            "status": "ACTIVE",
        }
        patient = await patients_repo.create(patient_dict)

        return patient

    except HTTPException:
        # Re-lanzar HTTPExceptions para que mantengan su código de estado
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear paciente: {str(e)}")


def generate_password(length: int = 12) -> str:
    """
    Genera una contraseña aleatoria segura.
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


@router.get("", response_model=PatientListResponse)
async def get_patients(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permissions(Permission.VIEW_PATIENTS)),
):
    """
    Listar y buscar pacientes con paginación.
    Requiere permiso: VIEW_PATIENTS
    """
    patients_repo = PatientsRepo(db)
    
    patients, total = await patients_repo.find_all(
        search=search,
        status=status,
        page=page,
        limit=limit,
    )

    return {
        "data": patients,
        "meta": {
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": math.ceil(total / limit) if total > 0 else 0,
        },
    }


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permissions(Permission.VIEW_PATIENTS)),
):
    """
    Obtener detalle de un paciente por ID.
    Requiere permiso: VIEW_PATIENTS
    """
    patients_repo = PatientsRepo(db)
    
    patient = await patients_repo.find_by_id(patient_id)
    
    if not patient:
        raise HTTPException(status_code=404, detail=f"Paciente con ID {patient_id} no encontrado")
    
    return patient


@router.patch("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    patient_data: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permissions(Permission.EDIT_PATIENTS)),
):
    """
    Actualizar datos administrativos de un paciente.
    Requiere permiso: EDIT_PATIENTS
    """
    patients_repo = PatientsRepo(db)
    
    # Verificar que el paciente existe
    existing_patient = await patients_repo.find_by_id(patient_id)
    if not existing_patient:
        raise HTTPException(status_code=404, detail=f"Paciente con ID {patient_id} no encontrado")
    
    # Actualizar solo los campos proporcionados
    update_dict = patient_data.model_dump(exclude_unset=True)
    
    try:
        updated_patient = await patients_repo.update(patient_id, update_dict)
        return updated_patient
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar paciente: {str(e)}")

