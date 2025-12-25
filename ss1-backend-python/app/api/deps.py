from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Callable

from app.core.config import settings
from app.core.security import decode_token
from app.core.permissions import Permission
from app.db.session import get_db
from app.db.repositories.users_repo import UsersRepo

bearer = HTTPBearer(auto_error=False)

async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
):
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="No autenticado")

    payload = decode_token(creds.credentials, settings.JWT_ACCESS_SECRET)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Token inválido")

    users = UsersRepo(db)
    # sub puede ser int o string, asegurar que sea int
    user_id = payload["sub"] if isinstance(payload["sub"], int) else int(payload["sub"])
    user = await users.find_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Token inválido")

    # Agregar lista de permisos como atributo
    user.permissions = [p.code for p in user.role.permissions] if user.role and user.role.permissions else []

    return user


def require_permissions(*required_permissions: Permission) -> Callable:
    """
    Dependencia para verificar que el usuario tenga los permisos requeridos.
    Uso:
        @router.get("/patients")
        async def get_patients(user = Depends(require_permissions(Permission.VIEW_PATIENTS))):
            ...
    """
    async def permission_checker(user = Depends(get_current_user)):
        # SUPER_ADMIN tiene acceso a todo
        if user.role and user.role.name == 'SUPER_ADMIN':
            return user
        
        user_permissions = getattr(user, 'permissions', [])
        
        for perm in required_permissions:
            if perm.value not in user_permissions:
                raise HTTPException(
                    status_code=403,
                    detail="No tienes permisos suficientes para realizar esta acción."
                )
        
        return user
    
    return permission_checker

