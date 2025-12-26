from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.db.repositories.roles_repo import RolesRepo
from app.api.routes.roles_schemas import RoleResponse

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", response_model=list[RoleResponse])
async def get_roles(db: AsyncSession = Depends(get_db)):
    """
    Endpoint público para obtener todos los roles disponibles.
    No requiere autenticación.
    """
    roles_repo = RolesRepo(db)
    roles = await roles_repo.find_all()
    return roles
