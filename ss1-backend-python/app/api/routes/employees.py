from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import secrets
import string
from datetime import time
from sqlalchemy import text

from app.api.deps import get_db, require_permissions
from app.core.permissions import Permission
from app.core.security import hash_value
from app.db.repositories.employees_repo import EmployeesRepo
from app.db.repositories.users_repo import UsersRepo
from app.services.mail_mailtrap import MailService
from app.api.routes.employees_schemas import EmployeeCreate, EmployeeResponse
from app.db.models import EmployeeAvailability

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

        # Asignar especialidades si se proporcionaron
        if employee_data.specialty_ids:
            for specialty_id in employee_data.specialty_ids:
                await db.execute(
                    text("INSERT INTO employee_specialties (employee_id, specialty_id) VALUES (:emp_id, :spec_id)"),
                    {"emp_id": employee.id, "spec_id": specialty_id}
                )

        # Crear registros de disponibilidad si se proporcionaron
        if employee_data.availability:
            assigned_specialties = employee_data.specialty_ids or []
            
            # Solo validar si hay especialidades asignadas
            if assigned_specialties:
                # Validación 1: Verificar que todos los specialty_ids en availability estén en specialty_ids
                for avail in employee_data.availability:
                    if avail.specialty_id and avail.specialty_id not in assigned_specialties:
                        raise HTTPException(
                            status_code=400,
                            detail=f"La especialidad {avail.specialty_id} en availability no está asignada al empleado"
                        )
                
                # Validación 2: Verificar que specialty_ids usados en availability coincidan con los asignados
                availability_specialty_ids = [
                    avail.specialty_id for avail in employee_data.availability 
                    if avail.specialty_id is not None
                ]
                unique_avail_spec_ids = list(set(availability_specialty_ids))
                
                missing_specialties = [
                    spec_id for spec_id in assigned_specialties 
                    if spec_id not in unique_avail_spec_ids
                ]
                
                if missing_specialties:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Las especialidades {', '.join(map(str, missing_specialties))} están asignadas pero no tienen horarios de disponibilidad"
                    )
            
            # Validación 3: Verificar que no haya traslapes de horarios
            for i, avail1 in enumerate(employee_data.availability):
                start1 = time_to_minutes(avail1.start_time)
                end1 = time_to_minutes(avail1.end_time)
                
                for avail2 in employee_data.availability[i+1:]:
                    # Solo verificar traslapes si es el mismo día y especialidad
                    if (avail1.day_of_week == avail2.day_of_week and 
                        avail1.specialty_id == avail2.specialty_id):
                        start2 = time_to_minutes(avail2.start_time)
                        end2 = time_to_minutes(avail2.end_time)
                        
                        # Verificar traslape: (start1 < end2) && (start2 < end1)
                        if start1 < end2 and start2 < end1:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Conflicto de horarios: {avail1.start_time}-{avail1.end_time} y {avail2.start_time}-{avail2.end_time} se traslapan el día {avail1.day_of_week} para la especialidad {avail1.specialty_id or 'general'}"
                            )

            for avail in employee_data.availability:
                # Convertir string HH:mm a time object
                start_parts = avail.start_time.split(":")
                end_parts = avail.end_time.split(":")
                
                availability = EmployeeAvailability(
                    employee_id=employee.id,
                    day_of_week=avail.day_of_week,
                    start_time=time(int(start_parts[0]), int(start_parts[1])),
                    end_time=time(int(end_parts[0]), int(end_parts[1])),
                    specialty_id=avail.specialty_id,
                    is_active=True,
                )
                db.add(availability)
            
            await db.commit()
            await db.refresh(employee)

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

    except HTTPException:
        # Re-lanzar HTTPExceptions para que mantengan su código de estado
        await db.rollback()
        raise
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


def time_to_minutes(time_str: str) -> int:
    """
    Convierte una hora en formato HH:mm a minutos desde medianoche.
    """
    hours, minutes = map(int, time_str.split(":"))
    return hours * 60 + minutes
