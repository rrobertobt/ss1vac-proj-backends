from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db
from app.api.routes.specialties_schemas import (
    SpecialtyCreate,
    SpecialtyUpdate,
    SpecialtyResponse,
)
from app.db.repositories.specialties_repo import SpecialtiesRepository
from app.api.deps import require_permissions
from app.core.permissions import Permission

router = APIRouter(prefix="/specialties", tags=["specialties"])


@router.post("", response_model=SpecialtyResponse, status_code=201)
async def create_specialty(
    specialty: SpecialtyCreate,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_permissions(Permission.MANAGE_SPECIALTIES)),
):
    """Crear una nueva especialidad (requiere permiso MANAGE_SPECIALTIES)"""
    try:
        created_specialty = await SpecialtiesRepository.create(db, specialty)
        return created_specialty
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("", response_model=List[SpecialtyResponse])
async def get_specialties(db: AsyncSession = Depends(get_db)):
    """Obtener todas las especialidades (público)"""
    specialties = await SpecialtiesRepository.get_all(db)
    return specialties


@router.get("/{specialty_id}", response_model=SpecialtyResponse)
async def get_specialty(specialty_id: int, db: AsyncSession = Depends(get_db)):
    """Obtener una especialidad por ID (público)"""
    specialty = await SpecialtiesRepository.get_by_id(db, specialty_id)
    if not specialty:
        raise HTTPException(status_code=404, detail="Especialidad no encontrada")
    return specialty


@router.patch("/{specialty_id}", response_model=SpecialtyResponse)
async def update_specialty(
    specialty_id: int,
    specialty_data: SpecialtyUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_permissions(Permission.MANAGE_SPECIALTIES)),
):
    """Actualizar una especialidad (requiere permiso MANAGE_SPECIALTIES)"""
    try:
        updated_specialty = await SpecialtiesRepository.update(
            db, specialty_id, specialty_data
        )
        if not updated_specialty:
            raise HTTPException(status_code=404, detail="Especialidad no encontrada")
        return updated_specialty
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/{specialty_id}", status_code=200)
async def delete_specialty(
    specialty_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_permissions(Permission.MANAGE_SPECIALTIES)),
):
    """Eliminar una especialidad (requiere permiso MANAGE_SPECIALTIES)"""
    try:
        deleted = await SpecialtiesRepository.delete(db, specialty_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Especialidad no encontrada")
        return {"message": "Especialidad eliminada exitosamente"}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
