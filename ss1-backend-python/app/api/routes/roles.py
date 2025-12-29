from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_permissions
from app.core.permissions import Permission
from app.db.repositories.roles_repo import RolesRepo
from app.db.repositories.permissions_repo import PermissionsRepo
from app.api.routes.roles_schemas import (
    RoleResponse,
    RolePermissionsResponse,
    UpdateRolePermissionsRequest,
)

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", response_model=list[RoleResponse])
async def get_roles(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permissions()),  # Solo requiere autenticación
):
    """
    Listar todos los roles disponibles.
    Requiere autenticación pero no permisos específicos.
    """
    roles_repo = RolesRepo(db)
    roles = await roles_repo.find_all()
    return roles


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permissions()),  # Solo requiere autenticación
):
    """
    Obtener detalles de un rol por ID.
    Requiere autenticación pero no permisos específicos.
    """
    roles_repo = RolesRepo(db)
    role = await roles_repo.find_by_id(role_id)
    
    if not role:
        raise HTTPException(status_code=404, detail=f"Rol con ID {role_id} no encontrado")
    
    return role


@router.get("/{role_id}/permissions", response_model=RolePermissionsResponse)
async def get_role_permissions(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permissions(Permission.ASSIGN_ROLE_PERMISSIONS)),
):
    """
    Obtener permisos de un rol específico.
    Requiere permiso: ASSIGN_ROLE_PERMISSIONS
    """
    roles_repo = RolesRepo(db)
    role = await roles_repo.get_role_permissions(role_id)
    
    if not role:
        raise HTTPException(status_code=404, detail=f"Rol con ID {role_id} no encontrado")
    
    return {
        "role": {
            "id": role.id,
            "name": role.name,
            "label": role.label,
            "description": role.description,
        },
        "permissions": role.permissions or [],
    }


@router.put("/{role_id}/permissions", response_model=RolePermissionsResponse)
async def update_role_permissions(
    role_id: int,
    request: UpdateRolePermissionsRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permissions(Permission.ASSIGN_ROLE_PERMISSIONS)),
):
    """
    Actualizar permisos de un rol.
    Requiere permiso: ASSIGN_ROLE_PERMISSIONS
    """
    roles_repo = RolesRepo(db)
    permissions_repo = PermissionsRepo(db)
    
    # Verificar que el rol existe
    role = await roles_repo.find_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail=f"Rol con ID {role_id} no encontrado")
    
    # Verificar que todos los permisos existen
    if request.permission_ids:
        permissions = await permissions_repo.find_by_ids(request.permission_ids)
        if len(permissions) != len(request.permission_ids):
            raise HTTPException(
                status_code=400,
                detail="Uno o más IDs de permisos no son válidos"
            )
    
    # Actualizar permisos
    try:
        updated_role = await roles_repo.update_role_permissions(role_id, request.permission_ids)
        
        if not updated_role:
            raise HTTPException(
                status_code=500,
                detail="Error al actualizar permisos del rol"
            )
        
        return {
            "role": {
                "id": updated_role.id,
                "name": updated_role.name,
                "label": updated_role.label,
                "description": updated_role.description,
            },
            "permissions": updated_role.permissions or [],
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar permisos: {str(e)}"
        )

