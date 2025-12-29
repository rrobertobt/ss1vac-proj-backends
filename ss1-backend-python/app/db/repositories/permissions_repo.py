from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Permission


class PermissionsRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_all(self):
        result = await self.db.execute(
            select(Permission).order_by(Permission.code.asc())
        )
        return result.scalars().all()

    async def find_by_ids(self, permission_ids: list[int]):
        result = await self.db.execute(
            select(Permission).where(Permission.id.in_(permission_ids))
        )
        return result.scalars().all()
