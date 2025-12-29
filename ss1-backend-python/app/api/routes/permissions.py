from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_permissions
from app.db.repositories.permissions_repo import PermissionsRepo
from app.api.routes.roles_schemas import PermissionResponse

router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.get("", response_model=list[PermissionResponse])
async def get_permissions(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permissions()),  # Solo requiere autenticación
):
    """
    Listar todos los permisos disponibles.
    Requiere autenticación pero no permisos específicos.
    """
    permissions_repo = PermissionsRepo(db)
    permissions = await permissions_repo.find_all()
    return permissions
