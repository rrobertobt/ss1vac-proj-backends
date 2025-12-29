from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, require_permissions
from app.core.permissions import Permission
from app.db.models import ConfidentialNote, ClinicalRecord
from app.api.routes.confidential_notes_schemas import (
    ConfidentialNoteCreate,
    ConfidentialNoteResponse,
)

router = APIRouter(prefix="/clinical-records", tags=["confidential-notes"])


@router.post("/{clinical_record_id}/confidential-notes", response_model=ConfidentialNoteResponse, status_code=201)
async def create_confidential_note(
    clinical_record_id: int,
    note_data: ConfidentialNoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permissions(Permission.CREATE_CONFIDENTIAL_NOTES)),
):
    """
    Crear una nota confidencial en una historia clínica.
    Requiere permiso: CREATE_CONFIDENTIAL_NOTES
    Roles: PSYCHOLOGIST, PSYCHIATRIST
    """
    
    # Verificar que la historia clínica existe
    result = await db.execute(
        select(ClinicalRecord).where(ClinicalRecord.id == clinical_record_id)
    )
    clinical_record = result.unique().scalar_one_or_none()
    
    if not clinical_record:
        raise HTTPException(
            status_code=404,
            detail=f"Historia clínica con ID {clinical_record_id} no encontrada"
        )
    
    # Verificar que la historia clínica esté activa
    if clinical_record.status != "ACTIVE":
        raise HTTPException(
            status_code=400,
            detail="No se puede agregar nota a una historia clínica cerrada"
        )
    
    # Obtener employee_id del usuario actual (si está disponible)
    author_employee_id = getattr(current_user, 'employee_id', None) if hasattr(current_user, 'employee_id') else None
    
    # Crear la nota confidencial
    new_note = ConfidentialNote(
        patient_id=clinical_record.patient_id,
        clinical_record_id=clinical_record_id,
        author_employee_id=author_employee_id,
        content=note_data.content,
    )
    
    db.add(new_note)
    await db.commit()
    await db.refresh(new_note)
    
    return new_note


@router.get("/{clinical_record_id}/confidential-notes", response_model=list[ConfidentialNoteResponse])
async def list_confidential_notes(
    clinical_record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permissions(Permission.VIEW_CONFIDENTIAL_NOTES)),
):
    """
    Listar notas confidenciales de una historia clínica.
    Requiere permiso: VIEW_CONFIDENTIAL_NOTES
    Roles: PSYCHOLOGIST, PSYCHIATRIST, ADMIN
    """
    
    # Verificar que la historia clínica existe
    result = await db.execute(
        select(ClinicalRecord).where(ClinicalRecord.id == clinical_record_id)
    )
    clinical_record = result.unique().scalar_one_or_none()
    
    if not clinical_record:
        raise HTTPException(
            status_code=404,
            detail=f"Historia clínica con ID {clinical_record_id} no encontrada"
        )
    
    # Obtener notas confidenciales
    result = await db.execute(
        select(ConfidentialNote)
        .where(ConfidentialNote.clinical_record_id == clinical_record_id)
        .order_by(ConfidentialNote.created_at.desc())
    )
    notes = result.unique().scalars().all()
    
    return notes
