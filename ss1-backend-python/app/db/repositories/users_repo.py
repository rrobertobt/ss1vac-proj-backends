from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, update, func
from sqlalchemy.orm import joinedload
from app.db.models import User
from typing import Optional

class UsersRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_id(self, user_id: int) -> User | None:
        res = await self.db.execute(
            select(User)
            .where(User.id == user_id)
            .options(joinedload(User.role), joinedload(User.employee), joinedload(User.patient))
        )
        return res.unique().scalar_one_or_none()

    async def find_by_email_or_username(self, email_or_username: str) -> User | None:
        res = await self.db.execute(
            select(User)
            .where(or_(User.email == email_or_username, User.username == email_or_username))
            .options(joinedload(User.role), joinedload(User.employee), joinedload(User.patient))
        )
        return res.unique().scalar_one_or_none()

    async def find_by_email(self, email: str) -> User | None:
        res = await self.db.execute(
            select(User).where(User.email == email)
        )
        return res.scalar_one_or_none()

    async def find_by_username(self, username: str) -> User | None:
        res = await self.db.execute(
            select(User).where(User.username == username)
        )
        return res.scalar_one_or_none()

    async def find_all(
        self,
        page: int = 1,
        limit: int = 10,
        role_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ):
        offset = (page - 1) * limit

        # Construir query
        query = select(User).options(
            joinedload(User.role),
            joinedload(User.employee),
            joinedload(User.patient)
        )

        # Aplicar filtros
        if role_id is not None:
            query = query.where(User.role_id == role_id)

        if is_active is not None:
            query = query.where(User.is_active == is_active)

        if search:
            query = query.where(
                or_(
                    User.email.ilike(f"%{search}%"),
                    User.username.ilike(f"%{search}%")
                )
            )

        # Obtener total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Aplicar paginación y ordenamiento
        query = query.order_by(User.created_at.desc()).limit(limit).offset(offset)

        # Ejecutar query
        result = await self.db.execute(query)
        users = result.unique().scalars().all()

        return user

    async def update(self, user_id: int, user_data: dict):
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return None

        for key, value in user_data.items():
            setattr(user, key, value)

        await self.db.commit()
        await self.db.refresh(user)
        return users, total

    async def create(self, user_data: dict) -> User:
        user = User(**user_data)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return await self.find_by_id(user.id)

    async def patch_user(self, user_id: int, patch: dict) -> User | None:
        await self.db.execute(update(User).where(User.id == user_id).values(**patch))
        await self.db.commit()
        return await self.find_by_id(user_id)
