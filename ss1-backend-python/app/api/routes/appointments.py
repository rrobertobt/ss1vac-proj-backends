from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date

from app.db.session import get_db
from app.api.deps import require_permissions, get_current_user
from app.core.permissions import Permission
from app.db.repositories.appointments_repo import AppointmentsRepository
from app.api.routes.appointments_schemas import (
    CheckAvailabilityRequest,
    AvailabilityResponse,
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    AppointmentListResponse,
)

router = APIRouter(prefix="/appointments", tags=["appointments"])


# ============================================
# A) Consultar disponibilidad
# ============================================
@router.get("/availability", response_model=AvailabilityResponse)
async def check_availability(
    date: str = Query(..., description="Fecha en formato YYYY-MM-DD"),
    specialtyId: Optional[int] = Query(None, alias="specialtyId"),
    professionalId: Optional[int] = Query(None, alias="professionalId"),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_permissions(Permission.VIEW_SCHEDULED_APPOINTMENTS)),
):
    """
    Consultar disponibilidad de citas en una fecha específica.
    
    Requiere permiso: VIEW_SCHEDULED_APPOINTMENTS
    Roles permitidos: ADMIN_STAFF, PSYCHOLOGIST, PSYCHIATRIST, SUPER_ADMIN
    """
    try:
        target_date = date.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD")
    
    result = await AppointmentsRepository.check_availability(
        db=db,
        target_date=target_date,
        specialty_id=specialtyId,
        professional_id=professionalId,
    )
    
    return result


# ============================================
# G) Mis citas (para pacientes)
# ============================================
@router.get("/my-appointments", response_model=list[AppointmentResponse])
async def get_my_appointments(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Obtener las citas del paciente actual.
    
    Roles permitidos: PATIENT (solo ve sus propias citas)
    """
    # Verificar que el usuario tenga un paciente asociado
    if not current_user.patient:
        raise HTTPException(
            status_code=403,
            detail="Usuario no está asociado a un paciente"
        )
    
    appointments = await AppointmentsRepository.find_by_patient_id(
        db=db,
        patient_id=current_user.patient.id
    )
    
    return appointments


# ============================================
# H) Mis citas profesionales (para psicólogos/psiquiatras)
# ============================================
@router.get("/my-professional-appointments", response_model=list[AppointmentResponse])
async def get_my_professional_appointments(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Obtener las citas del profesional actual (psicólogo/psiquiatra).
    
    Roles permitidos: PSYCHOLOGIST, PSYCHIATRIST (solo ven sus citas asignadas)
    """
    # Verificar que el usuario tenga un empleado asociado
    if not current_user.employee:
        raise HTTPException(
            status_code=403,
            detail="Usuario no está asociado a un empleado"
        )
    
    appointments = await AppointmentsRepository.find_by_professional_id(
        db=db,
        professional_id=current_user.employee.id
    )
    
    return appointments


# ============================================
# B) Crear cita
# ============================================
@router.post("", response_model=AppointmentResponse, status_code=201)
async def create_appointment(
    appointment: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_permissions(Permission.CREATE_APPOINTMENTS)),
):
    """
    Crear una nueva cita.
    
    Requiere permiso: CREATE_APPOINTMENTS
    Roles permitidos: ADMIN_STAFF, SUPER_ADMIN
    """
    try:
        new_appointment = await AppointmentsRepository.create(
            db=db,
            appointment_data=appointment.model_dump()
        )
        return new_appointment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================
# C) Listar citas
# ============================================
@router.get("", response_model=AppointmentListResponse)
async def list_appointments(
    from_date: Optional[str] = Query(None, alias="from", description="Fecha inicio YYYY-MM-DD"),
    to_date: Optional[str] = Query(None, alias="to", description="Fecha fin YYYY-MM-DD"),
    professionalId: Optional[int] = Query(None, alias="professionalId"),
    patientId: Optional[int] = Query(None, alias="patientId"),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_permissions(Permission.VIEW_SCHEDULED_APPOINTMENTS)),
):
    """
    Listar citas con filtros y paginación.
    
    Requiere permiso: VIEW_SCHEDULED_APPOINTMENTS
    Roles permitidos: ADMIN_STAFF, PSYCHOLOGIST, PSYCHIATRIST, SUPER_ADMIN
    
    Nota: Si deseas que los profesionales solo vean sus propias citas,
    implementa lógica adicional basada en el rol del usuario.
    """
    result = await AppointmentsRepository.find_all(
        db=db,
        from_date=from_date,
        to_date=to_date,
        professional_id=professionalId,
        patient_id=patientId,
        status=status,
        page=page,
        limit=limit,
    )
    
    return result


# ============================================
# Detalle de una cita
# ============================================
@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_permissions(Permission.VIEW_SCHEDULED_APPOINTMENTS)),
):
    """
    Obtener detalle de una cita específica.
    
    Requiere permiso: VIEW_SCHEDULED_APPOINTMENTS
    """
    appointment = await AppointmentsRepository.find_by_id(db, appointment_id)
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    return appointment


# ============================================
# D) Reprogramar/editar cita
# ============================================
@router.patch("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: int,
    appointment_data: AppointmentUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_permissions(Permission.EDIT_APPOINTMENTS)),
):
    """
    Reprogramar o editar una cita existente.
    
    Requiere permiso: EDIT_APPOINTMENTS
    Roles permitidos: ADMIN_STAFF, SUPER_ADMIN
    """
    try:
        # Filtrar campos no establecidos
        update_dict = appointment_data.model_dump(exclude_unset=True)
        
        updated_appointment = await AppointmentsRepository.update(
            db=db,
            appointment_id=appointment_id,
            update_data=update_dict
        )
        
        return updated_appointment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================
# E) Cancelar cita
# ============================================
@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
async def cancel_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_permissions(Permission.CANCEL_APPOINTMENTS)),
):
    """
    Cancelar una cita.
    
    Requiere permiso: CANCEL_APPOINTMENTS
    Roles permitidos: ADMIN_STAFF, SUPER_ADMIN
    """
    try:
        cancelled_appointment = await AppointmentsRepository.cancel(
            db=db,
            appointment_id=appointment_id
        )
        return cancelled_appointment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================
# F) Marcar como atendida/completada
# ============================================
@router.post("/{appointment_id}/complete", response_model=AppointmentResponse)
async def complete_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_permissions(Permission.EDIT_APPOINTMENTS)),
):
    """
    Marcar una cita como atendida/completada.
    
    Requiere permiso: EDIT_APPOINTMENTS
    Roles permitidos: PSYCHOLOGIST, PSYCHIATRIST, SUPER_ADMIN
    """
    try:
        completed_appointment = await AppointmentsRepository.complete(
            db=db,
            appointment_id=appointment_id
        )
        return completed_appointment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
