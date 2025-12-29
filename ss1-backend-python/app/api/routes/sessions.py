from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, require_permissions
from app.core.permissions import Permission
from app.db.models import Session, ClinicalRecord, Employee
from app.api.routes.sessions_schemas import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
)

router = APIRouter(tags=["sessions"])


@router.post("/clinical-records/{clinical_record_id}/sessions", response_model=SessionResponse, status_code=201)
async def create_session(
    clinical_record_id: int,
    session_data: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permissions(Permission.CREATE_SESSIONS)),
):
    """
    Crear una sesión / nota de progreso en una historia clínica.
    Requiere permiso: CREATE_SESSIONS
    Roles: PSYCHOLOGIST, PSYCHIATRIST
    """
    
    # Verificar que la historia clínica existe
    result = await db.execute(
        select(ClinicalRecord).where(ClinicalRecord.id == clinical_record_id)
    )
    clinical_record = result.scalar_one_or_none()
    
    if not clinical_record:
        raise HTTPException(
            status_code=404,
            detail=f"Historia clínica con ID {clinical_record_id} no encontrada"
        )
    
    # Verificar que la historia clínica esté activa
    if clinical_record.status != "ACTIVE":
        raise HTTPException(
            status_code=400,
            detail="No se puede agregar sesión a una historia clínica cerrada"
        )
    
    # Verificar profesional si se proporciona
    if session_data.professional_id:
        result = await db.execute(
            select(Employee).where(Employee.id == session_data.professional_id)
        )
        professional = result.unique().scalar_one_or_none()
        
        if not professional:
            raise HTTPException(
                status_code=404,
                detail=f"Profesional con ID {session_data.professional_id} no encontrado"
            )
        
        if professional.status != "ACTIVE":
            raise HTTPException(
                status_code=400,
                detail="No se puede asignar un profesional inactivo"
            )
    
    # Usar el professional_id del usuario actual si no se proporciona
    professional_id = session_data.professional_id
    if not professional_id:
        professional_id = getattr(current_user, 'employee_id', None) if hasattr(current_user, 'employee_id') else None
    
    # Crear la sesión
    new_session = Session(
        clinical_record_id=clinical_record_id,
        professional_id=professional_id,
        session_datetime=session_data.session_datetime,
        session_number=session_data.session_number,
        attended=session_data.attended if session_data.attended is not None else True,
        absence_reason=session_data.absence_reason,
        topics=session_data.topics,
        interventions=session_data.interventions,
        patient_response=session_data.patient_response,
        assigned_tasks=session_data.assigned_tasks,
        observations=session_data.observations,
        next_appointment_datetime=session_data.next_appointment_datetime,
        appointment_id=session_data.appointment_id,
    )
    
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    return new_session


@router.get("/clinical-records/{clinical_record_id}/sessions", response_model=list[SessionResponse])
async def list_sessions(
    clinical_record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permissions(Permission.VIEW_SESSIONS)),
):
    """
    Listar sesiones de una historia clínica.
    Requiere permiso: VIEW_SESSIONS
    """
    
    # Verificar que la historia clínica existe
    result = await db.execute(
        select(ClinicalRecord).where(ClinicalRecord.id == clinical_record_id)
    )
    clinical_record = result.scalar_one_or_none()
    
    if not clinical_record:
        raise HTTPException(
            status_code=404,
            detail=f"Historia clínica con ID {clinical_record_id} no encontrada"
        )
    
    # Obtener sesiones
    result = await db.execute(
        select(Session)
        .where(Session.clinical_record_id == clinical_record_id)
        .order_by(Session.session_datetime.desc())
    )
    sessions = result.unique().scalars().all()
    
    return sessions


@router.patch("/clinical-sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: int,
    session_data: SessionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permissions(Permission.EDIT_SESSIONS)),
):
    """
    Editar una sesión.
    Requiere permiso: EDIT_SESSIONS
    Roles: PSYCHOLOGIST, PSYCHIATRIST, ADMIN
    """
    
    # Buscar la sesión
    result = await db.execute(
        select(Session).where(Session.id == session_id)
    )
    session = result.unique().scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Sesión con ID {session_id} no encontrada"
        )
    
    # Verificar profesional si se cambia
    if session_data.professional_id and session_data.professional_id != session.professional_id:
        result = await db.execute(
            select(Employee).where(Employee.id == session_data.professional_id)
        )
        professional = result.unique().scalar_one_or_none()
        
        if not professional:
            raise HTTPException(
                status_code=404,
                detail=f"Profesional con ID {session_data.professional_id} no encontrado"
            )
        
        if professional.status != "ACTIVE":
            raise HTTPException(
                status_code=400,
                detail="No se puede asignar un profesional inactivo"
            )
    
    # Actualizar solo los campos proporcionados
    update_data = session_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(session, field, value)
    
    await db.commit()
    await db.refresh(session)
    
    return session
