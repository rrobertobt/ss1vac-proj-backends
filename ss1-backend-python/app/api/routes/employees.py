from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import secrets
import string

from app.api.deps import get_db, require_permissions
from app.core.permissions import Permission
from app.core.security import hash_value
from app.db.repositories.employees_repo import EmployeesRepo
from app.db.repositories.users_repo import UsersRepo
from app.services.mail_mailtrap import MailService
from app.api.routes.employees_schemas import EmployeeCreate, EmployeeResponse

router = APIRouter(prefix="/employees", tags=["employees"])


@router.post("", response_model=EmployeeResponse, status_code=201)
async def create_employee(
    employee_data: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permissions(Permission.CREATE_EMPLOYEES)),
):
    """
    Crear un nuevo empleado con su usuario asociado.
    Requiere permiso: CREATE_EMPLOYEES
    """
    users_repo = UsersRepo(db)
    employees_repo = EmployeesRepo(db)

    # Verificar si el email ya existe
    existing_user = await users_repo.find_by_email(employee_data.email)
    if existing_user:
        raise HTTPException(status_code=409, detail="El email ya está registrado")

    # Verificar si el username ya existe (si se proporcionó)
    if employee_data.username:
        existing_username = await users_repo.find_by_username(employee_data.username)
        if existing_username:
            raise HTTPException(status_code=409, detail="El username ya está registrado")

    # Generar contraseña aleatoria
    generated_password = generate_password()
    hashed_password = hash_value(generated_password)

    try:
        # Crear usuario
        user_dict = {
            "email": employee_data.email,
            "username": employee_data.username,
            "password_hash": hashed_password,
            "role_id": employee_data.role_id,
            "is_active": True,
        }
        user = await users_repo.create(user_dict)

        # Crear empleado
        employee_dict = {
            "user_id": user.id,
            "first_name": employee_data.first_name,
            "last_name": employee_data.last_name,
            "employee_type": employee_data.employee_type,
            "license_number": employee_data.license_number,
            "area_id": employee_data.area_id,
            "base_salary": employee_data.base_salary or 0,
            "session_rate": employee_data.session_rate or 0,
            "igss_percentage": employee_data.igss_percentage or 0,
            "hired_at": employee_data.hired_at,
            "status": "ACTIVE",
        }
        employee = await employees_repo.create(employee_dict)

        # Enviar correo con credenciales
        try:
            mail_service = MailService()
            mail_service.send_text_email(
                to=employee_data.email,
                subject="Bienvenido a PsiFirm - Credenciales de Acceso",
                text=f"""Hola {employee_data.first_name},

Tu cuenta de empleado ha sido creada exitosamente en PsiFirm.

Tus credenciales de acceso son:
Email: {employee_data.email}
Contraseña: {generated_password}

Por favor, cambia tu contraseña después de iniciar sesión por primera vez.

Saludos,
Equipo PsiFirm""",
            )
        except Exception as e:
            print(f"Error al enviar correo: {e}")

        return employee

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear empleado: {str(e)}")


def generate_password(length: int = 12) -> str:
    """
    Genera una contraseña aleatoria segura.
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password
