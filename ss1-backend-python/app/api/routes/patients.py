from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets
import string

from app.api.deps import get_db, require_permissions
from app.core.permissions import Permission
from app.core.security import hash_value
from app.db.repositories.patients_repo import PatientsRepo
from app.db.repositories.users_repo import UsersRepo
from app.db.models import Role
from app.services.mail_mailtrap import MailService
from app.api.routes.patients_schemas import PatientCreate, PatientResponse

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
