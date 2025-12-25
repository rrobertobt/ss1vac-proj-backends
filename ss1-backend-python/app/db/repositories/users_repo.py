from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, update
from app.db.models import User

class UsersRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_id(self, user_id: int) -> User | None:
        res = await self.db.execute(select(User).where(User.id == user_id))
        return res.unique().scalar_one_or_none()

    async def find_by_email_or_username(self, email_or_username: str) -> User | None:
        res = await self.db.execute(
            select(User).where(or_(User.email == email_or_username, User.username == email_or_username))
        )
        return res.unique().scalar_one_or_none()

    async def patch_user(self, user_id: int, patch: dict) -> User | None:
        await self.db.execute(update(User).where(User.id == user_id).values(**patch))
        await self.db.commit()
        return await self.find_by_id(user_id)
