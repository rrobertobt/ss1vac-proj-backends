from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import math

from app.api.deps import get_db, require_permissions
from app.core.permissions import Permission
from app.core.security import hash_password
from app.db.repositories.users_repo import UsersRepo
from app.api.routes.users_schemas import (
    UserCreate,
    UserUpdate,
    UserStatusUpdate,
    UserResponse,
    UserListResponse,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=UserListResponse)
async def get_users(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    role_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permissions(Permission.VIEW_USERS)),
):
    """
    Listar usuarios con paginación y filtros.
    Requiere permiso: VIEW_USERS
    """
    users_repo = UsersRepo(db)
    users, total = await users_repo.find_all(
        page=page,
        limit=limit,
        role_id=role_id,
        is_active=is_active,
        search=search,
    )

    return {
        "data": users,
        "meta": {
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": math.ceil(total / limit) if total > 0 else 0,
        },
    }


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permissions(Permission.VIEW_USERS)),
):
    """
    Ver detalle de un usuario.
    Requiere permiso: VIEW_USERS
    """
    users_repo = UsersRepo(db)
    user = await users_repo.find_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail=f"Usuario con ID {user_id} no encontrado")

    return user


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permissions(Permission.CREATE_USERS)),
):
    """
    Crear un nuevo usuario.
    Requiere permiso: CREATE_USERS
    """
    users_repo = UsersRepo(db)

    # Verificar si el email ya existe
    existing_user = await users_repo.find_by_email(user_data.email)
    if existing_user:
        raise HTTPException(status_code=409, detail="El email ya está registrado")

    # Verificar si el username ya existe (si se proporcionó)
    if user_data.username:
        existing_username = await users_repo.find_by_username(user_data.username)
        if existing_username:
            raise HTTPException(status_code=409, detail="El username ya está registrado")

    # Hashear la contraseña
    hashed_password = hash_password(user_data.password)

    # Crear usuario
    user_dict = user_data.model_dump(exclude={"password"})
    user_dict["password_hash"] = hashed_password

    user = await users_repo.create(user_dict)
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permissions(Permission.EDIT_USERS)),
):
    """
    Editar un usuario.
    Requiere permiso: EDIT_USERS
    """
    users_repo = UsersRepo(db)

    # Verificar que el usuario existe
    user = await users_repo.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"Usuario con ID {user_id} no encontrado")

    # Verificar si el nuevo email ya existe
    if user_data.email and user_data.email != user.email:
        existing_email = await users_repo.find_by_email(user_data.email)
        if existing_email:
            raise HTTPException(status_code=409, detail="El email ya está registrado")

    # Verificar si el nuevo username ya existe
    if user_data.username and user_data.username != user.username:
        existing_username = await users_repo.find_by_username(user_data.username)
        if existing_username:
            raise HTTPException(status_code=409, detail="El username ya está registrado")

    # Actualizar usuario
    update_dict = user_data.model_dump(exclude_unset=True)
    updated_user = await users_repo.patch_user(user_id, update_dict)

    return updated_user


@router.patch("/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: int,
    status_data: UserStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permissions(Permission.EDIT_USERS)),
):
    """
    Activar/desactivar un usuario.
    Requiere permiso: EDIT_USERS
    """
    users_repo = UsersRepo(db)

    # Verificar que el usuario existe
    user = await users_repo.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"Usuario con ID {user_id} no encontrado")

    # Actualizar estado
    updated_user = await users_repo.patch_user(user_id, {"is_active": status_data.is_active})

    return updated_user
