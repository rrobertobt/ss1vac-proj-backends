from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.db.models import Role, Permission, role_permissions


class RolesRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_all(self):
        result = await self.db.execute(
            select(Role).order_by(Role.name.asc())
        )
        return result.unique().scalars().all()

    async def find_by_id(self, role_id: int):
        result = await self.db.execute(
            select(Role).where(Role.id == role_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_role_permissions(self, role_id: int):
        result = await self.db.execute(
            select(Role).where(Role.id == role_id)
        )
        role = result.unique().scalar_one_or_none()
        return role

    async def update_role_permissions(self, role_id: int, permission_ids: list[int]):
        # Verificar que el rol existe
        role = await self.find_by_id(role_id)
        if not role:
            return None

        # Eliminar todas las relaciones existentes
        await self.db.execute(
            delete(role_permissions).where(role_permissions.c.role_id == role_id)
        )

        # Insertar las nuevas relaciones
        if permission_ids:
            values = [{"role_id": role_id, "permission_id": perm_id} for perm_id in permission_ids]
            await self.db.execute(role_permissions.insert(), values)

        await self.db.commit()

        # Retornar el rol actualizado con sus permisos
        return await self.get_role_permissions(role_id)
