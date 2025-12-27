from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db
from app.api.routes.areas_schemas import AreaCreate, AreaUpdate, AreaResponse
from app.db.repositories.areas_repo import AreasRepository
from app.api.deps import require_permissions
from app.core.permissions import Permission

router = APIRouter(prefix="/areas", tags=["areas"])


@router.post("", response_model=AreaResponse, status_code=201)
async def create_area(
    area: AreaCreate,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_permissions(Permission.MANAGE_AREAS)),
):
    """Crear una nueva área (requiere permiso MANAGE_AREAS)"""
    try:
        created_area = await AreasRepository.create(db, area)
        return created_area
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("", response_model=List[AreaResponse])
async def get_areas(db: AsyncSession = Depends(get_db)):
    """Obtener todas las áreas (público)"""
    areas = await AreasRepository.get_all(db)
    return areas


@router.get("/{area_id}", response_model=AreaResponse)
async def get_area(area_id: int, db: AsyncSession = Depends(get_db)):
    """Obtener un área por ID (público)"""
    area = await AreasRepository.get_by_id(db, area_id)
    if not area:
        raise HTTPException(status_code=404, detail="Área no encontrada")
    return area


@router.patch("/{area_id}", response_model=AreaResponse)
async def update_area(
    area_id: int,
    area_data: AreaUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_permissions(Permission.MANAGE_AREAS)),
):
    """Actualizar un área (requiere permiso MANAGE_AREAS)"""
    try:
        updated_area = await AreasRepository.update(db, area_id, area_data)
        if not updated_area:
            raise HTTPException(status_code=404, detail="Área no encontrada")
        return updated_area
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/{area_id}", status_code=200)
async def delete_area(
    area_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_permissions(Permission.MANAGE_AREAS)),
):
    """Eliminar un área (requiere permiso MANAGE_AREAS)"""
    deleted = await AreasRepository.delete(db, area_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Área no encontrada")
    return {"message": "Área eliminada exitosamente"}
