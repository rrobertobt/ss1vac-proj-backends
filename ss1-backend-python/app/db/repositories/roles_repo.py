from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Role


class RolesRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_all(self):
        result = await self.db.execute(
            select(Role).order_by(Role.name.asc())
        )
        return result.unique().scalars().all()
